from botbuilder.core import TurnContext, MessageFactory
from clickhouse_driver.client import Client
import pandas as pd

from ..activity_utils import create_file_card_activity
from .utils import CH_CREDS_IRON_3, dicts, get_filepath


def tariffs_matrix():
    """
    Returns the data in Calc3_tariffs_matrix_id.
    """
    iron_sh3_client = Client(**CH_CREDS_IRON_3)

    sql = '''SELECT sc.name FROM system.columns sc 
            WHERE sc.database LIKE ('db_name') AND sc.table LIKE ('table_name')
        '''
    all_columns = iron_sh3_client.execute(sql, with_column_types=True)[0]
    sql_columns = []
    columns = []
    for col in all_columns:
        c = col[0]
        columns.append(c)
        if c in dicts:
            sql_columns.append(f"{dicts[c]}")
        else:
            sql_columns.append(f"`{c}`")
    sql = 'select ' + ','.join(sql_columns) + 'from db_name.table_name'
    zero_metrics = iron_sh3_client.execute(sql, with_column_types=True)[0]
    df = pd.DataFrame.from_records(zero_metrics, columns=columns)
    for c in columns:
        df[c] = df[c].astype('str').str.replace('.', ',')
    return df


async def cmd_tariffs_matrix(turn_context: TurnContext, user_login: str):
    await turn_context.send_activity(MessageFactory.text("Ожидайте пожалуйста, выгрузка выполняется"))
    df = tariffs_matrix()
    timestamp = turn_context.activity.local_timestamp
    filepath = get_filepath(f"tariffs_matrix.xlsx", timestamp)
    df.to_excel(filepath, index=False)
    reply_activity = create_file_card_activity(turn_context.activity, filepath, user_login,
        text="Выгруженные данные из db_name.table_name:\r\n")
    return await turn_context.send_activity(reply_activity)

