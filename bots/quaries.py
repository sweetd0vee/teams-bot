from botbuilder.schema import ConversationReference
from clickhouse_driver.client import Client
from clickhouse_driver import errors
from .commands.utils import CH_CREDS_IRON_3
from datetime import datetime
import json
from pytz import timezone
from typing import Dict


class Query:
    def __init__(self):
        self.client = Client(**CH_CREDS_IRON_3)


    def select_conversation_logins(self, login):
        try:
            result = self.client.execute(
                "SELECT reference FROM db_name.table_name where login = %(myvar)s",
                {'myvar': login}
            )
        except errors.ServerException as e:
            result = ""
        return result


    def insert_conversation(self, login, reference):
        try:
            result = self.client.execute(
                """INSERT INTO db_name.table_name (login, reference) VALUES""",
                [{'login': login, 'reference': reference}])
        except errors.ServerException as e:
            result = ''
        return result


    def load_conversation_references(self):
        sql_query = """select * from db_name.table_name"""
        try:
            conversations = self.client.execute(sql_query)
        except errors.ServerException as e:
            conversations = []
        conversation_references: Dict[str, ConversationReference] = dict()
        for conversation in conversations:
            conversation_references[conversation[0]] = ConversationReference.from_dict(json.loads(conversation[1]))
        return conversation_references
    

    def check_user(self, login):
        try:
            result = self.client.execute(
            "SELECT count(*) from db_name.table_name where login = %(myvar)s",
            {'myvar': login})[0][0]
        except errors.ServerException as e:
            result = ''
        return result
    

    def is_valid_user(self, login):
        try:
            result = self.client.execute(
                "SELECT count(*) FROM db_name.table_name WHERE Login = %(myvar)s",
                {'myvar': login})[0][0]
        except errors.SeerverException as e:
            result = ''
        return result


    def insert_error(self, traceback):
        try:
            result = self.client.execute(
                """INSERT INTO db_name.table_name (Traceback, TimeLoad) VALUES""",
                [{'Traceback': traceback, 'TimeLoad': datetime.now(timezone('Europe/Moscow'))}]
            )
        except errors.ServerException as e:
            result = ''
        return result


    def insert_logs(self, login, reference):
        try:
            result = self.client.execute(
                """INSERT INTO db_name.table_name (Login, Activity, TimeLoad) VALUES""",
                [{'Login': login, 'Activity': reference, 'TimeLoad': datetime.now(timezone('Europe/Moscow'))}])
        except errors.ServerException as e:
            result = ''
        return result