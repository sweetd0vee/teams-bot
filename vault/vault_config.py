import os
import hvac

JWT_TOKEN_PATH = '' # path in vault

if os.path.exists(JWT_TOKEN_PATH):
    JWT_TOKEN = open(JWT_TOKEN_PATH).read()
    ENV = os.getenv("ENVIRONMENT")
    ROLE = os.getenv("VAULT_ROLE")
    AUTH_URL = os.getenv("VAULT_AUTH_URL")
    VAULT_MOUNT = os.getenv("VAULT_MOUNT")
    client = hvac.Client()
    client.auth.kubernetes.login(role=ROLE, jwt=JWT_TOKEN, mount_point=AUTH_URL)
    data = client.read('')# path in vault
    CH_HOST_CLOUD_1 = data['data']['CH_HOST_CLOUD_1']
    CH_HOST_CLOUD_2 = data['data']['CH_HOST_CLOUD_2']
    CH_HOST_IRON_1 = data['data']['CH_HOST_IRON_1']
    CH_HOST_IRON_2 = data['data']['CH_HOST_IRON_2']
    CH_HOST_IRON_3 = data['data']['CH_HOST_IRON_3']
    CH_HOST_IRON_4 = data['data']['CH_HOST_IRON_4']
    CH_HOST_IRON_5 = data['data']['CH_HOST_IRON_5']
    CH_HOST_IRON_6 = data['data']['CH_HOST_IRON_6']
    CH_HOST_IRON_USER = data['data']['CH_HOST_IRON_USER']
    CH_HOST_CLOUD_USER = data['data']['CH_HOST_CLOUD_USER']
    CH_HOST_IRON_PASSWORD = data['data']['CH_HOST_IRON_PASSWORD']
    CH_HOST_CLOUD_PASSWORD = data['data']['CH_HOST_CLOUD_PASSWORD']
    CH_HOST_IRON_DATABASE = data['data']['CH_HOST_IRON_DATABASE']
    CH_HOST_CLOUD_DATABASE =data['data']['CH_HOST_CLOUD_DATABASE']

    MAILING_USER = data['data']['MAILING_USER']
    MAILING_PASSWORD = data['data']['MAILING_PASSWORD']

    SRV_USERNAME = data['data']['SRV_USERNAME']
    SRV_PASSWORD = data['data']['SRV_PASSWORD']

    APP_ID = data['data']['APP_ID']
    APP_SECRET = data['data']['APP_SECRET']
    APP_TENANT = data['data']['APP_TENANT']
else:
    CH_HOST_CLOUD_1 = ""
    CH_HOST_CLOUD_2 = ""
    CH_HOST_IRON_1 = ""
    CH_HOST_IRON_2 = ""
    CH_HOST_IRON_3 = ""
    CH_HOST_IRON_4 = ""
    CH_HOST_IRON_5 = ""
    CH_HOST_IRON_6 = ""
    CH_HOST_IRON_USER = ""
    CH_HOST_CLOUD_USER = ""
    CH_HOST_IRON_PASSWORD = ""
    CH_HOST_CLOUD_PASSWORD = ""
    CH_HOST_IRON_DATABASE = ""
    CH_HOST_CLOUD_DATABASE = ""

    MAILING_USER = ""
    MAILING_PASSWORD = ""

    SRV_USERNAME = ""
    SRV_PASSWORD = ""

    APP_ID = ""
    APP_SECRET = ""
    APP_TENANT = ""