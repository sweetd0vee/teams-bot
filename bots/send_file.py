import requests
import os
import re
from urllib.parse import quote
from vault import vault_config


def get_token():
    app_tenant = vault_config.APP_TENANT
    token_url = f"https://login.microsoftonline.com/{app_tenant}/oauth2/token"
    token_data = {
        'grant_type': 'password',
        'client_id': vault_config.APP_ID,
        'client_secret': vault_config.APP_SECRET,
        'resource': 'https://graph.microsoft.com',
        'scope': 'Files.ReadWrite.All',
        'username': vault_config.SRV_USERNAME,
        'password': vault_config.SRV_PASSWORD
    }

    token_r = requests.post(token_url, data=token_data)
    token = token_r.json().get('access_token')
    return token


def get_bot_id(token):
    url = "https://graph.microsoft.com/v1.0/me"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-type": "application/json"
    }

    r = requests.get(url, headers=headers)
    return r.json().get("id")


def get_drive_id(token):
    res = requests.get(
        url="https://graph.microsoft.com/v1.0/me/drive",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json"
        }
    )
    return res.json()['id']


def upload_to_drive(path, bearer_token, sharepoint_drive_id, sharepoint_path, mode='file'):
    """
    Отправка сообщения с прикрепленным изображением/файлом
    (!) ВНИМАНИЕ: Для отправки сообщения бот должен находиться в команде

    ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ
        path - string - путь к файлу для загрузки
        bearer_token - string - авторизационный токен
        team_id - string - ID команды MS Teams
        channel_id - string - ID канала MS Teams
        sharepoint_drive_id - string - ID хранилища sharepoint, куда будет сохранен файл
        sharepoint_path - string - путь для файла в хранилище Sharepoint

    ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ
        message - string - текст сообщения - по умолчанию ''
        mode - string - 'file', 'large file' (для файлов более 4 Mb) или 'image' - по умолчанию 'file'
        proxy - dict - словарь с прокси для requests - по умолчанию default из ozon_bots

    ВОЗВРАЩАЕТ
        status_code - int - статус запроса на отправку сообщения
    """

    _etag = ""
    _fileUrl = ""
    _fileName = ""
    _fileThumbnail = ""

    if mode == "file":
        _data = open(path, 'rb').read()
        _response = requests.put(
            url=f"https://graph.microsoft.com/v1.0/drives/{sharepoint_drive_id}/items/root:/{sharepoint_path}:/content",
            headers={
                "Content-Type": "application/binary",
                "Authorization": f"Bearer {bearer_token}",
            },
            data=_data
        )

        _response_path = requests.get(
            url=f"https://graph.microsoft.com/v1.0/drives/{_response.json()['parentReference']['driveId']}",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )
        print(_response_path.json())
        meta = dict()
        meta['_etag'] = re.sub(".+\{|\}.+$", "", _response.json()['eTag'])
        meta['_fileUrl'] = _response_path.json()['webUrl'] + "/" + quote(sharepoint_path)

        meta['_fileName'] = _response.json()['name']
        return meta
    elif mode == "large file":

        # инициализация сессии
        _response = requests.post(
            url=f"https://graph.microsoft.com/v1.0/drives/{sharepoint_drive_id}/items/root:/{sharepoint_path}:/createUploadSession",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )

        # загрузка файла чанками в сессию
        with open(path, 'rb') as f:
            total_file_size = os.path.getsize(path)
            chunk_size = 327680
            chunk_number = total_file_size // chunk_size
            chunk_leftover = total_file_size - chunk_size * chunk_number

            i = 0
            while True:
                chunk_data = f.read(chunk_size)
                start_index = i * chunk_size
                end_index = start_index + chunk_size
                if not chunk_data:
                    break
                if i == chunk_number:
                    end_index = start_index + chunk_leftover

                _upload_response = requests.put(
                    url=_response.json()['uploadUrl'],
                    headers={
                        'Content-Length': '{}'.format(chunk_size),
                        'Content-Range': 'bytes {}-{}/{}'.format(start_index, end_index - 1, total_file_size)
                    },
                    data=chunk_data
                )
                i += 1

        _response_path = requests.get(
            url=f"https://graph.microsoft.com/v1.0/drives/{_upload_response.json()['parentReference']['driveId']}",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )

        meta = dict()
        meta['_etag'] = re.sub(".+\{|\}.+$", "", _upload_response.json()['eTag'])
        meta['_fileUrl'] = _response_path.json()['webUrl'] + "/" + quote(sharepoint_path)
        meta['_fileName'] = _upload_response.json()['name']
        return meta

    elif mode == "image":
        _data = open(path, 'rb').read()

        _response = requests.put(
            url=f"https://graph.microsoft.com/v1.0/drives/{sharepoint_drive_id}/items/root:/{sharepoint_path}:/content?$expand=thumbnails",
            headers={
                "Content-Type": "application/binary",
                "Authorization": f"Bearer {bearer_token}",
            },
            data=_data
        )
        _response_path = requests.get(
            url=f"https://graph.microsoft.com/v1.0/drives/{_response.json()['parentReference']['driveId']}",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )

        meta = dict()
        meta['_etag'] = re.sub(".+\{|\}.+$", "", _response.json()['eTag'])
        meta['_fileUrl'] = _response_path.json()['webUrl'] + "/" + quote(sharepoint_path)
        meta['_fileName'] = _response.json()['name']
        meta['_fileThumbnail'] = _response.json()['thumbnails'][0]['large']['url']
        return meta


def give_access(token, item_id, users):
    """
    Предоставление доступа к файлу, загруженному в облако бота
    """

    recipients = []
    for user in users:
        recipients.append({'email': user})

    data = {
                "recipients": recipients,
                "message": "Here's the file that we're collaborating on.",
                "requireSignIn": True,
                "sendInvitation": False,
                "roles": ["read"]
            }
    headers = {"Authorization": f"Bearer {token}",
               "Content-type": "application/json"}

    events = requests.post(
        url=f'https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/invite',
        json=data, headers=headers)
    return events


def get_item_id(token, path):
    res = requests.get(
        url=f"https://graph.microsoft.com/v1.0/me/drive/items/root:/{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json"
        }
    )
    return res.json()['id']


def send_rss(filepath_local, filepath_drive, users):
    token = get_token()
    drive_id = get_drive_id(token)
    filesize = os.path.getsize(filepath_local)
    meta = upload_to_drive(
        filepath_local, token,
        drive_id,
        filepath_drive, mode='large file'
    )
    meta['filesize'] = filesize
    meta['type'] = 'file'
    meta['filetype'] = filepath_local.split('.')[-1]

    item_id = get_item_id(token, meta['_fileName'])
    give_access(token, item_id, users)
    return meta


def give_mailing_access(path_in_drive, users):
    token = get_token()
    item_id = get_item_id(token, path_in_drive)
    give_access(token, item_id, users)
    print('users have access')
    return
