from ..activity_utils import create_file_card_activity
from botbuilder.core import MessageFactory, TurnContext
from clickhouse_driver.client import Client
from dateutil.relativedelta import relativedelta
from datetime import datetime
from .utils import *
import pandas as pd


def logist_checks(months: str, version: str, filepath=None) -> pd.DataFrame:
    """
    The function collects data in slice: month, version to check according
    advanced checkers standards and saves it to provided file path.
    :Returns: the dataframe with errors found
    """
    iron_sh3_client = Client(**CH_CREDS_IRON_3)
    iron_sh6_client = Client(**CH_CREDS_IRON_6)

    def parse_formula(formula):
        global uniq_dicts
        splited_formula = formula.split("`")
        for i in range(1, len(splited_formula), 2):
            if splited_formula[i] in dict_of_dicts and splited_formula[i] not in uniq_dicts:
                uniq_dicts.append(dict_of_dicts[splited_formula[i]])
        return

    def get_all_dicts(df):
        df = df.loc[df['Type'] == 'Dic_Metric']
        dict_of_dicts = {}
        for line in df.values.tolist():
            dict_of_dicts[line[1]] = line[2]
        return dict_of_dicts

    def metrics_list_to_sql(list_with_metrics, mode):
        metric_formula = []
        metrics_additional = []
        list_metric_formuls = list(df_metric_formuls['Metric'])
        for metric in list_with_metrics:
            if metric in list_metric_formuls:
                metric_index = list_metric_formuls.index(metric)
                if df_metric_formuls['Formula'][metric_index] and df_metric_formuls['Type'][
                    metric_index] != 'Not_Calc' and df_metric_formuls['Metric'][
                    metric_index] not in not_calc_metrics and mode == 'select':
                    metric_formula.append([metric, df_metric_formuls['Formula'][metric_index]])
                    metrics_additional += list(df_metric_formuls['Count'][metric_index].split(","))
                    parse_formula(df_metric_formuls['Formula'][metric_index])
                elif metric in ['Posting', 'Orders']:
                    if mode == 'select':
                        metric_formula.append([metric, f"any(`{metric}`)"])
                else:
                    if mode == 'select':
                        metric_formula.append([metric, f"sum(`{metric}`)"])
                        metrics_additional += [metric]
                    else:
                        metric_formula.append([metric, f"argMax(`{metric}`,Time_load)"])
        str_sql_part = []
        for i in range(len(metric_formula)):
            str_sql_part.append(f"{metric_formula[i][1]} as `{metric_formula[i][0]}`")

        return str_sql_part, metrics_additional

    sql_get_checks = f"""
    select `Category 1`,`Sales Schema`,`Ozon 1P`,`Metric`,`Cluster From`,`1_cond`,`2_cond`
    from db_name.table_name
    where `Type` = 'Логистика'
    """
    checks = iron_sh3_client.execute(sql_get_checks, with_column_types=True)
    df = pd.DataFrame(checks[0])
    df.columns = [i[0] for i in checks[1]]

    sql_get_actual_metrics = f"""
    select Metric
    from db_name.table_name
    where BT = 'MP'
    """
    actual_metrics = iron_sh6_client.execute(sql_get_actual_metrics)
    actual_metrics = [i[0] for i in actual_metrics]
    all_metrics = list(dict.fromkeys([i for i in df['Metric']]))
    for metric in all_metrics:
        if not metric in actual_metrics:
            all_metrics.remove(metric)

    sql_get_log_formula = f"""
    select script
    from db_name.table_name cmsit
    where id = 2 and `position` in (2,5)
    order by `position` 
    """
    formulas = iron_sh6_client.execute(sql_get_log_formula)
    main_formula = formulas[0][0]
    log_formula = formulas[1][0]
    main_formula_for_log = formulas[0][0]

    sql_get_formuls = f"""
    select `Type`,Metric,Sum,Count
    from db_name.table_name
    where BT = 'MP'
    """
    df_metric_formuls = pd.DataFrame(iron_sh6_client.execute(sql_get_formuls))
    df_metric_formuls.columns = ['Type', 'Metric', 'Formula', 'Count']
    dict_of_dicts = get_all_dicts(df_metric_formuls)
    df_log = df.loc[df['Cluster From'] != '']
    df_main = df.loc[df['Cluster From'] == '']
    uniq_metrics_main = list(dict.fromkeys([i for i in df_main['Metric']]))
    uniq_metrics_main = [metric for metric in uniq_metrics_main if metric in all_metrics]
    uniq_metrics_log = list(dict.fromkeys([i for i in df_log['Metric']]))
    uniq_metrics_log = [metric for metric in uniq_metrics_log if metric in all_metrics]

    metrics_additional = []
    not_calc_metrics = [
        'GMV D-R',
        'GMV D-R Travel'
    ]
    new_line = "\n"
    uniq_metrics_log_in_main = []
    for metric in uniq_metrics_log:
        temp_df = df_metric_formuls.loc[df_metric_formuls['Metric'] == metric]
        if temp_df['Type'].values[0] != 'Log_Columns':
            uniq_metrics_log.remove(metric)
            uniq_metrics_log_in_main.append(metric)

    global uniq_dicts
    uniq_dicts = []

    str_sql_part_select, str_sql_part_additional_metrics = metrics_list_to_sql(uniq_metrics_main, 'select')
    uniq_metrics_additional = list(dict.fromkeys([i for i in str_sql_part_additional_metrics]))
    str_sql_part_additional_metrics, temp = metrics_list_to_sql(uniq_metrics_additional, 'additional')

    uniq_dicts_main = list(dict.fromkeys([i for i in uniq_dicts]))


    uniq_dicts = []
    str_sql_part_select_log, str_sql_part_additional_metrics_log = metrics_list_to_sql(uniq_metrics_log, 'select')
    uniq_metrics_additional_log = list(dict.fromkeys([i for i in str_sql_part_additional_metrics_log]))
    str_sql_part_additional_metrics_log, temp = metrics_list_to_sql(uniq_metrics_additional_log, 'additional')
    uniq_dicts_log = list(dict.fromkeys([i for i in uniq_dicts]))


    uniq_dicts = []
    str_sql_part_select_log_in_main, str_sql_part_additional_metrics_log_in_main = metrics_list_to_sql(
        uniq_metrics_log_in_main, 'select')
    uniq_metrics_additional_log_in_main = list(dict.fromkeys([i for i in str_sql_part_additional_metrics_log_in_main]))
    str_sql_part_additional_metrics_log_in_main, temp = metrics_list_to_sql(uniq_metrics_additional_log_in_main, 'additional')
    uniq_dicts_log_in_main = list(dict.fromkeys([i for i in uniq_dicts]))

    complicated_formulas = []
    easy_formulas = []
    for formula in str_sql_part_select:
        if len(formula.split('`')) == 5:
            easy_formulas.append(formula)
        else:
            complicated_formulas.append(formula)

    for i in range(len(complicated_formulas)):
        for formula in easy_formulas:
            to_rep, rep_on = tuple(formula.split(' as '))
            if to_rep in complicated_formulas[i]:
                complicated_formulas[i] = complicated_formulas[i].replace(to_rep, rep_on)
            else:
                complicated_formulas[i] = complicated_formulas[i].replace(rep_on, f"t1.{rep_on}")
    str_sql_part_select = easy_formulas + complicated_formulas

    complicated_formulas_log = []
    easy_formulas_log = []
    for formula in str_sql_part_select_log:
        if len(formula.split('`')) == 5:
            easy_formulas_log.append(formula)
        else:
            complicated_formulas_log.append(formula)

    for i in range(len(complicated_formulas_log)):
        if 'as `Inbound direct cost`' in complicated_formulas_log[i]:
            complicated_formulas_log[i] = complicated_formulas_log[i].replace('`Inbound Total Items`','(t1.`Inbound direct items` + t1.`Inbound XD items` + if(Month>=202110 and t1.Version in (1,2),t1.`Replenishment In log` + t1.`Inbound Repl items`, 0))')
            break

    for i in range(len(complicated_formulas_log)):
        for formula in easy_formulas_log:
            to_rep, rep_on = tuple(formula.split(' as '))
            if to_rep in complicated_formulas_log[i]:
                complicated_formulas_log[i] = complicated_formulas_log[i].replace(to_rep, rep_on)
            else:
                complicated_formulas_log[i] = complicated_formulas_log[i].replace(rep_on, f"{rep_on}")
    str_sql_part_select_log = easy_formulas_log + complicated_formulas_log

    complicated_formulas_log_in_main = []
    easy_formulas_log_in_main = []
    for formula in str_sql_part_select_log_in_main:
        if len(formula.split('`')) == 5:
            easy_formulas_log_in_main.append(formula)
        else:
            complicated_formulas_log_in_main.append(formula)

    for i in range(len(complicated_formulas_log_in_main)):
        if '`Sales Schema`' in complicated_formulas_log_in_main[i]:
            complicated_formulas_log_in_main[i] = complicated_formulas_log_in_main[i].replace('`Sales Schema`','t1.`Sales Schema`')

    for i in range(len(complicated_formulas_log_in_main)):
        for formula in easy_formulas_log_in_main:
            to_rep, rep_on = tuple(formula.split(' as '))
            if to_rep in complicated_formulas_log_in_main[i]:
                complicated_formulas_log_in_main[i] = complicated_formulas_log_in_main[i].replace(to_rep, rep_on)
            else:
                complicated_formulas_log_in_main[i] = complicated_formulas_log_in_main[i].replace(rep_on, f"t1.{rep_on}")
    str_sql_part_select_log_in_main = easy_formulas_log_in_main + complicated_formulas_log_in_main
    
    main_formula = main_formula.replace('Special_Dict_string', '')
    main_formula = main_formula.replace('Dict_string',f"""{f",{new_line}".join(uniq_dicts_main)},{new_line}if(if(`GMV D-R` = 0, 0, divide(`GMV D-R VAT`, `GMV D-R`)) > 1.2,1.2,if(`GMV D-R` = 0, 0, divide(`GMV D-R VAT`, `GMV D-R`))) AS VAT,{new_line}""")
    main_formula = main_formula.replace('Filter_string', f'where `Version_to_analitic`= 0 and  `Month` in ({months}) and (`Version` in ({version})) and `Sales Schema` in (11017671628710, 11017671628740) and `Cluster From` <> 11232294486660 and `Category 1` not in (11157140223310, 9831613841000)')
    main_formula = main_formula.replace('Orders_Join', "LEFT JOIN (select `Month`, `Version`, `Category 1`, `Sales Schema`, argMax(Orders, Time_load) AS Orders, argMax(Posting, Time_load) AS Posting from calc_mp.order_datamart_d where `Category 1` global in (select Distinct `Category 1` from calc_mp.filter_set_d where `Version_to_analitic`= 0 and  `Month` in (202108) and `Version` in (3)  ) group by `Month`, `Version`, `Category 1`, `Sales Schema`) t2 ON t1.Month = t2.Month AND  t1.Version = t2.Version AND  t1.`Sales Schema` = t2.`Sales Schema` AND  t1.`Category 1` = t2.`Category 1` ")
    main_formula = main_formula.replace('Columns_VBA', '`Category 1`  , `Month`  , `Sales Schema`  , `Version` ')
    main_formula = main_formula.replace('Super_join', '')
    main_formula = main_formula.replace('Log_full_Join', '')
    main_formula = main_formula.replace('Total_Join', '')
    main_formula = main_formula.replace('<work_schema>.<table_bind> t1', 'calc_mp.main_datamart_d t1')

    uniq_metrics_log1 = [f"`{i}`" for i in uniq_metrics_log]
    uniq_metrics_log_in_main1 = [f"`{i}`" for i in uniq_metrics_log_in_main]
    result_log_formula = iron_sh3_client.execute(main_formula_for_log, with_column_types=True)
    result_main_formula = iron_sh3_client.execute(main_formula, with_column_types=True)
    exclude_from_metrics = ['Category 1 ', 'Month', 'Sales Schema ', 'Version ']
    data_to_check = pd.DataFrame(result_main_formula[0])
    metrics = [i[0] for i in result_main_formula[1] if i[0] not in exclude_from_metrics]
    data_to_check.columns = exclude_from_metrics + metrics

    exclude_from_metrics = ['Category 1', 'Month', 'Sales Schema', 'Version', 'Cluster From']
    data_to_check_log = pd.DataFrame(result_log_formula[0])
    metrics_log = [i[0] for i in result_log_formula[1] if i[0] not in exclude_from_metrics]
    data_to_check_log.columns = exclude_from_metrics + metrics_log
    data_to_check_log = data_to_check_log.fillna(0)

    errors = []
    for index, row in data_to_check.iterrows():
        for metric in metrics:
            f_cond_s = df_main[
                (df_main["Category 1"] == row['Category 1 ']) & (df_main["Sales Schema"] == row['Sales Schema ']) & (
                            df_main['Metric'] == metric)]['1_cond']
            s_cond_s = df_main[
                (df_main["Category 1"] == row['Category 1 ']) & (df_main["Sales Schema"] == row['Sales Schema ']) & (
                            df_main['Metric'] == metric)]['2_cond']

            if len(f_cond_s) != 0:
                f_cond = list(f_cond_s)[0].replace(',', '.')
                if f_cond[0] == '=':
                    f_cond = f_cond.replace('=', '==')
                if s_cond_s.item() != '':
                    s_cond = list(s_cond_s)[0].replace(',', '.')
                    if s_cond[0] == '=':
                        s_cond = s_cond.replace('=', '==')
                    check = str(row[metric]) + f_cond + " and " + str(row[metric]) + s_cond
                    result_of_check = eval(check)
                    if not result_of_check:
                        errors.append([
                            row['Category 1 '],
                            row['Month'],
                            row['Sales Schema '],
                            row['Version '],
                            '',
                            metric,
                            str(row[metric]).replace('.', ','),
                            f_cond,
                            s_cond])
                else:
                    check = str(row[metric]) + f_cond
                    result_of_check = eval(check)
                    if not result_of_check:
                        errors.append([
                            row['Category 1 '],
                            row['Month'],
                            row['Sales Schema '],
                            row['Version '],
                            '',
                            metric,
                            str(row[metric]).replace('.', ','),
                            f_cond,
                            ''])
    for index, row in data_to_check_log.iterrows():
        for metric in metrics_log:
            f_cond_s = df[(df["Category 1"] == row['Category 1']) & (df["Sales Schema"] == row['Sales Schema']) & (
                        df['Metric'] == metric) & (df["Cluster From"] == row['Cluster From'])]['1_cond']
            s_cond_s = df[(df["Category 1"] == row['Category 1']) & (df["Sales Schema"] == row['Sales Schema']) & (
                        df['Metric'] == metric) & (df["Cluster From"] == row['Cluster From'])]['2_cond']

            if len(f_cond_s) != 0:
                f_cond = list(f_cond_s)[0].replace(',', '.')
                if f_cond[0] == '=':
                    f_cond = f_cond.replace('=', '==')
                if s_cond_s.item() != '':
                    s_cond = list(s_cond_s)[0].replace(',', '.')
                    if s_cond[0] == '=':
                       s_cond = s_cond.replace('=', '==')
                    check = str(row[metric]) + f_cond + " and " + str(row[metric]) + s_cond
                    result_of_check = eval(check)
                    if not result_of_check:
                        errors.append([
                            row['Category 1'],
                            row['Month'],
                            row['Sales Schema'],
                            row['Version'],
                            row['Cluster From'],
                            metric,
                            str(row[metric]).replace('.', ','),
                            f_cond,
                            s_cond])
                else:
                    check = str(row[metric]) + f_cond
                    result_of_check = eval(check)
                    if not result_of_check:
                        errors.append([
                            row['Category 1'],
                            row['Month'],
                            row['Sales Schema'],
                            row['Version'],
                            row['Cluster From'],
                            metric,
                            str(row[metric]).replace('.', ','),
                            f_cond,
                            ''])
    df_errors = pd.DataFrame(errors, columns=['Category 1', 'Month', 'Sales Schema', 'Version', 'Cluster From',
                                                'Metric', 'Value', 'Condition 1', 'Condition 2'])
    if filepath:
        df_errors.to_excel(filepath)
        # logist_errors_file(df_errors, filepath)
    return df_errors


