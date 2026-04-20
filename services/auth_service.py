import hashlib
from db.connection import query_one, execute

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()

def login(username: str, password: str) -> dict | None:
    row = query_one(
        "SELECT user_id, username, role, status "
        "FROM user_account WHERE username=%s AND password_hash=%s",
        (username, hash_password(password)),
    )
    if row and row["status"] == "active":
        execute(
            "UPDATE user_account SET last_login_at=NOW() WHERE user_id=%s",
            (row["user_id"],),
        )
        return row
    return None

def get_student_id(user_id: int) -> str | None:
    row = query_one("SELECT student_id FROM student WHERE user_id=%s", (user_id,))
    return row["student_id"] if row else None

def get_teacher_id(user_id: int) -> str | None:
    row = query_one("SELECT teacher_id FROM teacher WHERE user_id=%s", (user_id,))
    return row["teacher_id"] if row else None
