from fileinput import filename
from aiohttp import web
from aiohttp.web import Request, Response, json_response
import asyncio
import base64
from pydantic import FilePath
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes, ConversationReference
from botframework.connector.auth import AppCredentials
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
)
from bots.bot import MalushkaBot
from bots.quaries import Query
from datetime import datetime
import sys
import traceback
import logging
import uuid
from typing import Dict
from http import HTTPStatus
from vault import vault_config
import os
from bots.activity_utils import create_attachment
from bots.send_file import give_mailing_access
from botbuilder.core import MessageFactory, TurnContext


logger = logging.getLogger('gunicorn.error')
query = Query()
SETTINGS = BotFrameworkAdapterSettings(vault_config.APP_ID, vault_config.APP_SECRET)
ADAPTER = BotFrameworkAdapter(SETTINGS)


@web.middleware
async def on_error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except Exception as e:
        logger.error(traceback.format_exc())


async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    logger.error(traceback.format_exc())
    query.insert_error(traceback.format_exc())
    return


ADAPTER.on_turn_error = on_error


CONVERSATION_REFERENCES: Dict[str, ConversationReference] = query.load_conversation_references()
APP_ID = SETTINGS.app_id if SETTINGS.app_id else uuid.uuid4()


BOT = MalushkaBot(CONVERSATION_REFERENCES)


async def messages(req: Request) -> Response:
    print(req.headers)
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
        print(body)
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)


async def notify(req: Request) -> Response:
    print(req.json())
    if "application/json" in req.headers["Content-Type"]:
        if req.headers["Authentication"] == 'token':
            req_body = await req.json()
            print(req_body)
            if req_body['type'] == 'mailing':
                users = req_body['users']
                message = req_body['message']
                meta = req_body['file_info']
                await _send_mailing(users, message, meta)
            elif req_body['type'] == 'notification':
                users = req_body['users']
                message = req_body['message']
                await _send_message(users, message)
    return Response(status=HTTPStatus.OK, text="Proactive messages have been sent")


async def _send_mailing(users, message, meta):
    give_mailing_access(meta['_fileName'], users)
    mailing = MessageFactory.text(message) 
    mailing.attachments = [create_attachment(meta)]
    for user in users:
        if user in CONVERSATION_REFERENCES.keys():
            AppCredentials.trust_service_url(CONVERSATION_REFERENCES[user].service_url)
            await ADAPTER.continue_conversation(
                CONVERSATION_REFERENCES[user],
                lambda turn_context: turn_context.send_activity(mailing),
                APP_ID,
            )
    return


async def _send_message(users, message):
    for user in users:
        if user in CONVERSATION_REFERENCES.keys():
            AppCredentials.trust_service_url(CONVERSATION_REFERENCES[user].service_url)
            await ADAPTER.continue_conversation(
                CONVERSATION_REFERENCES[user],
                lambda turn_context: turn_context.send_activity(MessageFactory.text(message)),
                APP_ID,
            )
    return


async def index(req: Request) -> Response:
    return Response(status=HTTPStatus.OK)


async def get_web_app():
    APP = web.Application(middlewares=[aiohttp_error_middleware])
    APP.router.add_post("/api/messages", messages)
    APP.router.add_post("/api/notify", notify)
    APP.router.add_post("/", index)
    return APP


if __name__ == "__main__":
    try:
        APP = get_web_app()
        web.run_app(APP, host="localhost", port=3978)
    except Exception as error:
        raise error