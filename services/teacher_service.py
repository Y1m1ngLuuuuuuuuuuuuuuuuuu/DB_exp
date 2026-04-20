from db.connection import query, query_one, execute, DBSession

def get_teacher_info(teacher_id: str) -> dict | None:
    return query_one(
        """
        SELECT t.teacher_id, t.teacher_name, t.gender, t.title,
               t.phone, t.email, t.status, d.dept_name, u.username
        FROM teacher t
        LEFT JOIN department d ON t.dept_id = d.dept_id
        LEFT JOIN user_account u ON t.user_id = u.user_id
        WHERE t.teacher_id = %s
        """,
        (teacher_id,),
    )

def list_teachers(keyword: str = None) -> list[dict]:
    sql = """
        SELECT t.teacher_id, t.teacher_name, t.gender, t.title,
               t.email, t.status, d.dept_name, d.dept_id, u.username
        FROM teacher t
        LEFT JOIN department d ON t.dept_id = d.dept_id
        LEFT JOIN user_account u ON t.user_id = u.user_id
        WHERE 1=1
    """
    args: list = []
    if keyword:
        sql += " AND (t.teacher_name LIKE %s OR t.teacher_id LIKE %s)"
        args += [f"%{keyword}%", f"%{keyword}%"]
    sql += " ORDER BY t.teacher_id"
    return query(sql, args or None)

def create_teacher(data: dict) -> tuple[bool, str]:
    from services.auth_service import hash_password
    try:
        with DBSession() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_account (username, password_hash, role) VALUES (%s,%s,'teacher')",
                    (data["username"], hash_password(data.get("password", "123456"))),
                )
                user_id = cur.lastrowid
                cur.execute(
                    """
                    INSERT INTO teacher
                      (teacher_id, user_id, teacher_name, gender, dept_id, title, phone, email)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        data["teacher_id"], user_id, data["teacher_name"],
                        data.get("gender"), data.get("dept_id"), data.get("title"),
                        data.get("phone"), data.get("email"),
                    ),
                )
        return True, ""
    except Exception as exc:
        return False, str(exc)

def update_teacher(teacher_id: str, data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            UPDATE teacher
            SET teacher_name=%s, gender=%s, dept_id=%s,
                title=%s, phone=%s, email=%s, status=%s
            WHERE teacher_id=%s
            """,
            (
                data["teacher_name"], data.get("gender"), data.get("dept_id"),
                data.get("title"), data.get("phone"), data.get("email"),
                data.get("status", "active"), teacher_id,
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)

def delete_teacher(teacher_id: str) -> tuple[bool, str]:

    cnt = query_one(
        "SELECT COUNT(*) AS n FROM course_offering WHERE teacher_id=%s", (teacher_id,)
    )
    if cnt and cnt["n"] > 0:
        return False, "该教师存在开课记录，无法直接删除"
    row = query_one("SELECT user_id FROM teacher WHERE teacher_id=%s", (teacher_id,))
    if not row:
        return False, "教师不存在"
    try:
        execute("DELETE FROM teacher WHERE teacher_id=%s", (teacher_id,))
        execute("DELETE FROM user_account WHERE user_id=%s", (row["user_id"],))
        return True, ""
    except Exception as exc:
        return False, str(exc)
