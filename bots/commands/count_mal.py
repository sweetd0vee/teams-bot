from botbuilder.core import MessageFactory, TurnContext
from clickhouse_driver.client import Client
from .utils import CH_CREDS_IRON_3, validate_input_months


def count_mal(months):
    client_ch_i3 = Client(**CH_CREDS_IRON_3)

    sql = f'''
        select count(*) from( 
        select distinct `Month`, dictGet('db_name.table_name', 'Category 1',tuple(`Category 1`)) as `Category 1`
        ,dictGet('db_name.table_name', 'Category 4',tuple(`Category 4`)) , mal, t1.`Category 4`
        from 
        (
        select distinct `Month`, `Category 1`,`Category 4`as `Category 4`
        from db_name.table_name
        where `Month` where_filter and `Category 4`<>0
        ) t1 
        left join db_name.table_name t2 
        using (`Category 4`,`Month`)
        where t2.mal = 0 and `Category 1` <> 'Travel')    
        '''
    sql = sql.replace('where_filter', f"""in ({", ".join(months)})""")
    res = client_ch_i3.execute(sql, with_column_types=True)
    if len(res[0]) == 0:
        num_zero_metrics = 0
    else:
        num_zero_metrics = client_ch_i3.execute(sql, with_column_types=True)[0][0][0]
    return num_zero_metrics


async def cmd_count_mal(turn_context: TurnContext, user_login: str):
    """
    Respond to the users choice and display the suggested actions again.
    """
    data = turn_context.activity.value
    months, message = validate_input_months(data)
    if len(months):
        num_zero_metrics = count_mal(months)
        message = f"Количество пустых малышек за месяца из списка: {', '.join(months)} равно {num_zero_metrics}"
        await turn_context.send_activity(MessageFactory.text(message))
    else:
        await turn_context.send_activity(MessageFactory.text(message))