from ..activity_utils import create_file_card_activity
from botbuilder.core import MessageFactory, TurnContext
from clickhouse_driver.client import Client
import pandas as pd

from .utils import CH_CREDS_IRON_3, get_filepath, validate_input_months


def malushka_all(months: list) -> pd.DataFrame:
    iron_sh3_client = Client(**CH_CREDS_IRON_3)

    sql = f'''select distinct `Month`
        ,dictGet('db_name.table_name', 'Category 1',tuple(`Category 1`)) as `Category 1`
        ,dictGet('db_name.table_name', 'Category 4',tuple(`Category 4`)) 
        ,`Category 4`
        , mal
        from (select distinct `Month`,`Category 1`, `Category 4`as `Category 4`
        from db_name.table_name
        where `Month` where_filter and `Category 4`<>0
        ) t1 
        left join db_name.table_name t2 
        using (`Category 4`, `Month`)
        '''
    sql = sql.replace('where_filter', f"""in ({", ".join(months)})""")
    zero_metrics = iron_sh3_client.execute(sql, with_column_types=True)[0]
    df = pd.DataFrame.from_records(zero_metrics, columns=['Month', 'Category 1', 'Category 4', 'Category 4 ID', 'mal'])
    return df


async def cmd_malushka_all(turn_context: TurnContext, user_login: str):
    data = turn_context.activity.value
    months, message = validate_input_months(data)
    if len(months):
        df = malushka_all(months)
        timestamp = turn_context.activity.local_timestamp
        filepath = get_filepath(f"malushka_all.csv", timestamp)
        df.to_csv(filepath, encoding="windows-1251", sep=';', index=False)
        reply_activity = create_file_card_activity(turn_context.activity, filepath, user_login,
            text=f"""Файл со всеми мылышками за месяца из списка: {', '.join(months)}""")
        return await turn_context.send_activity(reply_activity)
    return await turn_context.send_activity(MessageFactory.text(message))
