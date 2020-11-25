import os
import pymysql
import pandas as pd

meta = {
    "host": os.getenv('USER_SERVICE_HOST'),
    "user": os.getenv('USER_SERVICE_USER'),
    "password": os.getenv("USER_SERVICE_PASSWORD"),
    "port": int(os.getenv("USER_SERVICE_PORT")),
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    conn = pymysql.connect(**meta)
    return conn


def get_signals(user_id):
    conn = get_connection()
    df = pd.read_sql(
        f"select * "
        f"from signals.signals "
        f"where user_id = {user_id}",
        conn
    )
    return df

