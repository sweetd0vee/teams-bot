from botbuilder.core import MessageFactory, TurnContext
from ..activity_utils import create_file_card_activity
from .utils import CH_CREDS_IRON_3, get_filepath, validate_input_months
from clickhouse_driver.client import Client
import pandas as pd


def malushka_csv(months: list) -> pd.DataFrame:
    iron_sh3_client = Client(**CH_CREDS_IRON_3)

    sql = f'''select distinct `Month`
            ,dictGet('db_name.table_name', 'Category 1',tuple(`Category 1`)) as `Category 1`
            ,dictGet('db_name.table_name', 'Category 4',tuple(`Category 4`))
            , mal
            , t1.`Category 4`
            from (
            select distinct `Month`, `Category 1`,`Category 4`as `Category 4`
            from db_name.table_name
            where `Month` where_filter and `Category 4`<>0
            ) t1 
            left join db_name.table_name t2 
            using (`Category 4`,`Month`)
            where t2.mal = 0 and `Category 1` <> 'Travel'
            '''
    sql = sql.replace('where_filter', f"""in ({", ".join(months)})""")
    zero_metrics = iron_sh3_client.execute(sql)
    df = pd.DataFrame.from_records(zero_metrics, columns=['Month', 'Category 1', 'Category 4', 'mal', 'Category 4 ID'])
    return df


async def cmd_malushka_csv(turn_context: TurnContext, user_login: str):
    data = turn_context.activity.value
    months, message = validate_input_months(data)
    if len(months):
        df = malushka_csv(months)
        timestamp = turn_context.activity.local_timestamp
        filepath = get_filepath(f"calc3_malushka.csv", timestamp)
        df.to_csv(filepath, encoding="windows-1251", sep=';', index=False)
        reply_activity = create_file_card_activity(turn_context.activity, filepath, user_login,
                            text=f"Файл с пустыми малышками за месяца из списка: {', '.join(months)}")
        return await turn_context.send_activity(reply_activity)
    return await turn_context.send_activity(MessageFactory.text(message))
