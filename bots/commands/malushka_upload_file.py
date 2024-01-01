from botbuilder.core import MessageFactory, TurnContext
from .utils import *
from datetime import datetime
from clickhouse_driver.client import Client
import pandas as pd
import requests
import io
import csv


async def cmd_malushka_upload_file(turn_context: TurnContext, user_login: str):
    attachments = turn_context.activity.attachments
    if not attachments:
        return await turn_context.send_activity(MessageFactory.text('Вы не отправили файл с малышками, выполните функцию еще раз'))

    file_info = attachments[0].content
    file_type = file_info['fileType']
    if file_type != 'csv':
        return await turn_context.send_activity(MessageFactory.text('Необходимо было прикрепить файл с расширением .csv, выполните функцию еще раз'))
    downloadUrl = file_info['downloadUrl']
    try:
        r = requests.get(downloadUrl, allow_redirects=True)
        open('resources/files/upload_malushka.csv', 'wb').write(r.content)
        with open('resources/files/upload_malushka.csv') as f:
            rows = [line for line in csv.reader(f, delimiter=';')]
        df = pd.DataFrame(rows[1:])
        df.columns = rows[0]
        if list(df.columns) != ['Month', 'Category 1', 'Category 2', 'Category 3', 'Category 4', 'mal', 'Category 4 ID']:
            return await turn_context.send_activity(MessageFactory.text("Некорректный файл, так как отсутствуют необходимые поля"))
        sql_part = []
        now = datetime.now()
        for index, row in df.iterrows():
            client = Client(**CH_CREDS_IRON_3)
            ids = client.execute(f"""select `Category 4 ID` from db_name.table_name
                            where `Category 4` = '{row['Category 4']}'""")
            ids = tuple([i[0] for i in ids])
            if len(ids) == 1:
                sql_part.append(
                    f"""(dictGet('db_name.table_name', 'Category 4 ID',tuple(assumeNotNull('{row['Category 4']}'))), {str(row['mal']).replace(',', '.')}, {row['Month']}, '{user}', now())""")
            elif len(ids) > 1:
                id = client.execute(f"""select `Category 4 ID`
                                from db_name.table_name citcctd
                                where `Category 4 ID` in {ids} and `Month` = {row['Month']} and `Category 3 ID` <> -1  
                                order by `Month` DESC""")[0][0]
                sql_part.append(
                    f"""({id}, {str(row['mal']).replace(',', '.')}, {row['Month']}, '{user_login}', now())""")
    except Exception as e:
        print(e)
        return await turn_context.send_activity(MessageFactory.text("Возникла ошибка с чтением файла"))

    sql_update_dict = "SYSTEM RELOAD DICTIONARY db_name.table_name"
    try:
        client = Client(**CH_CREDS_IRON_6)
        new_line = '\n'
        client.execute(
            f"""insert into db_name.table_name  {f"  {new_line} ".join(sql_part)}
            """
        )
        all_shards = [
            CH_CREDS_IRON_1,
            CH_CREDS_IRON_2,
            CH_CREDS_IRON_3,
            CH_CREDS_IRON_4,
            CH_CREDS_IRON_5,
            CH_CREDS_IRON_6
        ]
        for creds in all_shards:
            client_temp = Client(**creds)
            client_temp.execute(sql_update_dict)
    except Exception as e:
        return await turn_context.send_activity(MessageFactory.text("Возникла ошибка с SQL запросом, попробуйте позже"))
    return await turn_context.send_activity(MessageFactory.text("Новые малышки сохранены"))