import sys
import os

import pymysql
import pymysql.cursors

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_CONFIG

def get_connection() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

class DBSession:

    def __init__(self):
        self._conn: pymysql.connections.Connection | None = None

    def __enter__(self) -> pymysql.connections.Connection:
        self._conn = get_connection()
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is None:
            return False
        try:
            if exc_type:
                self._conn.rollback()
            else:
                self._conn.commit()
        finally:
            self._conn.close()
        return False

def query(sql: str, args=None) -> list[dict]:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

def query_one(sql: str, args=None) -> dict | None:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

def execute(sql: str, args=None) -> tuple[int, int]:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.rowcount, cur.lastrowid

def execute_many(sql: str, args_list: list) -> int:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, args_list)
            return cur.rowcount
