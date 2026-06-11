#!/usr/bin/env python3
"""Two-connection concurrency smoke test for course enrollment capacity.

The script creates a capacity-1 offering, starts two independent database
connections, and lets two students call select_course_tx() at nearly the same
time. Exactly one enrollment should commit; the other should fail after the
database-level row lock and capacity check run.
"""

from __future__ import annotations

import os
import sys
import threading
from dataclasses import dataclass

import psycopg2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import DB_CONFIG  # noqa: E402


PASSWORD_HASH = "0" * 64
TEST_USERNAMES = ("tst_conc_student_1", "tst_conc_student_2")
TEST_STUDENTS = ("TST_CONC_STU_1", "TST_CONC_STU_2")
TEST_SEMESTER = "TST-CONC-SEM"
TEST_COURSE = "TST_CONC_COURSE"
TEST_ROOM = "TST_CONC_R1"


@dataclass
class AttemptResult:
    student_id: str
    ok: bool
    message: str


def connect():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname=DB_CONFIG["database"],
    )


def cleanup(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM enrollment WHERE student_id IN (%s, %s)",
            TEST_STUDENTS,
        )
        cur.execute(
            """
            DELETE FROM course_schedule
            WHERE offering_id IN (
                SELECT offering_id FROM course_offering
                WHERE semester_id = %s OR course_id = %s
            )
            """,
            (TEST_SEMESTER, TEST_COURSE),
        )
        cur.execute(
            "DELETE FROM course_offering WHERE semester_id = %s OR course_id = %s",
            (TEST_SEMESTER, TEST_COURSE),
        )
        cur.execute("DELETE FROM classroom WHERE classroom_id = %s", (TEST_ROOM,))
        cur.execute("DELETE FROM student WHERE student_id IN (%s, %s)", TEST_STUDENTS)
        cur.execute("DELETE FROM user_account WHERE username IN (%s, %s)", TEST_USERNAMES)
        cur.execute("DELETE FROM semester WHERE semester_id = %s", (TEST_SEMESTER,))
        cur.execute("DELETE FROM course WHERE course_id = %s", (TEST_COURSE,))
    conn.commit()


def setup(conn) -> int:
    cleanup(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_account (username, password_hash, role)
            VALUES (%s, %s, 'student'), (%s, %s, 'student')
            RETURNING user_id
            """,
            (TEST_USERNAMES[0], PASSWORD_HASH, TEST_USERNAMES[1], PASSWORD_HASH),
        )
        user_ids = [row[0] for row in cur.fetchall()]

        cur.execute(
            """
            INSERT INTO student (student_id, user_id, student_name, major_id, status)
            VALUES (%s, %s, '并发测试学生一', 'CS01', 'enrolled'),
                   (%s, %s, '并发测试学生二', 'CS01', 'enrolled')
            """,
            (TEST_STUDENTS[0], user_ids[0], TEST_STUDENTS[1], user_ids[1]),
        )
        cur.execute(
            """
            INSERT INTO semester (
                semester_id, semester_name, start_date, end_date,
                selection_start, selection_end, status
            )
            VALUES (
                %s, '并发测试学期',
                CURRENT_DATE - 1, CURRENT_DATE + 30,
                CURRENT_TIMESTAMP - INTERVAL '1 day',
                CURRENT_TIMESTAMP + INTERVAL '1 day',
                'open'
            )
            """,
            (TEST_SEMESTER,),
        )
        cur.execute(
            """
            INSERT INTO course (course_id, course_name, course_type, credit, total_hours, dept_id)
            VALUES (%s, '并发测试课程', 'elective', 1.0, 16, 'CS')
            """,
            (TEST_COURSE,),
        )
        cur.execute(
            """
            INSERT INTO classroom (classroom_id, building, room_no, capacity)
            VALUES (%s, '并发测试楼', '101', 1)
            """,
            (TEST_ROOM,),
        )
        cur.execute(
            """
            INSERT INTO course_offering (
                course_id, semester_id, teacher_id, classroom_id, max_capacity, status
            )
            VALUES (%s, %s, 'T001', %s, 1, 'open')
            RETURNING offering_id
            """,
            (TEST_COURSE, TEST_SEMESTER, TEST_ROOM),
        )
        offering_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO course_schedule (offering_id, weekday, start_section, end_section)
            VALUES (%s, 7, 9, 10)
            """,
            (offering_id,),
        )
    conn.commit()
    return offering_id


def attempt_select(student_id: str, offering_id: int, barrier: threading.Barrier, out: list[AttemptResult]) -> None:
    conn = connect()
    try:
        barrier.wait()
        with conn.cursor() as cur:
            cur.execute("SELECT select_course_tx(%s, %s)", (student_id, offering_id))
        conn.commit()
        out.append(AttemptResult(student_id, True, "selected"))
    except Exception as exc:  # noqa: BLE001 - test reports database exception text
        conn.rollback()
        out.append(AttemptResult(student_id, False, str(exc).splitlines()[0]))
    finally:
        conn.close()


def main() -> int:
    conn = connect()
    offering_id = setup(conn)
    results: list[AttemptResult] = []
    barrier = threading.Barrier(2)
    threads = [
        threading.Thread(target=attempt_select, args=(student, offering_id, barrier, results))
        for student in TEST_STUDENTS
    ]

    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM enrollment
                WHERE offering_id = %s AND status = 'selected'
                """,
                (offering_id,),
            )
            selected_count = cur.fetchone()[0]

        success_count = sum(1 for result in results if result.ok)
        failed_count = sum(1 for result in results if not result.ok)

        for result in sorted(results, key=lambda item: item.student_id):
            print(f"{result.student_id}: {'SUCCESS' if result.ok else 'FAILED'} - {result.message}")
        print(f"success_count = {success_count}")
        print(f"failed_count = {failed_count}")
        print(f"selected_count_in_db = {selected_count}")

        return 0 if (success_count, failed_count, selected_count) == (1, 1, 1) else 1
    finally:
        cleanup(conn)
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
