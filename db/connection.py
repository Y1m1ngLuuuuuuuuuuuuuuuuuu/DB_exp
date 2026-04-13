"""
db/connection.py —— 数据库连接管理

提供:
  - get_connection()   获取一条原始 PyMySQL 连接
  - DBSession          上下文管理器，自动提交 / 回滚，用完自动关闭
  - query()            执行 SELECT，返回 list[dict]
  - query_one()        执行 SELECT，返回第一行 dict 或 None
  - execute()          执行 INSERT/UPDATE/DELETE，返回 (rowcount, lastrowid)
"""

import sys
import os

import pymysql
import pymysql.cursors

# 确保项目根目录在 sys.path 中，以便 import config
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_CONFIG


# ── 基础连接 ─────────────────────────────────────────────────

def get_connection() -> pymysql.connections.Connection:
    """返回一条新的数据库连接（DictCursor）。调用方负责关闭。"""
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


# ── 上下文管理器 ─────────────────────────────────────────────

class DBSession:
    """
    用法::

        with DBSession() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

    发生异常时自动 rollback，正常退出时自动 commit。
    """

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
        return False  # 不吞异常


# ── 便捷查询辅助函数 ─────────────────────────────────────────

def query(sql: str, args=None) -> list[dict]:
    """
    执行查询语句，返回全部行（每行为 dict）。

    :param sql:  带 %s 占位符的 SQL 字符串
    :param args: 参数元组或列表，单个值也要写成 (val,)
    """
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()


def query_one(sql: str, args=None) -> dict | None:
    """
    执行查询语句，返回第一行 dict；无结果时返回 None。
    """
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()


def execute(sql: str, args=None) -> tuple[int, int]:
    """
    执行 INSERT / UPDATE / DELETE，返回 (rowcount, lastrowid)。

    :returns: (受影响行数, 最后插入的自增 ID)
    """
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.rowcount, cur.lastrowid


def execute_many(sql: str, args_list: list) -> int:
    """
    批量执行同一语句，返回受影响总行数。

    :param args_list: 参数列表，每个元素是一个元组
    """
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, args_list)
            return cur.rowcount
