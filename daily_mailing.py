from datetime import datetime
from dateutil.relativedelta import *
import pandas as pd
from pytz import timezone
from mailing_utils import *
from bots.activity_utils import create_file_card_activity
from bots.commands import malushka_csv, tariffs_matrix, cost_fbs
import asyncio
from async_cron.job import CronJob
from async_cron.schedule import Scheduler
import pytz
from bots.activity_utils import create_mailing_message
from bots.quaries import Query
import threading
from app import APP_ID, ADAPTER


async def _send_proactive_message(app_id, adapter, users, message):
    conversation_references = Query.load_conversation_references()
    for user_login in users:
        if user_login in conversation_references.keys():
            await adapter.continue_conversation(
                conversation_references[user_login],
                lambda turn_context: turn_context.send_activity(message),
                app_id,
            )


async def malushka_csv_mailing(app_id, adapter):
    time_start = datetime.now(timezone('Europe/Moscow')).strftime("%Y-%m-%d %H:%M:%S")
    months = [datetime.now().strftime("%Y%m")]
    df = malushka_csv(months)
    n = len(df)
    if n > 0:
        filepath = get_file_path_mailings('calc3_malushka.csv')                                
        df.to_csv(filepath, encoding="windows-1251", sep=';', index=False)
    else:
        filepath = None
    today = datetime.now().strftime("%Y - %m - %d")
    text = f"""!ЕЖЕДНЕВНАЯ РАССЫЛКА: Категории без малышки, {today}!\r\n Количество категорий без малышки = {n}"""
    message = create_mailing_message(text, filepath)
    emails = get_emails('count_mal')
    users = [maile[:8] for maile in emails]
    await _send_proactive_message(app_id, adapter, users, message)

    with open(filepath, 'rb') as f:
        logging(time_start, 'Empty Malushka','Done', n)
        if n > 0:
            send_email('',
                       f'Количество категорий без малышки = {n}',
                       emails,
                       attachments=[filepath])
            log_entry('User: file calc3_malushka.csv was updated and sent to users')
    return


async def tariffs_matrix_mailing(app_id, adapter):
    filepath = get_file_path_mailings('Calc3_tariffs_matrix_id.csv')
    df = tariffs_matrix()
    df.to_csv(filepath, encoding="windows-1251", sep=';', index=False)
    today = datetime.now().strftime("%Y - %m - %d")
    text = f"""!ЕЖЕДНЕВНАЯ РАССЫЛКА: tariffs_matrix, {today}!"""
    message = create_mailing_message(text, filepath)
    emails = get_emails("tariffs_matrix")
    users = [maile[:8] for maile in emails]
    await _send_proactive_message(app_id, adapter, users, message)
    
    with open(filepath, 'rb') as f:
        send_email('',
                   'tariffs_matrix',
                   emails,
                   attachments=[filepath])
        log_entry('User: file Calc3_tariffs_matrix_id.csv was updated and sent to users')
    return


async def cost_fbs_mailing(app_id, adapter):
    filepath = get_file_path_mailings('Calc3_std_cost_fbs_id.csv')
    df = cost_fbs()
    df.to_csv(filepath, encoding="windows-1251", sep=';', index=False)
    today = datetime.now().strftime("%Y - %m - %d")
    text = f"""!ЕЖЕДНЕВНАЯ РАССЫЛКА: cost_fbs, {today}!"""
    message = create_mailing_message(text, filepath)
    emails = get_emails("std_cost_fbs")
    users = [maile[:8] for maile in emails]
    await _send_proactive_message(app_id, adapter, users, message)

    with open('Calc3_std_cost_fbs_id.csv', 'rb') as f:
        send_email('',
                   'cost_fbs',
                   emails,
                   attachments=['Calc3_std_cost_fbs_id.csv'])
        log_entry('User: file Calc3_std_cost_fbs_id.csv was updated and sent to users')
    return


def cron_sched(app_id, adapter, conversation_references):
    msh = Scheduler()
    mal_job = CronJob(name='malushka_csv_mailing').every().day.at("10:00").go(malushka_csv_mailing, app_id, adapter, conversation_references)
    triffmat_job = CronJob(name='tariffs_matrix_mailing').every().day.at("10:00").go(tariffs_matrix_mailing, app_id, adapter, conversation_references)
    costfbs_job = CronJob(name='cost_fbs_mailing').every().day.at("10:00").go(cost_fbs_mailing, app_id, adapter, conversation_references)

    msh.add_job(mal_job)
    msh.add_job(triffmat_job)
    msh.add_job(costfbs_job)
    return msh

# def target_callback():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     # loop = asyncio.get_event_loop()
#     mailings = cron_sched(APP_ID, ADAPTER)
#     loop.run_until_complete(mailings.start())


if __name__ == '__main__':
    # _thread = threading.Thread(target=target_callback)
    # _thread.start()
    pass