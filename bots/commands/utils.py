from datetime import datetime
import os
import pandas as pd
import sys
from vault.vault_config import *


CH_CREDS_CLOUD_1 = {
    'host': CH_HOST_CLOUD_1,
    'user': CH_HOST_CLOUD_USER,
    'password': CH_HOST_CLOUD_PASSWORD,
    'database': CH_HOST_CLOUD_DATABASE,
}


CH_CREDS_CLOUD_2 = {
    'host': CH_HOST_CLOUD_2,
    'user': CH_HOST_CLOUD_USER,
    'password': CH_HOST_CLOUD_PASSWORD,
    'database': CH_HOST_CLOUD_DATABASE,
}


CH_CREDS_IRON_1 = {
    'host': CH_HOST_IRON_1,
    'user': CH_HOST_IRON_USER,
    'password': CH_HOST_IRON_PASSWORD,
    'database': CH_HOST_IRON_DATABASE,
    'settings': {
        'connect_timeout_with_failover_ms': 1000
    }
}


CH_CREDS_IRON_2 = {
    'host': CH_HOST_IRON_2,
    'user': CH_HOST_IRON_USER,
    'password': CH_HOST_IRON_PASSWORD,
    'database': CH_HOST_IRON_DATABASE,
}


CH_CREDS_IRON_3 = {
    'host': CH_HOST_IRON_3,
    'user': CH_HOST_IRON_USER,
    'password': CH_HOST_IRON_PASSWORD,
    'database': CH_HOST_IRON_DATABASE,
    'settings': {
        'connect_timeout_with_failover_ms': 1000
    }
}


CH_CREDS_IRON_4 = {
    'host': CH_HOST_IRON_4,
    'user': CH_HOST_IRON_USER,
    'password': CH_HOST_IRON_PASSWORD,
    'database': CH_HOST_IRON_DATABASE,
}


CH_CREDS_IRON_5 = {
    'host': CH_HOST_IRON_5,
    'user': CH_HOST_IRON_USER,
    'password': CH_HOST_IRON_PASSWORD,
    'database': CH_HOST_IRON_DATABASE,
}


CH_CREDS_IRON_6 = {
    'host': CH_HOST_IRON_6,
    'user': CH_HOST_IRON_USER,
    'password': CH_HOST_IRON_PASSWORD,
    'database': CH_HOST_IRON_DATABASE,
    'settings': {
        'connect_timeout_with_failover_ms': 1000
    }
}

dicts = {
    "MacroBU": "dictGet('table_name', 'MacroBU',tuple(assumeNotNull(`MacroBU`))) as `MacroBU`",
    "Category 1": "dictGet('db_name.table_name', 'Category 1', tuple(assumeNotNull(`Category 1`))) as `Category 1`",
    "Category 2": "dictGet('db_name.table_name', 'Category 2',tuple(assumeNotNull(`Category 2`))) as `Category 2`",
    "Category 3": "dictGet('db_name.table_name', 'Category 3',tuple(assumeNotNull(`Category 3`))) as `Category 3`",
    "Category 4": "dictGet('db_name.table_name', 'Category 4',tuple(assumeNotNull(`Category 4`))) as `Category 4`",
    "Cluster To": "dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Cluster To`))) as `Cluster To`",
    "Warehouse": "dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Warehouse`))) as Warehouse",
    "Cluster From": "dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Cluster From`))) as `Cluster From`",
    "Cluster From old": "dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Cluster From old`))) as `Cluster From old`",
    "Sales Schema": "dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Sales Schema`))) as `Sales Schema`",
    "LM Channel": "dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`LM Channel`))) as `LM Channel`",
    "Version": "dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Version`))) as `Version `"
}


def get_filepath(filename: str, timestemp: datetime, is_mailing = 0) -> str:
    file_name = filename.split('.')[0]
    file_extension = filename.split('.')[-1]
    if not is_mailing:
        date = timestemp.strftime("%Y%m%d")
        time = timestemp.strftime("%H%M%S")
        path = f"resources/files/{file_name}_{date}_{time}.{file_extension}"
    filepath = os.path.join(os.getcwd(), path)
    return filepath


def validate_input_months(data):
    if "months" not in data:
        message = "Вы не заполнили, какие месяца хотите выгрузить, попробуйте еще раз"
        return [], message
    input = [i.strip() for i in str(data['months']).split(",")]
    months = []
    for i in input:
        try:
            d = datetime.strptime(i, "%Y%m")
        except:
            return [], f"Некорректный формат ввода: {data['months']}, попробуйте еще раз"
        m = datetime.strftime(d, format="%Y%m")
        months.append(m)
    if not len(months):
        return [], f"Некорректный формат ввода {data['months']}, попробуйте еще раз"
    return months, ""


def validate_input_versions(data):
    if "versions" not in data:
        message = "Вы не заполнили версии, которые хотите проверить, попробуйте еще раз"
        return [], message
    versions = [i.strip() for i in str(data['versions']).split(",")]
    return versions, ""


def validate_input_supermarket(data):
    if "supermarket" not in data:
        message = "Вы не заполнили значение 'supermarket', попробуйте еще раз"
        return [], message
    supermarket = data['supermarket']
    return supermarket, ""