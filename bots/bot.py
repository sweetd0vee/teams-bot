from botbuilder.core import ActivityHandler, MessageFactory, TurnContext, CardFactory
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from botbuilder.schema.teams.additional_properties import ContentType
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    ConversationReference,
)
from typing import Dict
from .activity_utils import create_adaptive_card_attachment
from .auth import Auth
from .commands import *
import json
import os
from .quaries import Query


CMD_DICT = {
        'count_mal' : cmd_count_mal,
        'malushka_all' : cmd_malushka_all,
        'malushka_csv' : cmd_malushka_csv,
        'malushka_upload_file': cmd_malushka_upload_file,
        'get_table_owner' : cmd_get_table_owner,
        'get_useless_tables' : cmd_get_useless_tables,
        'cost_fbs'  : cmd_cost_fbs,
        'tariffs_matrix' : cmd_tariffs_matrix,
        'tariffs_matrix_checks' : cmd_tariffs_matrix_checks,
        'logist_checks' : cmd_logist_checks,
        'commerce_checks' : cmd_commerce_checks
    }


class MalushkaBot(TeamsActivityHandler):
    """
    This bot will respond to the user's input with suggested actions, that implement the range of
    malushka functions, metric checkers and support.
    Suggested actions enable your bot to present buttons that the user can tap to provide input.
    """
    def __init__(self, conversation_references: Dict[str, ConversationReference]):
        self.conversation_references = conversation_references
        self.query = Query()
        self.global_ids = {user.user.id for user in self.conversation_references.values()}
        self.error_msg = MessageFactory.text('К сожалению, у Вас недостаточно прав на использование данного приложения')
        self.auth = Auth()


    async def on_members_added_activity(self, members_added, turn_context):
        """
        Send a welcome message to the user and tell them what actions they may perform to use this bot
        """
        for member in members_added:
            activity = turn_context.activity
            member_info = await TeamsInfo.get_member(turn_context, turn_context.activity.from_property.id)
            user_login = member_info.user_principal_name[:-8]

            if not self.query.is_valid_user(user_login):
                return await turn_context.send_activity(self.error_msg)
            # auth 
            # user_role = self.auth.get_user_role(user_login)
            # user_role = 'user'
            # if not self.auth.check_permission(user_role):
            #     return await turn_context(self.error_msg)

            if (member.id != activity.recipient.id):
                if member.id not in self.global_ids:
                    self._add_conversation_reference(activity, user_login)
                await self._send_suggested_actions(turn_context)
        return


    async def on_conversation_update_activity(self, turn_context: TurnContext):
        member_info = await TeamsInfo.get_member(turn_context, turn_context.activity.from_property.id)
        user_login = member_info.user_principal_name[:-8]
        if not self.query.is_valid_user(user_login):
            return await turn_context.send_activity(self.error_msg)
        self._add_conversation_reference(turn_context.activity, user_login)
        return await super().on_conversation_update_activity(turn_context)
  

    def _add_conversation_reference(self, activity: Activity, user_login):
        """
            Updates the dictionary with the last ConversationReference for provided user.
        """
        conversation_reference = TurnContext.get_conversation_reference(activity)
        serialized_data = conversation_reference.as_dict()
        serialized_data = json.dumps(serialized_data)
        is_old = self.query.check_user(user_login)
        if not is_old:
            self.query.insert_conversation(user_login, serialized_data)
            self.conversation_references[user_login] = conversation_reference
            self.global_ids.add(conversation_reference.user.id)
        self.conversation_references[user_login] = conversation_reference
        return


    async def on_message_activity(self, turn_context: TurnContext):
        activity = turn_context.activity
        member_info = await TeamsInfo.get_member(turn_context, turn_context.activity.from_property.id)
        user_login = member_info.user_principal_name[:-8]
        
        if not self.query.is_valid_user(user_login):
            return await turn_context.send_activity(self.error_msg)

        # auth
        # user_role = self.auth.get_user_role(user_login)
        # user_role = 'user'
        # if not self.auth.check_permission(user_role):
        #     return await turn_context(self.error_msg)

        if user_login not in self.conversation_references.keys():
            self._add_conversation_reference(activity, user_login)
            return await self._send_suggested_actions(turn_context)

        self._add_conversation_reference(activity, user_login)
        if activity.value:
            if 'command_id' in activity.value:
                cmd = activity.value['command_id']
                input_flag = activity.value['input']
                if not input_flag and cmd in CMD_DICT.keys():
                        message = Activity(
                            type=ActivityTypes.message,
                            attachments=[create_adaptive_card_attachment(os.path.join(os.getcwd(), f"resources/{cmd}.json"))]
                        )
                        await turn_context.send_activity(message)
                else:
                    activity_data = activity.value
                    activity_data = json.dumps(activity_data)
                    self.query.insert_logs(user_login, activity_data)
                    await CMD_DICT[cmd](turn_context, user_login)
        text = activity.text
        if text:
            if "start" in text.lower():
                await self._send_suggested_actions(turn_context)

        attachments = activity.attachments
        if attachments:
            await cmd_malushka_upload_file(turn_context, user_login)
        return


    async def _send_suggested_actions(self, turn_context: TurnContext):
        """
        Creates and sends an activity with suggested actions to the user. When the user
        clicks one of the buttons the text value from the "CardAction" will be displayed
        in the channel just as if the user entered the text.
        """
        message = Activity(
            type=ActivityTypes.message,
            attachments=[create_adaptive_card_attachment("resources/welcome.json")],
        )
        return await turn_context.send_activity(message)