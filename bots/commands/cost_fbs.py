from clickhouse_driver.client import Client
from botbuilder.core import TurnContext, MessageFactory
import pandas as pd
from ..activity_utils import create_file_card_activity
from .utils import CH_CREDS_IRON_3, dicts, get_filepath


def cost_fbs():
    """
    Returns the data.
    """
    client_ch_i3 = Client(**CH_CREDS_IRON_3)
    sql = '''SELECT sc.name FROM system.columns sc 
            WHERE sc.database LIKE ('db_name') AND sc.table LIKE ('table_name')
        '''
    column_names = client_ch_i3.execute(sql, with_column_types=True)[0]
    sql_columns, columns = [], []
    for col in column_names:
        c = col[0]
        columns.append(c)
        if c in dicts:
            sql_columns.append(f"{dicts[c]}")
        else:
            sql_columns.append(f"`{c}`")

    sql = 'select ' + ','.join(sql_columns) + ' from db_name.table_name'
    zero_metrics = client_ch_i3.execute(sql)
    df = pd.DataFrame.from_records(zero_metrics, columns=columns)
    for c in columns:
        df[c] = df[c].astype('str').str.replace('.', ',')
    return df


async def cmd_cost_fbs(turn_context: TurnContext, user_login: str):
    """
    Processes the user's request on getting data from db_name.table_name.
    Sends the data saved in a .csv file format.
    """
    await turn_context.send_activity(MessageFactory.text("Ожидайте пожалуйста, выгрузка выполняется"))
    df = cost_fbs()
    print(df)
    timestamp = turn_context.activity.local_timestamp
    filepath = get_filepath(f"Calc3_std_cost_fbs_id.xlsx", timestamp)
    df.to_excel(filepath, index=False)
    print('saved')
    reply_activity = create_file_card_activity(turn_context.activity, filepath, user_login,
        "Выгруженные данные из DP_Analytics_dictionaries.Calc3_st_cost_fbs_id_dict:\r\n")
    await turn_context.send_activity(reply_activity)
