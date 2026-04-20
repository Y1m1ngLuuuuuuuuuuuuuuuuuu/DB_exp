from db.connection import query, query_one, execute, DBSession

def get_student_info(student_id: str) -> dict | None:
    return query_one(
        """
        SELECT s.student_id, s.student_name, s.gender, s.enroll_year,
               s.class_name, s.phone, s.email, s.status,
               m.major_name, d.dept_name
        FROM student s
        LEFT JOIN major m ON s.major_id = m.major_id
        LEFT JOIN department d ON m.dept_id = d.dept_id
        WHERE s.student_id = %s
        """,
        (student_id,),
    )

def list_students(keyword: str = None) -> list[dict]:
    sql = """
        SELECT s.student_id, s.student_name, s.gender, s.enroll_year,
               s.class_name, s.email, s.status,
               m.major_name, d.dept_name, u.username
        FROM student s
        LEFT JOIN major m ON s.major_id = m.major_id
        LEFT JOIN department d ON m.dept_id = d.dept_id
        LEFT JOIN user_account u ON s.user_id = u.user_id
        WHERE 1=1
    """
    args: list = []
    if keyword:
        sql += " AND (s.student_name LIKE %s OR s.student_id LIKE %s)"
        args += [f"%{keyword}%", f"%{keyword}%"]
    sql += " ORDER BY s.student_id"
    return query(sql, args or None)

def create_student(data: dict) -> tuple[bool, str]:
    from services.auth_service import hash_password
    try:
        with DBSession() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_account (username, password_hash, role) VALUES (%s,%s,'student')",
                    (data["username"], hash_password(data.get("password", "123456"))),
                )
                user_id = cur.lastrowid
                cur.execute(
                    """
                    INSERT INTO student
                      (student_id, user_id, student_name, gender, enroll_year,
                       major_id, class_name, phone, email)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        data["student_id"], user_id, data["student_name"],
                        data.get("gender"), data.get("enroll_year"), data.get("major_id"),
                        data.get("class_name"), data.get("phone"), data.get("email"),
                    ),
                )
        return True, ""
    except Exception as exc:
        return False, str(exc)

def update_student(student_id: str, data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            UPDATE student
            SET student_name=%s, gender=%s, class_name=%s,
                phone=%s, email=%s, status=%s
            WHERE student_id=%s
            """,
            (
                data["student_name"], data.get("gender"), data.get("class_name"),
                data.get("phone"), data.get("email"),
                data.get("status", "enrolled"), student_id,
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)

def delete_student(student_id: str) -> tuple[bool, str]:
    row = query_one("SELECT user_id FROM student WHERE student_id=%s", (student_id,))
    if not row:
        return False, "学生不存在"
    try:
        execute("DELETE FROM student WHERE student_id=%s", (student_id,))
        execute("DELETE FROM user_account WHERE user_id=%s", (row["user_id"],))
        return True, ""
    except Exception as exc:
        return False, str(exc)