async def cmd_logist_checks(turn_context: TurnContext, user_login: str):
    data = turn_context.activity.value
    months, message = validate_input_months(data)
    if not len(months):
        return await turn_context.send_activity(MessageFactory.text(message))
    versions, message = validate_input_versions(data)
    if not len(versions):
        return await turn_context.send_activity(MessageFactory.text(message))
    
    months_str = ', '.join(months)
    versions_str = ', '.join(versions)

    await turn_context.send_activity(MessageFactory.text("Ожидайте пожалуйста, проверка выполняется"))
    timestamp = turn_context.activity.local_timestamp
    filepath = get_filepath(f"errors_in_log.xlsx", timestamp)
    df_errors = logist_checks(months_str, versions_str, filepath)
    if len(df_errors):
        reply_activity = create_file_card_activity(turn_context.activity, filepath, user_login,
            text=f"Найденные ошибки по чекеру логистика за месяца из списка: {months_str}, по версиям: {versions_str}")
        return await turn_context.send_activity(reply_activity)
    else:
        return await turn_context.send_activity(MessageFactory.text(
            f"Ошибок по чекеру логистика за месяца из списка: {months_str}, по версиям {versions_str} найдено не было"))


def logist_checks_mailing_data(filepath: str) -> pd.DataFrame:
    """
    Returns the data from logist checks that should be sent as a daily mailing logist checks to some users.
    This data will be saved to filepath with mailing files.
    """
    months_for_fact = [(datetime.now() + relativedelta(months=-1 * i)).strftime("%Y%m") for i in
                       range(3, 0, -1)]
    months_for_estim = [(datetime.now() + relativedelta(months=1 * i)).strftime("%Y%m") for i in range(3)]
    errors_fact = logist_checks(", ".join(months_for_fact), "3")
    errors_estim = logist_checks(", ".join(months_for_estim), "1")
    df_errors = pd.concat([errors_fact, errors_estim])
    if len(df_errors):
        df_errors.to_csv(filepath, encoding="windows-1251", sep=';', index=False)
    return df_errors