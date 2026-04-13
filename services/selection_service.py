"""
services/selection_service.py —— 选课 / 退课业务逻辑
"""
from db.connection import query_one, execute


def _has_passed_prerequisites(student_id: str, offering_id: int) -> tuple[bool, str]:
    """Check whether the student has passed all prerequisites for the offering."""
    target = query_one(
        """
        SELECT co.course_id
        FROM course_offering co
        WHERE co.offering_id = %s
        """,
        (offering_id,),
    )
    if not target:
        return False, "开课班次不存在"

    prereqs = query_one(
        """
        SELECT COUNT(*) AS total
        FROM course_prerequisite
        WHERE course_id = %s
        """,
        (target["course_id"],),
    )
    if not prereqs or prereqs["total"] == 0:
        return True, ""

    missing = query_one(
        """
        SELECT COUNT(*) AS missing_count
        FROM course_prerequisite cp
        WHERE cp.course_id = %s
          AND NOT EXISTS (
              SELECT 1
              FROM enrollment e
              JOIN course_offering co2 ON e.offering_id = co2.offering_id
              WHERE e.student_id = %s
                AND co2.course_id = cp.prereq_course_id
                AND e.status = 'completed'
                AND e.final_score >= 60
          )
        """,
        (target["course_id"], student_id),
    )
    if missing and missing["missing_count"] > 0:
        return False, "未满足先修课程要求"
    return True, ""


def enroll(student_id: str, offering_id: int) -> tuple[bool, str]:
    """
    选课。
    - 重复选课（selected 状态）→ 提示已选
    - 曾退课（dropped 状态）  → 恢复为 selected
    - 新选课                  → INSERT
    """
    existing = query_one(
        "SELECT enrollment_id, status FROM enrollment "
        "WHERE student_id=%s AND offering_id=%s",
        (student_id, offering_id),
    )
    if existing:
        if existing["status"] == "selected":
            return False, "你已选过这门课"
        if existing["status"] == "completed":
            return False, "该课程已结课，不能重复在同一班次中选课"
        if existing["status"] == "dropped":
            # 检查容量后恢复
            offering = query_one(
                """
                SELECT co.max_capacity, co.selected_count, co.status,
                       s.selection_start, s.selection_end, s.status AS semester_status
                FROM course_offering co
                JOIN semester s ON co.semester_id = s.semester_id
                WHERE co.offering_id=%s
                """,
                (offering_id,),
            )
            if not offering:
                return False, "开课班次不存在"
            if offering["semester_status"] != "open":
                return False, "当前学期未开放选课"
            if offering["selection_start"] and offering["selection_end"]:
                window_ok = query_one(
                    "SELECT NOW() BETWEEN %s AND %s AS in_window",
                    (offering["selection_start"], offering["selection_end"]),
                )
                if not window_ok or not window_ok["in_window"]:
                    return False, "当前不在选课开放时间内"
            if offering["selected_count"] >= offering["max_capacity"]:
                return False, "名额已满，无法恢复选课"
            ok, msg = _has_passed_prerequisites(student_id, offering_id)
            if not ok:
                return False, msg
            execute(
                "UPDATE enrollment SET status='selected', select_time=NOW() "
                "WHERE enrollment_id=%s",
                (existing["enrollment_id"],),
            )
            return True, ""

    # 检查开课状态与容量
    offering = query_one(
        """
        SELECT co.max_capacity, co.selected_count, co.status,
               s.selection_start, s.selection_end, s.status AS semester_status
        FROM course_offering co
        JOIN semester s ON co.semester_id = s.semester_id
        WHERE co.offering_id=%s
        """,
        (offering_id,),
    )
    if not offering:
        return False, "开课班次不存在"
    if offering["semester_status"] != "open":
        return False, "当前学期未开放选课"
    if offering["status"] != "open":
        return False, "该课程班次已关闭，不允许选课"
    if offering["selection_start"] and offering["selection_end"]:
        window_ok = query_one(
            "SELECT NOW() BETWEEN %s AND %s AS in_window",
            (offering["selection_start"], offering["selection_end"]),
        )
        if not window_ok or not window_ok["in_window"]:
            return False, "当前不在选课开放时间内"
    if offering["selected_count"] >= offering["max_capacity"]:
        return False, "名额已满"
    ok, msg = _has_passed_prerequisites(student_id, offering_id)
    if not ok:
        return False, msg

    try:
        execute(
            "INSERT INTO enrollment (student_id, offering_id, status, select_time) "
            "VALUES (%s,%s,'selected',NOW())",
            (student_id, offering_id),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def drop(enrollment_id: int, student_id: str) -> tuple[bool, str]:
    """退课：将 enrollment.status 改为 dropped。"""
    row = query_one(
        """
        SELECT e.status, e.student_id, e.final_score,
               s.selection_start, s.selection_end, s.status AS semester_status
        FROM enrollment e
        JOIN course_offering co ON e.offering_id = co.offering_id
        JOIN semester s ON co.semester_id = s.semester_id
        WHERE e.enrollment_id=%s
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
        window_ok = query_one(
            "SELECT NOW() BETWEEN %s AND %s AS in_window",
            (row["selection_start"], row["selection_end"]),
        )
        if not window_ok or not window_ok["in_window"]:
            return False, "当前不在选退课开放时间内"
    try:
        execute(
            "UPDATE enrollment SET status='dropped' WHERE enrollment_id=%s",
            (enrollment_id,),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)
