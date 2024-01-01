from ..activity_utils import create_file_card_activity
from botbuilder.core import MessageFactory, TurnContext
from clickhouse_driver.client import Client
import pandas as pd

from .get_all_shard_tables import get_all_shard_tables
from .utils import *


def get_useless_tables(tables_shards_list=[x for x in range(1,7)], time_delta=''):
    """
        Функция получает на вход список интересующих шардов tables_shards_list и время time_delta 
        Функция возвращает dataframe таблиц, которые расположены на выбранных шардах
        и не использовались, начиная с указанного времени
    """
    tables_list = get_all_shard_tables(tables_shards_list)
    sql_query = """select table, max(event_date) from ( 
                    select event_date, event_time, query_kind, arrayJoin(tables) table, `user`, databases
                    from system.query_log)
                """
    if time_delta:
        sql_query += f"""where event_time >= '{time_delta}'\n"""
    sql_query += """group by table"""

    shards = pd.unique(tables_list.shard)
    result_list = []
    for shard in shards:
        if shard == 1:
            result1 = pd.DataFrame(Client(**CH_CREDS_IRON_1).query_dataframe(sql_query))
            result1.insert(0, "shard", 1)
            result_list.append(result1)
        if shard == 2:
            result2 = pd.DataFrame(Client(**CH_CREDS_IRON_2).query_dataframe(sql_query))
            result2.insert(0, "shard", 2)
            result_list.append(result2)
        if shard == 3:
            result3 = pd.DataFrame(Client(**CH_CREDS_IRON_3).query_dataframe(sql_query))
            result3.insert(0, "shard", 3)
            result_list.append(result3)
        if shard == 4:
            result4 = pd.DataFrame(Client(**CH_CREDS_IRON_4).query_dataframe(sql_query))
            result4.insert(0, "shard", 4)
            result_list.append(result4)
        if shard == 5:
            result5 = pd.DataFrame(Client(**CH_CREDS_IRON_5).query_dataframe(sql_query))
            result5.insert(0, "shard", 5)
            result_list.append(result5)
        if shard == 6:
            result6 = pd.DataFrame(Client(**CH_CREDS_IRON_6).query_dataframe(sql_query))
            result6.insert(0, "shard", 6)
            result_list.append(result6)
    result = pd.concat(result_list, axis=0)
    
    tables_list = tables_list.assign(table = tables_list.database + '.' + tables_list.table_name)
    if not (result.empty or tables_list.empty):
        tables_list = tables_list.merge(result, how='left', left_on=['shard', 'table'], right_on=['shard', 'table'])
        result = tables_list.loc[tables_list.max_event_date_.notnull()]
        result.drop(columns = ['max_event_date_'],axis = 1, inplace=True)
    else:
        result = pd.DataFrame({'index' : [], 'shard' : [], 'database' : [], 'table_name' : [], 'table' : []})
    return result


async def cmd_get_useless_tables(turn_context: TurnContext, user_login: str):
    data = turn_context.activity.value
    if 'shards' not in data:
        await turn_context.send_activity(MessageFactory.text("""Вы не выбрали список шардов для 
                        выгрузки неиспользуемых таблиц, попробуйте еще раз"""))
    elif 'start_date' not in data:
        await turn_context.send_activity(MessageFactory.text("""Вы не ввели дату, начиная с которой хотите узнать,
                        какие таблицы не использовались, попробуйте еще раз"""))
    else:
        shards = list(map(int, data['shards'].split(',')))
        start_date = data['start_date']
        df = get_useless_tables(shards, start_date)
        timestamp = turn_context.activity.local_timestamp
        filepath = get_filepath(f"useless_tables.xlsx", timestamp)
        df.to_excel(filepath, index=False)
        reply_activity = create_file_card_activity(turn_context.activity, filepath, user_login,
            text=f"Файл со всеми таблицами на выбранных шардах: {data['shards']}, которые не использовались начиная с {start_date}")
        await turn_context.send_activity(reply_activity)
