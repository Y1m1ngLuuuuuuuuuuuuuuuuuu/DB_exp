from db.connection import DBSession


def _friendly_db_error(exc: Exception) -> str:
    msg = str(exc)
    marker = "Missing prerequisites:"
    if marker in msg:
        missing = msg.split(marker, 1)[1].splitlines()[0].strip().rstrip(".")
        return f"未满足先修课程要求：{missing}"

    checks = [
        ("already selected", "你已选过这门课"),
        ("already selected offering", "你已选过这门课"),
        ("Completed enrollment", "该课程已结课，不能重复选择或退课"),
        ("not open for selection", "当前学期未开放选课"),
        ("outside course selection window", "当前不在选课开放时间内"),
        ("outside drop window", "当前不在选退课开放时间内"),
        ("Course offering", "该课程班次不可选或已满"),
        ("another offering for course", "同一学期同一门课程只能选择一个教学班"),
        ("is full", "名额已满"),
        ("timetable conflict", "与已选课程时间冲突"),
        ("has not passed all prerequisites", "未满足先修课程要求"),
        ("cannot be dropped", "该选课记录不允许退课"),
        ("duplicate key value", "你已选过这门课"),
    ]
    for needle, friendly in checks:
        if needle in msg:
            return friendly
    return msg.splitlines()[0] if msg else "数据库操作失败"


def _fetch_one(cur, sql: str, args=None) -> dict | None:
    cur.execute(sql, args)
    row = cur.fetchone()
    return dict(row) if row else None


def enroll(student_id: str, offering_id: int) -> tuple[bool, str]:
    try:
        with DBSession() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT select_course_tx(%s,%s) AS enrollment_id",
                    (student_id, offering_id),
                )
        return True, ""
    except Exception as exc:
        return False, _friendly_db_error(exc)

def drop(enrollment_id: int, student_id: str) -> tuple[bool, str]:
    try:
        with DBSession() as conn:
            with conn.cursor() as cur:
                row = _fetch_one(
                    cur,
                    """
                    SELECT e.status, e.student_id, e.final_score,
                           s.selection_start, s.selection_end,
                           s.status AS semester_status
                    FROM enrollment e
                    JOIN course_offering co ON e.offering_id = co.offering_id
                    JOIN semester s ON co.semester_id = s.semester_id
                    WHERE e.enrollment_id=%s
                    FOR UPDATE
                    """,
                    (enrollment_id,),
                )
                if not row:
                    return False, "选课记录不存在"
                if row["student_id"] != student_id:
                    return False, "只能退掉自己的课程"
                if row["status"] != "selected":
                    return False, "只能退掉「已选」状态的课程"
                if row["final_score"] is not None:
                    return False, "已录入成绩的课程不允许退课"
                if row["semester_status"] != "open":
                    return False, "当前学期未开放退课"
                if row["selection_start"] and row["selection_end"]:
                    window_ok = _fetch_one(
                        cur,
                        "SELECT CURRENT_TIMESTAMP BETWEEN %s AND %s AS in_window",
                        (row["selection_start"], row["selection_end"]),
                    )
                    if not window_ok or not window_ok["in_window"]:
                        return False, "当前不在选退课开放时间内"
                cur.execute(
                    "UPDATE enrollment SET status='dropped' WHERE enrollment_id=%s",
                    (enrollment_id,),
                )
        return True, ""
    except Exception as exc:
        return False, _friendly_db_error(exc)
