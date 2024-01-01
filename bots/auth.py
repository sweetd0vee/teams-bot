from botbuilder.core import TurnContext
from botbuilder.core.teams import TeamsInfo
from clickhouse_driver.client import Client
from bots.commands.utils import CH_CREDS_IRON_3
from environment.python_auth import make_token_verifier, verify_headers
import requests

roles = ("user", "administrator")
token_url = ""

class BaseAuth():
    def has_permission(self):
        verificator = make_token_verifier(
                        issuer='',
                        client_id=''
                        )
        headers = {
            'content-type' : "application/json"
        }
        data = {
            "client_id" : "",
            "client_secret" : "",
            "grant_type": "client_credentials"
        }
        token = requests.post(url='',
                            params=data,
                            headers=headers)
        return verificator


class Auth():
    def __init__(self):
        pass

    def get_user_role(self, user_login):
        pass

    @staticmethod
    def check_permission(user_role, params=None):
        if user_role == "administrator":
            return True
        elif user_role == "user":
            return True
        return False
