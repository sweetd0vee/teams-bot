from botbuilder.core import MessageFactory, TurnContext
from ..activity_utils import create_file_card_activity
from .utils import *
from clickhouse_driver.client import Client
import pandas as pd


def tariffs_matrix_checks(months: list, versions: list, filepath: str) -> pd.DataFrame:
    """
    The function collects data in slice: month, version and compares the data in calc 
    with the data in tariffs_matrix and saves it to provided filepath.
    :Returns: the dataframe with differencies found.
    """
    iron_sh3_client = Client(**CH_CREDS_IRON_3)
    iron_sh6_client = Client(**CH_CREDS_IRON_6)

    sql_data_calc = f"""
    SELECT DISTINCT `Month`,
    dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Version`))) as Version_str ,
    dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Cluster From`)))as`Cluster From` ,
    dictGet('db_name.table_name', 'Name',tuple(assumeNotNull(`Cluster To`)))as `Cluster To` 
    FROM db_name.table_name_d cmin 
    WHERE `Month` IN ({", ".join(months)}) AND Version in ({", ".join(versions)}) 
    ORDER BY `Month` ,Version ,`Cluster From` ,`Cluster To` 
    """
    sql_data_tariffs_matrix = f"""
    SELECT DISTINCT `Month` ,
    dictGet('db_name.table_name', 'Name',tuple(`Version`)) as Version_str, 
    dictGet('db_name.table_name', 'Name',tuple(`Cluster From` ))as`Cluster From` ,
    dictGet('db_name.table_name', 'Name',tuple(`Cluster To` ))as `Cluster To` 
    from db_name.table_name
    where `Month` in ({", ".join(months)}) and Version in ({", ".join(versions)})
    order by `Month` ,Version ,`Cluster From` ,`Cluster To` 
    """
    data_calc = iron_sh3_client.execute(sql_data_calc)
    df_data_calc = pd.DataFrame(data_calc, columns=['Month', 'Version', 'Cluster From', 'Cluster To'])
    data_tariffs_matrix = iron_sh6_client.execute(sql_data_tariffs_matrix)
    df_data_tariffs_matrix = pd.DataFrame(data_tariffs_matrix, columns=['Month', 'Version', 'Cluster From', 'Cluster To'])

    in_tariffs_matrix = pd.DataFrame(columns=['Month', 'Version', 'Cluster From', 'Cluster To'])
    in_calc = pd.DataFrame(columns=['Month', 'Version', 'Cluster From', 'Cluster To'])
    for index, row in df_data_tariffs_matrix.iterrows():
        value = df_data_calc[
            (df_data_calc['Cluster From'] == row['Cluster From']) &
            (df_data_calc['Cluster To'] == row['Cluster To']) &
            (df_data_calc['Month'] == row['Month']) &
            (df_data_calc['Version'] == row['Version'])
            ].values
        if len(value) == 0:
            in_tariffs_matrix = in_tariffs_matrix.append(row, ignore_index=True)
    for index, row in df_data_calc.iterrows():
        value = df_data_tariffs_matrix[
            (df_data_tariffs_matrix['Cluster From'] == row['Cluster From']) &
            (df_data_tariffs_matrix['Cluster To'] == row['Cluster To']) &
            (df_data_tariffs_matrix['Month'] == row['Month']) &
            (df_data_tariffs_matrix['Version'] == row['Version'])
            ].values
        if len(value) == 0:
            in_calc = in_calc.append(row, ignore_index=True)
    in_calc['Month'] = in_calc['Month'].astype('int64')
    in_tariffs_matrix['Month'] = in_tariffs_matrix['Month'].astype('int64')
    in_tariffs_matrix['Location'] = 'tariffs_matrix'
    in_calc['Location'] = 'calc'
    df_result = pd.concat([in_tariffs_matrix, in_calc])
    if filepath:
        df_result.to_excel(filepath, sheet_name='Check result', index=False)
    return df_result


async def cmd_tariffs_matrix_checks(turn_context: TurnContext, user_login: str):
    data = turn_context.activity.value
    months, message = validate_input_months(data)
    if not len(months):
        return await turn_context.send_activity(MessageFactory.text(message))
    versions, message = validate_input_versions(data)
    if not len(versions):
        return await turn_context.send_activity(MessageFactory.text(message))
    
    await turn_context.send_activity(MessageFactory.text("Ожидайте пожалуйста, проверка выполняется"))
    timestamp = turn_context.activity.local_timestamp
    filepath = get_filepath(f"tariffs_matrix_checks.xlsx", timestamp)
    df_errors = tariffs_matrix_checks(months, versions, filepath)
    if len(df_errors):
        reply_activity = create_file_card_activity(turn_context.activity, filepath, user_login,
                text=f"""Найденные ошибки по чекеру тарифф матрицы за месяца из списка: {', '.join(months)}, по версиям: {', '.join(versions)}""")
        return await turn_context.send_activity(reply_activity)
    else:
        return await turn_context.send_activity(MessageFactory.text(
            f"""Ошибок по тарифф матрице за месяца из списка: {', '.join(months)}, по версиям: {', '.join(versions)} найдено не было"""))