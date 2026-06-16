#!/usr/bin/env python3
"""Generate local demo credentials and sync password hashes into init.sql.

Plain-text demo passwords are written only under secrets/, which is ignored by
git. The public SQL seed keeps only SHA-256 password hashes.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import string
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_SQL = ROOT / "opengauss_setup" / "sql" / "init.sql"
SECRETS_DIR = ROOT / "secrets"
LOCAL_SQL_DIR = ROOT / "opengauss_setup" / "sql" / "local"
CREDENTIALS_MD = SECRETS_DIR / "DEMO_ACCOUNT_CREDENTIALS.md"
EXAMPLE_MD = ROOT / "docs" / "DEMO_ACCOUNT_CREDENTIALS.example.md"
LOCAL_DB_GRANTS = LOCAL_SQL_DIR / "grant_demo_db_accounts_20260611.sql"
LOCAL_ACCOUNT_SEED = LOCAL_SQL_DIR / "seed_demo_accounts_20260611.sql"


@dataclass(frozen=True)
class DemoAccount:
    role: str
    profile_id: str
    username: str
    display_name: str
    old_username: str


DEMO_ACCOUNTS = [
    DemoAccount("admin", "A001", "A001", "系统管理员", "admin"),
    DemoAccount("teacher", "T001", "T001", "张明", "t_zhang"),
    DemoAccount("teacher", "T002", "T002", "李晓华", "t_li"),
    DemoAccount("teacher", "T003", "T003", "王志强", "t_wang"),
    DemoAccount("teacher", "T004", "T004", "孙敏", "t_sun"),
    DemoAccount("student", "20240001", "20240001", "王小明", "s_001"),
    DemoAccount("student", "20240002", "20240002", "陈雨欣", "s_002"),
    DemoAccount("student", "20240003", "20240003", "刘强", "s_003"),
    DemoAccount("student", "20240004", "20240004", "赵雨桐", "s_004"),
    DemoAccount("student", "20240005", "20240005", "周子豪", "s_005"),
    DemoAccount("student", "20240006", "20240006", "林可欣", "s_006"),
    DemoAccount("student", "20240007", "20240007", "何俊杰", "s_007"),
    DemoAccount("student", "20240008", "20240008", "郭书瑶", "s_008"),
    DemoAccount("student", "20240009", "20240009", "许嘉宁", "s_009"),
    DemoAccount("student", "20240010", "20240010", "高远", "s_010"),
    DemoAccount("student", "20240011", "20240011", "唐诗雨", "s_011"),
    DemoAccount("student", "20240012", "20240012", "冯博文", "s_012"),
]


def random_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(ch.islower() for ch in password)
            and any(ch.isupper() for ch in password)
            and any(ch.isdigit() for ch in password)
        ):
            return password


def sha256_hex(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_user_account_insert(password_hashes: dict[str, str]) -> str:
    rows = []
    for account in DEMO_ACCOUNTS:
        rows.append(
            f"({sql_quote(account.username):<12}, "
            f"{sql_quote(password_hashes[account.username])}, "
            f"{sql_quote(account.role)})"
        )
    return (
        "INSERT INTO user_account (username, password_hash, role) VALUES\n"
        + ",\n".join(rows)
        + ";"
    )


def update_init_sql(password_hashes: dict[str, str]) -> None:
    text = INIT_SQL.read_text(encoding="utf-8")
    new_insert = build_user_account_insert(password_hashes)
    text = re.sub(
        r"INSERT INTO user_account \(username, password_hash, role\) VALUES\n.*?;",
        new_insert,
        text,
        flags=re.S,
    )
    for account in DEMO_ACCOUNTS:
        text = text.replace(
            f"FROM user_account WHERE username = '{account.old_username}';",
            f"FROM user_account WHERE username = '{account.username}';",
        )
    INIT_SQL.write_text(text, encoding="utf-8")


def write_credentials(passwords: dict[str, str], generated_at: str) -> None:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Demo Account Credentials",
        "",
        f"生成时间：{generated_at}",
        "",
        "说明：",
        "- 本文件仅用于本地演示和测试。",
        "- 不应提交到公开仓库。",
        "- 不应写入正式报告 PDF。",
        "- 数据库 `user_account` 表只保存 `password_hash`。",
        "- 明文初始密码仅用于首次登录演示。",
        "",
        "| role | profile_id | username | display_name | initial_password |",
        "| --- | --- | --- | --- | --- |",
    ]
    for account in DEMO_ACCOUNTS:
        lines.append(
            f"| {account.role} | {account.profile_id} | {account.username} | "
            f"{account.display_name} | {passwords[account.username]} |"
        )
    CREDENTIALS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_example() -> None:
    EXAMPLE_MD.write_text(
        """# Demo Account Credentials Example

