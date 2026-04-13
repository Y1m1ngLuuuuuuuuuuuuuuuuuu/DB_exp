"""
db/__init__.py —— 将 db/ 声明为 Python 包，并导出常用接口。
"""
from db.connection import get_connection, DBSession, query, query_one, execute, execute_many

__all__ = [
    "get_connection",
    "DBSession",
    "query",
    "query_one",
    "execute",
    "execute_many",
]
