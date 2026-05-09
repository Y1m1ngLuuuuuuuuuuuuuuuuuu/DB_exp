import sys
import os

import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_CONFIG

def get_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname=DB_CONFIG["database"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )

class DBSession:

    def __init__(self):
        self._conn = None

    #进入和退出，执行结果没有报错，自动提交
    def __enter__(self):
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

#select发挥所有或者一个结果，行
#调用enter接受返回的connection
def query(sql: str, args=None) -> list[dict]:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return [dict(row) for row in cur.fetchall()]

def query_one(sql: str, args=None) -> dict | None:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            row = cur.fetchone()
            return dict(row) if row else None

#insert delete update执行，一次或者多次
def execute(sql: str, args=None) -> tuple[int, int | None]:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            generated_id = None
            if cur.description:
                row = cur.fetchone()
                if row:
                    generated_id = next(iter(row.values()))
            return cur.rowcount, generated_id

def execute_many(sql: str, args_list: list) -> int:
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, args_list)
            return cur.rowcount
