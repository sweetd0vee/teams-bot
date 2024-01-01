from clickhouse_driver.client import Client
from botbuilder.core import MessageFactory, TurnContext
from .utils import CH_CREDS_IRON_3


def get_table_owner(host, db, table):
    client_ch_i3 = Client(**CH_CREDS_IRON_3)
    sql_get_databases = f"""SELECT Table_name FROM db_name.table_name
                            WHERE Database = '{db}' AND Host = '{host}'
                        """
    res = client_ch_i3.execute(sql_get_databases, with_column_types=True)[0]
    if not len(res):
        return f"Информации по базе данных {db} нет, проверьте правильно ли выбран хост {host}, введено название бд, попробуйте еще раз"
    sql_get_table = f"""SELECT argMax(Creator, Create_time) AS Creator, MAX(Create_time)
                        FROM bot_dev.Mal_tables_creators
                        WHERE Database = '{db}' AND Table_name = '{table}' AND Host = '{host}'
                    """
    res = client_ch_i3.execute(sql_get_table)[0]
    if not len(res[0]):
        return f"Информации по таблице {db}.{table} нет, проверьте правильно ли указан хост {host}, введены названия таблицы и бд"
    (creator, creation_time) = res[0], res[1]
    return f"""Хост: {host} \r\nТаблица: {db}.{table} \r\nВладелец: {creator} \r\nДата создания: {creation_time}"""


async def cmd_get_table_owner(turn_context: TurnContext, user_login: str):
    """
        Processes user's request to get the information about table_creator and time when it was created.
        Takes as an input the name of host, data base and table name provided by the user.
    """
    data = turn_context.activity.value
    if 'host' not in data:
        message = f"Вы не указали host, на котором находится таблица, заполните поле и попробуйте еще раз"
        return await turn_context.send_activity(MessageFactory.text(message))
    if 'table' not in data:
        message = f"Вы не указали таблицу для поиска, заполните поле и попробуйте еще раз"
        return await turn_context.send_activity(MessageFactory.text(message))
    table = data['table'].split('.')
    if len(table) != 2:
        message = f"Неверно указано название таблицы или база данных, попробуйте еще раз"
        return  await turn_context.send_activity(MessageFactory.text(message))
    db = table[0]
    table_name = table[1]
    message = get_table_owner(data['host'], db, table_name)
    return await turn_context.send_activity(MessageFactory.text(message))
