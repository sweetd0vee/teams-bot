from vault.vault_config import MAILING_USER, MAILING_PASSWORD
from bots.commands.utils import CH_CREDS_CLOUD_1
from clickhouse_driver.client import Client
from datetime import datetime
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os.path import basename
from pytz import timezone
import os


client_ch_c1 = Client(**CH_CREDS_CLOUD_1)


def get_file_path_mailings(file_name: str) ->str:
    """
    Returns the full path to generated file with the name: file_name.
    """
    file_path = os.path.join(os.getcwd(), f"resources/files/mailings/{file_name}")
    return file_path


def get_emails(mailing):
    emails_sql = f"SELECT DISTINCT Email db_name.table_name WHERE Mailing = '{mailing}'"
    emails = [email[0] for email in client_ch_c1.execute(emails_sql)]
    return emails


def logging(time_start, process,status, result):
    time_load = datetime.now(timezone('Europe/Moscow')).strftime("%Y-%m-%d %H:%M:%S")
    sql_query_web_log = f"""
    insert into db_name.table_name (Time_load,`Start_dttm`,End_dttm,Project,`Status`,`Result`)
    values ('{time_load}','{time_start}','{time_load}','{process}','{status}','{result}')
    """
    client_ch_c1.execute(sql_query_web_log)
    return


def log_entry(text):
    with open('log.txt', 'a') as file:
        time = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        file.write(f'{time}: {text}\n')
    return


def send_email(text, subject, to, attachments=[]):
    fr = f'Malushka <{MAILING_USER}>'
    msg = MIMEMultipart()
    msg['From'] = fr
    msg['To'] = ','.join(to)
    msg['Subject'] = subject
    msg.attach(MIMEText(text, 'html'))
    for filename in attachments:
        with open(filename, 'rb') as f:
            att = MIMEApplication(f.read())
        att.add_header('Content-Disposition', 'attachment', filename=basename(filename))
        msg.attach(att)
    try:
        server = smtplib.SMTP('')
        server.login(MAILING_USER, MAILING_PASSWORD)
        server.sendmail(fr, to, msg.as_string())
        server.close()
    except Exception as e:
        print(e)
    return