本文件只展示格式，不包含真实初始密码。

| role | profile_id | username | display_name | initial_password |
| --- | --- | --- | --- | --- |
| admin | A001 | A001 | 系统管理员 | <generated-locally> |
| teacher | T001 | T001 | 张明 | <generated-locally> |
| student | 20240001 | 20240001 | 王小明 | <generated-locally> |
""",
        encoding="utf-8",
    )


def write_local_db_grants() -> None:
    LOCAL_SQL_DIR.mkdir(parents=True, exist_ok=True)
    db_passwords = {
        "db_app_demo_user": random_password(18),
        "db_student_demo_user": random_password(18),
        "db_teacher_demo_user": random_password(18),
        "db_admin_demo_user": random_password(18),
    }
    lines = [
        "-- Local demo database account binding. Do not commit this file.",
        "-- Run opengauss_setup/sql/grant_roles_20260608.sql before this script.",
        "START TRANSACTION;",
        "",
        "DO $$",
        "BEGIN",
    ]
    for username, password in db_passwords.items():
        lines.extend(
            [
                f"    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{username}') THEN",
                f"        EXECUTE 'CREATE USER {username} WITH PASSWORD ''{password}''';",
                "    END IF;",
                "",
            ]
        )
    lines.extend(
        [
            "END;",
            "$$;",
            "",
            "GRANT db_app_role TO db_app_demo_user;",
            "GRANT db_student_role TO db_student_demo_user;",
            "GRANT db_teacher_role TO db_teacher_demo_user;",
            "GRANT db_admin_role TO db_admin_demo_user;",
            "",
            "COMMIT;",
            "",
        ]
    )
    LOCAL_DB_GRANTS.write_text("\n".join(lines), encoding="utf-8")


def write_local_account_seed(password_hashes: dict[str, str]) -> None:
    LOCAL_SQL_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "-- Local demo account sync. Do not commit this file.",
        "-- It updates an existing seed database without rebuilding it.",
        "START TRANSACTION;",
        "",
    ]
    for account in DEMO_ACCOUNTS:
        lines.append(
            "UPDATE user_account ua\n"
            f"SET username = '{account.username}',\n"
            f"    password_hash = '{password_hashes[account.username]}'\n"
            "WHERE ua.user_id = (\n"
            f"    SELECT user_id FROM {profile_table(account.role)}\n"
            f"    WHERE {profile_id_column(account.role)} = '{account.profile_id}'\n"
            ");\n"
        )
    lines.extend(["COMMIT;", ""])
    LOCAL_ACCOUNT_SEED.write_text("\n".join(lines), encoding="utf-8")


def profile_table(role: str) -> str:
    return {
        "admin": "admin_profile",
        "teacher": "teacher",
        "student": "student",
    }[role]


def profile_id_column(role: str) -> str:
    return {
        "admin": "admin_id",
        "teacher": "teacher_id",
        "student": "student_id",
    }[role]


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    passwords = {account.username: random_password() for account in DEMO_ACCOUNTS}
    password_hashes = {
        username: sha256_hex(password)
        for username, password in passwords.items()
    }

    update_init_sql(password_hashes)
    write_credentials(passwords, generated_at)
    write_example()
    write_local_account_seed(password_hashes)
    write_local_db_grants()

    print(f"Updated SQL seed: {INIT_SQL}")
    print(f"Wrote local credentials: {CREDENTIALS_MD}")
    print(f"Wrote public example: {EXAMPLE_MD}")
    print(f"Wrote local account sync SQL: {LOCAL_ACCOUNT_SEED}")
    print(f"Wrote local DB grant binding: {LOCAL_DB_GRANTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
