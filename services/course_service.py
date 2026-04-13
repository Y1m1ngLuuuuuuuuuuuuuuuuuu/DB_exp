"""
services/course_service.py —— 课程 / 开课班次查询与维护
"""
from db.connection import query, query_one, execute


# ── 学期 ─────────────────────────────────────────────────────

def list_semesters() -> list[dict]:
    return query("SELECT * FROM semester ORDER BY start_date DESC")


def get_active_semester() -> dict | None:
    """返回 status='open' 的学期；若无则返回最近一个。"""
    row = query_one(
        "SELECT * FROM semester WHERE status='open' ORDER BY start_date DESC LIMIT 1"
    )
    return row or query_one(
        "SELECT * FROM semester ORDER BY start_date DESC LIMIT 1"
    )


def create_semester(data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            INSERT INTO semester
              (semester_id, semester_name, start_date, end_date,
               selection_start, selection_end, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                data["semester_id"], data["semester_name"],
                data["start_date"], data["end_date"],
                data["selection_start"], data["selection_end"],
                data.get("status", "planned"),
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def update_semester(semester_id: str, data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            UPDATE semester
            SET semester_name=%s, start_date=%s, end_date=%s,
                selection_start=%s, selection_end=%s, status=%s
            WHERE semester_id=%s
            """,
            (
                data["semester_name"], data["start_date"], data["end_date"],
                data["selection_start"], data["selection_end"],
                data.get("status", "planned"), semester_id,
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


# ── 课程基础信息 ─────────────────────────────────────────────

def list_courses(keyword: str = None, include_inactive: bool = False) -> list[dict]:
    sql = """
        SELECT c.course_id, c.course_name, c.course_type, c.credit,
               c.total_hours, c.status, c.description, d.dept_name
        FROM course c
        LEFT JOIN department d ON c.dept_id = d.dept_id
        WHERE 1=1
    """
    args: list = []
    if not include_inactive:
        sql += " AND c.status='active'"
    if keyword:
        sql += " AND (c.course_name LIKE %s OR c.course_id LIKE %s)"
        args += [f"%{keyword}%", f"%{keyword}%"]
    sql += " ORDER BY c.course_id"
    return query(sql, args or None)


def create_course(data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            INSERT INTO course
              (course_id, course_name, course_type, credit, total_hours, dept_id, description)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                data["course_id"], data["course_name"],
                data.get("course_type", "required"), data["credit"],
                data["total_hours"], data.get("dept_id"), data.get("description", ""),
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def update_course(course_id: str, data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            UPDATE course
            SET course_name=%s, course_type=%s, credit=%s, total_hours=%s,
                dept_id=%s, description=%s, status=%s
            WHERE course_id=%s
            """,
            (
                data["course_name"], data.get("course_type", "required"),
                data["credit"], data["total_hours"], data.get("dept_id"),
                data.get("description", ""), data.get("status", "active"), course_id,
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def delete_course(course_id: str) -> tuple[bool, str]:
    has_offering = query_one(
        "SELECT COUNT(*) n FROM course_offering WHERE course_id=%s", (course_id,)
    )
    if has_offering and has_offering["n"] > 0:
        return False, "该课程已有开课安排，请先删除相关班次"
    try:
        execute("DELETE FROM course_prerequisite WHERE course_id=%s OR prereq_course_id=%s",
                (course_id, course_id))
        execute("DELETE FROM course WHERE course_id=%s", (course_id,))
        return True, ""
    except Exception as exc:
        return False, str(exc)


# ── 开课班次 ─────────────────────────────────────────────────

def list_offerings(semester_id: str = None, teacher_id: str = None) -> list[dict]:
    sql = """
        SELECT co.offering_id, co.schedule_text, co.max_capacity,
               co.selected_count, co.status,
               c.course_id, c.course_name, c.credit,
               t.teacher_id, t.teacher_name,
               s.semester_name, s.semester_id,
               cl.building, cl.room_no
        FROM course_offering co
        JOIN course  c  ON co.course_id    = c.course_id
        JOIN teacher t  ON co.teacher_id   = t.teacher_id
        JOIN semester s ON co.semester_id  = s.semester_id
        LEFT JOIN classroom cl ON co.classroom_id = cl.classroom_id
        WHERE 1=1
    """
    args: list = []
    if semester_id:
        sql += " AND co.semester_id=%s"
        args.append(semester_id)
    if teacher_id:
        sql += " AND co.teacher_id=%s"
        args.append(teacher_id)
    sql += " ORDER BY co.offering_id"
    return query(sql, args or None)


def list_offerings_for_student(student_id: str, semester_id: str) -> list[dict]:
    """学生在指定学期可以选（未选或已退课）的班次。"""
    return query(
        """
        SELECT co.offering_id, co.schedule_text, co.max_capacity,
               co.selected_count,
               (co.max_capacity - co.selected_count) AS seats_left,
               c.course_id, c.course_name, c.credit, c.course_type,
               t.teacher_name,
               cl.building, cl.room_no
        FROM course_offering co
        JOIN course  c  ON co.course_id   = c.course_id
        JOIN teacher t  ON co.teacher_id  = t.teacher_id
        LEFT JOIN classroom cl ON co.classroom_id = cl.classroom_id
        WHERE co.semester_id = %s
          AND co.status = 'open'
          AND co.offering_id NOT IN (
              SELECT offering_id FROM enrollment
              WHERE student_id = %s AND status = 'selected'
          )
        ORDER BY c.course_id
        """,
        (semester_id, student_id),
    )


def list_classrooms() -> list[dict]:
    from db.connection import query as _query
    return _query("SELECT classroom_id, building, room_no, capacity FROM classroom ORDER BY building, room_no")


def create_offering(data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            INSERT INTO course_offering
              (course_id, semester_id, teacher_id, classroom_id,
               max_capacity, schedule_text, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                data["course_id"], data["semester_id"], data["teacher_id"],
                data.get("classroom_id"), data["max_capacity"],
                data.get("schedule_text", ""), data.get("status", "open"),
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def update_offering(offering_id: int, data: dict) -> tuple[bool, str]:
    try:
        execute(
            """
            UPDATE course_offering
            SET teacher_id=%s, classroom_id=%s, max_capacity=%s,
                schedule_text=%s, status=%s
            WHERE offering_id=%s
            """,
            (
                data["teacher_id"], data.get("classroom_id"),
                data["max_capacity"], data.get("schedule_text", ""),
                data.get("status", "open"), offering_id,
            ),
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def delete_offering(offering_id: int) -> tuple[bool, str]:
    enrolled = query_one(
        "SELECT COUNT(*) n FROM enrollment WHERE offering_id=%s",
        (offering_id,),
    )
    if enrolled and enrolled["n"] > 0:
        return False, "该班次已有选课或成绩记录，无法删除"
    try:
        execute("DELETE FROM enrollment WHERE offering_id=%s", (offering_id,))
        execute("DELETE FROM course_offering WHERE offering_id=%s", (offering_id,))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def list_enrolled_offerings(student_id: str, semester_id: str) -> list[dict]:
    """学生在指定学期的所有选课记录（含已退课）。"""
    return query(
        """
        SELECT e.enrollment_id, e.status AS enroll_status,
               e.final_score, e.gpa_point,
               co.offering_id, co.schedule_text,
               c.course_id, c.course_name, c.credit, c.course_type,
               t.teacher_name,
               cl.building, cl.room_no
        FROM enrollment e
        JOIN course_offering co ON e.offering_id  = co.offering_id
        JOIN course  c  ON co.course_id   = c.course_id
        JOIN teacher t  ON co.teacher_id  = t.teacher_id
        LEFT JOIN classroom cl ON co.classroom_id = cl.classroom_id
        WHERE co.semester_id = %s AND e.student_id = %s
        ORDER BY e.enrollment_id
        """,
        (semester_id, student_id),
    )
