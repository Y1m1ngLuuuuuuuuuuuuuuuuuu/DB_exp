from db.connection import query, query_one, DBSession

def get_enrollments_for_offering(offering_id: int) -> list[dict]:
    return query(
        """
        SELECT e.enrollment_id, e.student_id, e.status,
               e.final_score, vgd.gpa_point,
               s.student_name, s.class_name
        FROM enrollment e
        JOIN student s ON e.student_id = s.student_id
        LEFT JOIN v_enrollment_grade_detail vgd
          ON e.enrollment_id = vgd.enrollment_id
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
        """
        SELECT c.course_name, c.credit, c.course_type,
               sem.semester_name, t.teacher_name,
               vgd.final_score, vgd.grade_label, vgd.gpa_point,
               vgd.policy_name, vgd.version_no
        FROM v_enrollment_grade_detail vgd
        JOIN course_offering co ON vgd.offering_id = co.offering_id
        JOIN course    c   ON vgd.course_id    = c.course_id
        JOIN semester  sem ON vgd.semester_id  = sem.semester_id
        JOIN teacher   t   ON co.teacher_id    = t.teacher_id
        WHERE vgd.student_id = %s
          AND vgd.enrollment_status = 'completed'
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

def get_score_change_log(
    offering_id: int | None = None,
    semester_id: str | None = None,
    teacher_id: str | None = None,
    course_keyword: str | None = None,
    student_keyword: str | None = None,
    date_from=None,
    date_to=None,
    limit: int = 100,
) -> list[dict]:
    sql = """
        SELECT scl.log_id, scl.changed_at, scl.old_score, scl.new_score, scl.reason,
               u.username AS changed_by,
               s.student_id, s.student_name,
               c.course_id, c.course_name, co.offering_id,
               t.teacher_id, t.teacher_name,
               sem.semester_id, sem.semester_name
        FROM score_change_log scl
        JOIN enrollment e    ON scl.enrollment_id       = e.enrollment_id
        JOIN student    s    ON e.student_id            = s.student_id
        JOIN course_offering co ON e.offering_id        = co.offering_id
        JOIN course     c    ON co.course_id            = c.course_id
        JOIN teacher    t    ON co.teacher_id           = t.teacher_id
        JOIN semester   sem  ON co.semester_id          = sem.semester_id
        JOIN user_account u  ON scl.changed_by_user_id = u.user_id
        WHERE 1=1
    """
    args: list = []
    if offering_id is not None:
        sql += " AND co.offering_id=%s"
        args.append(offering_id)
    if semester_id:
        sql += " AND sem.semester_id=%s"
        args.append(semester_id)
    if teacher_id:
        sql += " AND t.teacher_id=%s"
        args.append(teacher_id)
    if course_keyword:
        sql += " AND (c.course_name LIKE %s OR c.course_id LIKE %s)"
        args.extend([f"%{course_keyword}%", f"%{course_keyword}%"])
    if student_keyword:
        sql += " AND (s.student_name LIKE %s OR s.student_id LIKE %s)"
        args.extend([f"%{student_keyword}%", f"%{student_keyword}%"])
    if date_from is not None:
        sql += " AND scl.changed_at >= %s"
        args.append(date_from)
    if date_to is not None:
        sql += " AND scl.changed_at < (%s::date + INTERVAL '1 day')"
        args.append(date_to)
    sql += " ORDER BY scl.changed_at DESC LIMIT %s"
    args.append(limit)
    return query(sql, args)
