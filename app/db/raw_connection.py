# Простое подключение к PostgreSQL без пула
import psycopg2
from flask import g
from app.config import DATABASE_CONFIG

def connect():
    if 'db_conn' not in g:
        g.db_conn = psycopg2.connect(**DATABASE_CONFIG)
    return g.db_conn

def close_connection(exception):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()