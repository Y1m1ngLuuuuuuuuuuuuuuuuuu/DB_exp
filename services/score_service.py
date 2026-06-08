from db.connection import query, query_one, DBSession

def calc_gpa(score: float) -> float:
    if score >= 90: return 4.0
    if score >= 85: return 3.7
    if score >= 82: return 3.3
    if score >= 78: return 3.0
    if score >= 75: return 2.7
    if score >= 72: return 2.3
    if score >= 68: return 2.0
    if score >= 64: return 1.5
    if score >= 60: return 1.0
    return 0.0

def _gpa_point_sql(alias: str = "e") -> str:
    return f"""
           CASE
               WHEN {alias}.final_score IS NULL THEN NULL
               WHEN {alias}.final_score >= 90 THEN 4.0
               WHEN {alias}.final_score >= 85 THEN 3.7
               WHEN {alias}.final_score >= 82 THEN 3.3
               WHEN {alias}.final_score >= 78 THEN 3.0
               WHEN {alias}.final_score >= 75 THEN 2.7
               WHEN {alias}.final_score >= 72 THEN 2.3
               WHEN {alias}.final_score >= 68 THEN 2.0
               WHEN {alias}.final_score >= 64 THEN 1.5
               WHEN {alias}.final_score >= 60 THEN 1.0
               ELSE 0.0
           END"""

def get_enrollments_for_offering(offering_id: int) -> list[dict]:
    return query(
        f"""
        SELECT e.enrollment_id, e.student_id, e.status,
               e.final_score, {_gpa_point_sql("e")} AS gpa_point,
               s.student_name, s.class_name
        FROM enrollment e
        JOIN student s ON e.student_id = s.student_id
        WHERE e.offering_id = %s AND e.status != 'dropped'
        ORDER BY s.student_id
        """,
        (offering_id,),
    )

def can_manage_offering_score(
    offering_id: int,
    role: str,
    teacher_id: str | None = None,
) -> tuple[bool, str]:
    if role == "admin":
        return True, ""

    if role != "teacher" or not teacher_id:
        return False, "当前账号无权维护该班次成绩"

    row = query_one(
        "SELECT teacher_id FROM course_offering WHERE offering_id=%s",
        (offering_id,),
    )
    if not row:
        return False, "开课班次不存在"
    if row["teacher_id"] != teacher_id:
        return False, "教师只能维护自己负责的开课班次"
    return True, ""

def update_score(
    enrollment_id: int,
    new_score: float | None,
    changed_by_user_id: int,
    reason: str = "",
    role: str = "",
    teacher_id: str | None = None,
) -> tuple[bool, str]:
    try:
        with DBSession() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.final_score, e.status, e.offering_id, co.teacher_id
                    FROM enrollment e
                    JOIN course_offering co ON e.offering_id = co.offering_id
                    WHERE e.enrollment_id=%s
                    FOR UPDATE
                    """,
                    (enrollment_id,),
                )
                row = cur.fetchone()
                if not row:
                    return False, "记录不存在"

                if role == "admin":
                    allowed = True
                    msg = ""
                elif role == "teacher" and teacher_id and row["teacher_id"] == teacher_id:
                    allowed = True
                    msg = ""
                else:
                    allowed = False
                    msg = "当前账号无权维护该班次成绩"
                if not allowed:
                    return False, msg
                if row["status"] == "dropped":
                    return False, "退课记录不能录入成绩"
                if new_score is None:
                    return False, "成绩不能为空"
                if new_score < 0 or new_score > 100:
                    return False, "成绩必须在 0 到 100 之间"

                old_score = row["final_score"]
                if old_score is not None and float(old_score) == float(new_score):
                    return True, ""

                cur.execute(
                    "SELECT set_config('app.current_user_id', %s, true)",
                    (str(changed_by_user_id),),
                )
                cur.execute(
                    "SELECT set_config('app.score_change_reason', %s, true)",
                    (reason or "score updated",),
                )
                cur.execute(
                    "UPDATE enrollment SET final_score=%s, status='completed' "
                    "WHERE enrollment_id=%s",
                    (new_score, enrollment_id),
                )
        return True, ""
    except Exception as exc:
        msg = str(exc).splitlines()[0] if str(exc) else "数据库操作失败"
        if "requires app.current_user_id" in msg:
            msg = "成绩更新缺少当前操作者，无法写入审计日志"
        return False, msg

def get_student_transcript(student_id: str) -> list[dict]:
    return query(
        f"""
        SELECT c.course_name, c.credit, c.course_type,
               sem.semester_name, t.teacher_name,
               e.final_score, {_gpa_point_sql("e")} AS gpa_point
        FROM enrollment e
        JOIN course_offering co ON e.offering_id = co.offering_id
        JOIN course    c   ON co.course_id   = c.course_id
        JOIN semester  sem ON co.semester_id = sem.semester_id
        JOIN teacher   t   ON co.teacher_id  = t.teacher_id
        WHERE e.student_id = %s AND e.status = 'completed'
        ORDER BY sem.start_date DESC, c.course_name
        """,
        (student_id,),
    )

def get_score_distribution(offering_id: int) -> dict:
    rows = query(
        "SELECT final_score FROM enrollment "
        "WHERE offering_id=%s AND final_score IS NOT NULL AND status='completed'",
        (offering_id,),
    )
    if not rows:
        return {}
    buckets = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "不及格": 0}
    for r in rows:
        s = float(r["final_score"])
        if s >= 90:   buckets["90-100"] += 1
        elif s >= 80: buckets["80-89"]  += 1
        elif s >= 70: buckets["70-79"]  += 1
        elif s >= 60: buckets["60-69"]  += 1
        else:         buckets["不及格"]  += 1
    return buckets

def get_score_change_log(offering_id: int | None = None, limit: int = 100) -> list[dict]:
    sql = """
        SELECT scl.log_id, scl.changed_at, scl.old_score, scl.new_score, scl.reason,
               u.username AS changed_by,
               s.student_id, s.student_name,
               c.course_name, co.offering_id
        FROM score_change_log scl
        JOIN enrollment e    ON scl.enrollment_id       = e.enrollment_id
        JOIN student    s    ON e.student_id            = s.student_id
        JOIN course_offering co ON e.offering_id        = co.offering_id
        JOIN course     c    ON co.course_id            = c.course_id
        JOIN user_account u  ON scl.changed_by_user_id = u.user_id
        WHERE 1=1
    """
    args: list = []
    if offering_id is not None:
        sql += " AND co.offering_id=%s"
        args.append(offering_id)
    sql += " ORDER BY scl.changed_at DESC LIMIT %s"
    args.append(limit)
    return query(sql, args)
