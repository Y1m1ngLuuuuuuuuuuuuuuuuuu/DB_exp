import hashlib
import secrets
from datetime import datetime, timedelta

from config import SESSION_COOKIE_MAX_AGE_DAYS
from db.connection import query_one, execute

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()

def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def login(username: str, password: str) -> dict | None:
    row = query_one(
        "SELECT user_id, username, role, status "
        "FROM user_account WHERE username=%s AND password_hash=%s",
        (username, hash_password(password)),
    )
    if row and row["status"] == "active":
        execute(
            "UPDATE user_account SET last_login_at=CURRENT_TIMESTAMP WHERE user_id=%s",
            (row["user_id"],),
        )
        return row
    return None

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hash_session_token(token)
    expires_at = datetime.now() + timedelta(days=SESSION_COOKIE_MAX_AGE_DAYS)
    execute(
        """
        INSERT INTO user_session (user_id, token_hash, expires_at)
        VALUES (%s,%s,%s)
        """,
        (user_id, token_hash, expires_at),
    )
    return token

def get_user_by_session_token(token: str | None) -> dict | None:
    if not token:
        return None

    token_hash = hash_session_token(token)
    row = query_one(
        """
        SELECT u.user_id, u.username, u.role, u.status
        FROM user_session us
        JOIN user_account u ON us.user_id = u.user_id
        WHERE us.token_hash = %s
          AND us.revoked_at IS NULL
          AND us.expires_at > CURRENT_TIMESTAMP
        """,
        (token_hash,),
    )
    if not row or row["status"] != "active":
        return None

    execute(
        """
        UPDATE user_session
        SET last_seen_at = CURRENT_TIMESTAMP
        WHERE token_hash = %s
        """,
        (token_hash,),
    )
    return row

def revoke_session(token: str | None) -> None:
    if not token:
        return
    execute(
        """
        UPDATE user_session
        SET revoked_at = CURRENT_TIMESTAMP
        WHERE token_hash = %s AND revoked_at IS NULL
        """,
        (hash_session_token(token),),
    )

def get_student_id(user_id: int) -> str | None:
    row = query_one("SELECT student_id FROM student WHERE user_id=%s", (user_id,))
    return row["student_id"] if row else None

def get_teacher_id(user_id: int) -> str | None:
    row = query_one("SELECT teacher_id FROM teacher WHERE user_id=%s", (user_id,))
    return row["teacher_id"] if row else None
