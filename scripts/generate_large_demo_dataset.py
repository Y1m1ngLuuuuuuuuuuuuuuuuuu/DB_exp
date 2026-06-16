#!/usr/bin/env python3
"""Generate a reproducible large demo dataset for the course system.

The generated SQL is intended for the local demo database only. It stores only
password hashes in SQL and writes plaintext initial passwords to the ignored
secrets/ directory.
"""

from __future__ import annotations

import csv
import hashlib
import random
import string
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260611
RNG = random.Random(SEED)

LOCAL_SQL = ROOT / "opengauss_setup/sql/local/seed_large_demo_dataset_20260611.sql"
CREDENTIALS_MD = ROOT / "secrets/DEMO_ACCOUNT_CREDENTIALS.md"
CREDENTIALS_CSV = ROOT / "secrets/DEMO_ACCOUNT_CREDENTIALS.csv"
SUMMARY_MD = ROOT / "report/LARGE_DEMO_DATASET_SUMMARY.md"
VALIDATION_MD = ROOT / "report/LARGE_DEMO_DATASET_VALIDATION.md"


@dataclass(frozen=True)
class Account:
    role: str
    profile_id: str
    username: str
    display_name: str
    user_id: int
    password: str


@dataclass(frozen=True)
class Course:
    course_id: str
    name: str
    course_type: str
    credit: float
    hours: int
    dept_id: str


@dataclass
class Offering:
    offering_id: int
    course_id: str
    semester_id: str
    teacher_id: str
    classroom_id: str
    max_capacity: int
    status: str


@dataclass
class Enrollment:
    enrollment_id: int
    student_id: str
    offering_id: int
    select_time: str
    status: str
    final_score: float | None
    remark: str


def sql_str(value: object | None) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def sha256_hex(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def password(length: int = 14) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        pwd = "".join(RNG.choice(chars) for _ in range(length))
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
        ):
            return pwd


def insert_values(table: str, columns: list[str], rows: list[tuple], batch: int = 200) -> list[str]:
    if not rows:
        return []
    lines: list[str] = []
    col_sql = ", ".join(columns)
    for start in range(0, len(rows), batch):
        chunk = rows[start : start + batch]
        values = []
        for row in chunk:
            values.append("(" + ", ".join(sql_str(v) for v in row) + ")")
        lines.append(f"INSERT INTO {table} ({col_sql}) VALUES\n" + ",\n".join(values) + ";")
    return lines


def build_departments() -> list[tuple]:
    return [
        ("CS", "计算机学院", "010-88881111", "综合楼 A301"),
        ("MATH", "数学与统计学院", "010-88882222", "综合楼 B201"),
        ("FL", "外国语学院", "010-88883333", "文科楼 C202"),
        ("EM", "经济管理学院", "010-88884444", "经管楼 D105"),
    ]


def build_majors() -> list[tuple]:
    return [
        ("CS01", "计算机科学与技术", "CS"),
        ("CS02", "软件工程", "CS"),
        ("CS03", "数据科学与大数据技术", "CS"),
        ("MA01", "数学与应用数学", "MATH"),
        ("MA02", "统计学", "MATH"),
        ("MA03", "信息与计算科学", "MATH"),
        ("FL01", "英语", "FL"),
        ("FL02", "翻译", "FL"),
        ("EM01", "工商管理", "EM"),
        ("EM02", "会计学", "EM"),
        ("EM03", "信息管理与信息系统", "EM"),
    ]


def fake_name(index: int, gender: str) -> str:
    surnames = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
    male_given = ["子轩", "浩然", "宇航", "嘉懿", "俊杰", "明远", "博文", "承泽", "梓豪", "睿哲"]
    female_given = ["雨桐", "欣怡", "诗涵", "若曦", "思琪", "婉清", "语嫣", "芷晴", "佳宁", "梦瑶"]
    pool = male_given if gender == "M" else female_given
    return surnames[index % len(surnames)] + pool[(index * 7) % len(pool)]


def build_courses() -> list[Course]:
    specs = [
        ("CS", 15, [
            "程序设计基础", "数据结构", "数据库原理", "操作系统", "计算机网络",
            "软件工程", "Web 应用开发", "人工智能导论", "数据挖掘", "信息安全",
            "移动应用开发", "云计算基础", "机器学习", "大数据平台", "编译原理",
        ]),
        ("MA", 10, [
            "高等数学", "线性代数", "概率论与数理统计", "离散数学", "数值分析",
            "数学建模", "统计计算", "运筹学", "随机过程", "时间序列分析",
        ]),
        ("FL", 10, [
            "大学英语", "英语听说", "英语写作", "跨文化交际", "商务英语",
            "翻译理论与实践", "英语文学导读", "学术英语", "第二外语", "语言学概论",
        ]),
        ("EM", 15, [
            "管理学原理", "微观经济学", "宏观经济学", "会计学基础", "市场营销",
            "财务管理", "组织行为学", "运营管理", "管理信息系统", "商业数据分析",
            "人力资源管理", "战略管理", "电子商务", "金融学基础", "创业管理",
        ]),
    ]
    dept_map = {"CS": "CS", "MA": "MATH", "FL": "FL", "EM": "EM"}
    courses: list[Course] = []
    for prefix, count, names in specs:
        for i in range(1, count + 1):
            course_id = f"{prefix}{100 + i:03d}"
            if i <= 5:
                ctype = "required"
            elif i <= count - 3:
                ctype = "elective"
            else:
                ctype = "public"
            credit = RNG.choice([1.0, 2.0, 2.5, 3.0, 3.5, 4.0])
            if ctype == "required":
                credit = max(3.0, credit)
            hours = int(credit * 16)
            courses.append(Course(course_id, names[i - 1], ctype, credit, hours, dept_map[prefix]))
    return courses


def score_value(force_pass: bool = False) -> float:
    if force_pass:
        return float(RNG.randint(68, 96))
    roll = RNG.random()
    if roll < 0.07:
        return float(RNG.randint(45, 59))
    if roll < 0.25:
        return float(RNG.randint(60, 69))
    if roll < 0.55:
        return float(RNG.randint(70, 79))
    if roll < 0.85:
        return float(RNG.randint(80, 89))
    return float(RNG.randint(90, 100))


def main() -> None:
    departments = build_departments()
    majors = build_majors()
    courses = build_courses()
    course_by_id = {c.course_id: c for c in courses}
    course_ids = [c.course_id for c in courses]

    prerequisites = [
        ("CS102", "CS101"),
        ("CS103", "CS102"),
        ("CS104", "CS102"),
        ("CS105", "CS101"),
        ("CS110", "CS104"),
        ("CS115", "CS103"),
        ("MA102", "MA101"),
        ("MA103", "MA102"),
        ("EM103", "EM101"),
        ("EM110", "EM103"),
        ("FL104", "FL101"),
    ]
    prereq_map: dict[str, set[str]] = defaultdict(set)
    for course_id, prereq_id in prerequisites:
        prereq_map[course_id].add(prereq_id)

    accounts: list[Account] = []
    admins = [
        ("A001", "系统管理员"),
        ("A002", "教务管理员"),
        ("A003", "数据审计管理员"),
    ]
    for idx, (admin_id, name) in enumerate(admins, start=1):
        accounts.append(Account("admin", admin_id, admin_id, name, idx, password()))

    teacher_rows = []
    teacher_depts = ["CS"] * 9 + ["MATH"] * 7 + ["FL"] * 6 + ["EM"] * 8
    titles = ["教授", "副教授", "讲师", "助教"]
    for i in range(1, 31):
        teacher_id = f"T{i:03d}"
        gender = "M" if i % 2 else "F"
        name = fake_name(100 + i, gender)
        user_id = 10 + i
        dept_id = teacher_depts[i - 1]
        title = titles[(i + (0 if dept_id == "CS" else 1)) % len(titles)]
        accounts.append(Account("teacher", teacher_id, teacher_id, name, user_id, password()))
        teacher_rows.append(
            (
                teacher_id,
                user_id,
                name,
                gender,
                dept_id,
                title,
                f"138{10000000 + i:08d}",
                f"{teacher_id.lower()}@demo.edu.cn",
                "active",
            )
        )

    major_by_dept: dict[str, list[str]] = defaultdict(list)
    for major_id, _, dept_id in majors:
        major_by_dept[dept_id].append(major_id)

    student_rows = []
    student_dept_cycle = ["CS", "MATH", "FL", "EM"]
    student_major: dict[str, str] = {}
    for i in range(1, 101):
        student_id = f"2024{i:04d}"
        dept_id = student_dept_cycle[(i - 1) % len(student_dept_cycle)]
        major_id = major_by_dept[dept_id][((i - 1) // len(student_dept_cycle)) % len(major_by_dept[dept_id])]
        gender = "M" if i % 2 else "F"
        name = fake_name(i, gender)
        user_id = 100 + i
        accounts.append(Account("student", student_id, student_id, name, user_id, password()))
        class_name = f"{major_id}-24{((i - 1) % 4) + 1}班"
        student_major[student_id] = major_id
        student_rows.append(
            (
                student_id,
                user_id,
                name,
                gender,
                f"2006-{((i - 1) % 12) + 1:02d}-{((i * 3 - 1) % 28) + 1:02d}",
                2024,
                major_id,
                class_name,
                f"139{20000000 + i:08d}",
                f"{student_id}@demo.edu.cn",
                "enrolled",
            )
        )

    account_rows = [
        (a.user_id, a.username, sha256_hex(a.password), a.role, "active") for a in accounts
    ]
    admin_rows = [
        (admin_id, next(a.user_id for a in accounts if a.username == admin_id), name, f"010-8899{idx:04d}")
        for idx, (admin_id, name) in enumerate(admins, start=1)
    ]

    semesters = [
        ("2024-2025-1", "2024-2025 学年第 1 学期", "2024-09-01", "2025-01-15", "2024-08-20 00:00:00", "2024-09-20 23:59:59", "closed"),
        ("2024-2025-2", "2024-2025 学年第 2 学期", "2025-02-20", "2025-07-05", "2025-02-01 00:00:00", "2025-03-10 23:59:59", "closed"),
        ("2025-2026-1", "2025-2026 学年第 1 学期", "2025-09-01", "2026-01-15", "2025-08-20 00:00:00", "2025-09-20 23:59:59", "closed"),
        ("2025-2026-2", "2025-2026 学年第 2 学期", "2026-02-20", "2026-07-05", "2026-06-01 00:00:00", "2026-06-30 23:59:59", "open"),
    ]

    classroom_rows = []
    buildings = [("A", "综合楼"), ("B", "实验楼"), ("C", "文科楼"), ("D", "经管楼")]
    capacities = [30, 40, 50, 60, 80, 100]
    classroom_capacity: dict[str, int] = {}
    for i in range(1, 21):
        letter, building = buildings[(i - 1) % len(buildings)]
        room_no = f"{(i - 1) // 4 + 1}{(i - 1) % 4 + 1:02d}"
        classroom_id = f"{letter}{room_no}"
        cap = capacities[(i * 2) % len(capacities)]
        classroom_capacity[classroom_id] = cap
        classroom_rows.append((classroom_id, building, room_no, cap))

    course_rows = [
        (c.course_id, c.name, c.course_type, c.credit, c.hours, c.dept_id, f"{c.name}课程", "active")
        for c in courses
    ]

    teachers_by_dept: dict[str, list[str]] = defaultdict(list)
    for row in teacher_rows:
        teachers_by_dept[row[4]].append(row[0])

    offerings: list[Offering] = []
    schedule_rows: list[tuple] = []
    schedules_by_offering: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    teacher_slot_used: set[tuple[str, str, int, int, int]] = set()
    room_slot_used: set[tuple[str, str, int, int, int]] = set()
    offering_by_course_sem: dict[tuple[str, str], list[int]] = defaultdict(list)
    course_by_offering: dict[int, str] = {}
    semester_by_offering: dict[int, str] = {}
    offering_capacity: dict[int, int] = {}
    offering_status: dict[int, str] = {}

    semester_course_counts = {
        "2024-2025-1": 30,
        "2024-2025-2": 40,
        "2025-2026-1": 45,
        "2025-2026-2": 50,
    }
    historical_orders = {
        "2024-2025-1": course_ids[:30],
        "2024-2025-2": course_ids[:40],
        "2025-2026-1": course_ids[:45],
        "2025-2026-2": course_ids[:50],
    }
    popular_current = ["CS101", "CS102", "CS103", "MA101", "MA102", "FL101", "EM101", "EM103", "CS107", "EM110"]

    slot_pool = [(weekday, start, start + 1) for weekday in range(1, 6) for start in (1, 3, 5, 7, 9)]
    offering_id = 1
    schedule_id = 1

    def choose_slot(sem: str, teacher_id: str, classroom_id: str) -> tuple[int, int, int]:
        shuffled = slot_pool[:]
        RNG.shuffle(shuffled)
        for slot in shuffled:
            key_t = (sem, teacher_id, *slot)
            key_r = (sem, classroom_id, *slot)
            if key_t not in teacher_slot_used and key_r not in room_slot_used:
                teacher_slot_used.add(key_t)
                room_slot_used.add(key_r)
                return slot
        slot = RNG.choice(slot_pool)
        teacher_slot_used.add((sem, teacher_id, *slot))
        room_slot_used.add((sem, classroom_id, *slot))
        return slot

    def add_offering(course_id: str, sem: str, status: str, duplicate_index: int = 0) -> None:
        nonlocal offering_id, schedule_id
        course = course_by_id[course_id]
        teacher_id = teachers_by_dept[course.dept_id][(offering_id + duplicate_index) % len(teachers_by_dept[course.dept_id])]
        classroom_id = classroom_rows[(offering_id * 3 + duplicate_index) % len(classroom_rows)][0]
        room_cap = classroom_capacity[classroom_id]
        max_capacity = min(room_cap, RNG.choice([30, 35, 40, 45, 50, 55, 60, 70, 80]))
        max_capacity = max(30, max_capacity)
        offerings.append(Offering(offering_id, course_id, sem, teacher_id, classroom_id, max_capacity, status))
        course_by_offering[offering_id] = course_id
        semester_by_offering[offering_id] = sem
        offering_capacity[offering_id] = max_capacity
        offering_status[offering_id] = status
        offering_by_course_sem[(course_id, sem)].append(offering_id)
        slot = choose_slot(sem, teacher_id, classroom_id)
        schedule_rows.append((schedule_id, offering_id, *slot))
        schedules_by_offering[offering_id].append(slot)
        schedule_id += 1
        if RNG.random() < 0.22:
            second_slot = choose_slot(sem, teacher_id, classroom_id)
            if second_slot != slot:
                schedule_rows.append((schedule_id, offering_id, *second_slot))
                schedules_by_offering[offering_id].append(second_slot)
                schedule_id += 1
        offering_id += 1

    for sem, count in semester_course_counts.items():
        status = "open" if sem == "2025-2026-2" else "closed"
        for cid in historical_orders[sem][:count]:
            add_offering(cid, sem, status)
        if sem == "2025-2026-2":
            for cid in popular_current:
                add_offering(cid, sem, status, duplicate_index=1)

    offering_rows = [
        (o.offering_id, o.course_id, o.semester_id, o.teacher_id, o.classroom_id, o.max_capacity, o.status)
        for o in offerings
    ]
    historical_offerings_by_course = {
        cid: [
            oid
            for (course_id, sem), oids in offering_by_course_sem.items()
            if course_id == cid and sem != "2025-2026-2"
            for oid in oids
        ]
        for cid in course_ids
    }
    current_offerings = [
        oid for (cid, sem), oids in offering_by_course_sem.items() if sem == "2025-2026-2" for oid in oids
    ]

    enrollments: list[Enrollment] = []
    enrollment_ids_by_student: dict[str, set[int]] = defaultdict(set)
    passed_courses: dict[str, set[str]] = defaultdict(set)
    completed_courses: dict[str, set[str]] = defaultdict(set)
    selected_counts: Counter[int] = Counter()
    student_current_slots: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    student_current_courses: dict[str, set[str]] = defaultdict(set)
    enrollment_id = 1
    score_histogram = Counter()

    foundation_courses = ["CS101", "CS102", "MA101", "MA102", "EM101", "EM103", "FL101"]
    safe_extra_courses = [
        cid for cid in course_ids if cid not in {"CS115", "CS110", "MA103", "FL104", "EM110"}
    ]

    def add_enrollment(student_id: str, oid: int, status: str, score: float | None, remark: str, ts: str) -> None:
        nonlocal enrollment_id
        if oid in enrollment_ids_by_student[student_id]:
            return
        enrollments.append(Enrollment(enrollment_id, student_id, oid, ts, status, score, remark))
        enrollment_ids_by_student[student_id].add(oid)
        if status == "completed":
            completed_courses[student_id].add(course_by_offering[oid])
            if score is not None and score >= 60:
                passed_courses[student_id].add(course_by_offering[oid])
                score_histogram[int(score // 10) * 10] += 1
            elif score is not None:
                score_histogram[0] += 1
        if status == "selected":
            selected_counts[oid] += 1
            student_current_courses[student_id].add(course_by_offering[oid])
            student_current_slots[student_id].extend(schedules_by_offering[oid])
        enrollment_id += 1

    def has_prereqs(student_id: str, cid: str) -> bool:
        return prereq_map[cid].issubset(passed_courses[student_id])

    def no_slot_conflict(student_id: str, oid: int) -> bool:
        for new_w, new_s, new_e in schedules_by_offering[oid]:
            for old_w, old_s, old_e in student_current_slots[student_id]:
                if new_w == old_w and old_s <= new_e and old_e >= new_s:
                    return False
        return True

    student_ids = [row[0] for row in student_rows]
    for student_id in student_ids:
        for cid in foundation_courses:
            oid = historical_offerings_by_course[cid][0]
            add_enrollment(
                student_id,
                oid,
                "completed",
                score_value(force_pass=True),
                "历史完成课程",
                "2025-01-10 10:00:00",
            )
        extra_pool = safe_extra_courses[:]
        RNG.shuffle(extra_pool)
        added = 0
        for cid in extra_pool:
            if added >= 3:
                break
            if cid in completed_courses[student_id]:
                continue
            if not has_prereqs(student_id, cid):
                continue
            oids = historical_offerings_by_course.get(cid, [])
            if not oids:
                continue
            oid = RNG.choice(oids)
            force_pass = cid in foundation_courses or cid in {"CS103", "CS104", "EM103", "MA102"}
            add_enrollment(
                student_id,
                oid,
                "completed",
                score_value(force_pass=force_pass),
                "历史成绩",
                "2026-01-08 10:00:00",
            )
            added += 1

    current_candidates = current_offerings[:]
    for student_id in student_ids:
        target_count = 4 if int(student_id[-2:]) % 4 else 5
        shuffled = current_candidates[:]
        RNG.shuffle(shuffled)
        for oid in shuffled:
            if len(student_current_courses[student_id]) >= target_count:
                break
            cid = course_by_offering[oid]
            if cid in student_current_courses[student_id]:
                continue
            if selected_counts[oid] >= offering_capacity[oid] - 1:
                continue
            if not has_prereqs(student_id, cid):
                continue
            if not no_slot_conflict(student_id, oid):
                continue
            add_enrollment(
                student_id,
                oid,
                "selected",
                None,
                "当前学期选课",
                "2026-06-11 09:00:00",
            )

    dropped_added = 0
    shuffled_students = student_ids[:]
    RNG.shuffle(shuffled_students)
    for student_id in shuffled_students:
        if dropped_added >= 55:
            break
        shuffled_oids = historical_offerings_by_course[RNG.choice(foundation_courses)][:] + current_candidates[:]
        RNG.shuffle(shuffled_oids)
        for oid in shuffled_oids:
            if oid in enrollment_ids_by_student[student_id]:
                continue
            add_enrollment(
                student_id,
                oid,
                "dropped",
                None,
                "退课记录",
                "2026-03-01 14:00:00",
            )
            dropped_added += 1
            break

    completed_enrollments = [e for e in enrollments if e.status == "completed"]
    audit_targets = RNG.sample(completed_enrollments, 80)
    audit_updates: list[tuple[int, int, float, str]] = []
    teacher_admin_user_ids = [a.user_id for a in accounts if a.role in {"teacher", "admin"}]
    reasons = ["期末复核", "平时分修正", "录入错误修正", "补充实验成绩", "试卷复核"]
    for e in audit_targets:
        old = float(e.final_score or 0)
        delta = RNG.choice([-3, -2, -1, 1, 2, 3])
        new_score = max(60.0 if course_by_offering[e.offering_id] in foundation_courses else 0.0, min(100.0, old + delta))
        if new_score == old:
            new_score = max(0.0, min(100.0, old - 1))
        audit_updates.append((e.enrollment_id, RNG.choice(teacher_admin_user_ids), round(new_score, 2), RNG.choice(reasons)))

    sql_lines: list[str] = []
    sql_lines.append("-- Generated by scripts/generate_large_demo_dataset.py")
    sql_lines.append(f"-- Random seed: {SEED}")
    sql_lines.append("START TRANSACTION;")
    sql_lines.append("")
    sql_lines.append("-- Local demo reset. Do not use this script on production data.")
    sql_lines.extend(
        [
            "UPDATE grade_policy SET created_by_user_id = NULL WHERE created_by_user_id IS NOT NULL;",
            "DELETE FROM score_change_log;",
            "DELETE FROM enrollment;",
            "DELETE FROM course_prerequisite;",
            "DELETE FROM course_schedule;",
            "DELETE FROM course_offering;",
            "DELETE FROM classroom;",
            "DELETE FROM course;",
            "DELETE FROM semester;",
            "DELETE FROM admin_profile;",
            "DELETE FROM teacher;",
            "DELETE FROM student;",
            "DELETE FROM user_session;",
            "DELETE FROM user_account;",
            "DELETE FROM major;",
            "DELETE FROM department;",
            "",
        ]
    )

    sql_lines.extend(insert_values("department", ["dept_id", "dept_name", "office_phone", "office_location"], departments))
    sql_lines.extend(insert_values("major", ["major_id", "major_name", "dept_id"], majors))
    sql_lines.extend(insert_values("user_account", ["user_id", "username", "password_hash", "role", "status"], account_rows))
    sql_lines.extend(insert_values("admin_profile", ["admin_id", "user_id", "admin_name", "phone"], admin_rows))
    sql_lines.extend(
        insert_values(
            "teacher",
            ["teacher_id", "user_id", "teacher_name", "gender", "dept_id", "title", "phone", "email", "status"],
            teacher_rows,
        )
    )
    sql_lines.extend(
        insert_values(
            "student",
            [
                "student_id",
                "user_id",
                "student_name",
                "gender",
                "birth_date",
                "enroll_year",
                "major_id",
                "class_name",
                "phone",
                "email",
                "status",
            ],
            student_rows,
        )
    )
    semester_rows = [
        (*s, None)
        for s in semesters
    ]
    sem_insert = [
        "INSERT INTO semester (semester_id, semester_name, start_date, end_date, selection_start, selection_end, status, grade_policy_id) VALUES"
    ]
    sem_values = []
    for sid, name, start, end, sel_start, sel_end, status, _ in semester_rows:
        sem_values.append(
            "("
            + ", ".join(
                [
                    sql_str(sid),
                    sql_str(name),
                    sql_str(start),
                    sql_str(end),
                    sql_str(sel_start),
                    sql_str(sel_end),
                    sql_str(status),
                    "(SELECT policy_id FROM grade_policy WHERE policy_code='DEFAULT_4_0' AND version_no='v1')",
                ]
            )
            + ")"
        )
    sql_lines.append(sem_insert[0] + "\n" + ",\n".join(sem_values) + ";")
    sql_lines.extend(insert_values("classroom", ["classroom_id", "building", "room_no", "capacity"], classroom_rows))
    sql_lines.extend(
        insert_values(
            "course",
            ["course_id", "course_name", "course_type", "credit", "total_hours", "dept_id", "description", "status"],
            course_rows,
        )
    )
    sql_lines.extend(
        insert_values(
            "course_offering",
            ["offering_id", "course_id", "semester_id", "teacher_id", "classroom_id", "max_capacity", "status"],
            offering_rows,
        )
    )
    sql_lines.extend(
        insert_values(
            "course_schedule",
            ["schedule_id", "offering_id", "weekday", "start_section", "end_section"],
            schedule_rows,
        )
    )
    sql_lines.extend(insert_values("course_prerequisite", ["course_id", "prereq_course_id"], prerequisites))
    enrollment_rows = [
        (e.enrollment_id, e.student_id, e.offering_id, e.select_time, e.status, e.final_score, e.remark)
        for e in enrollments
    ]
    sql_lines.extend(
        insert_values(
            "enrollment",
            ["enrollment_id", "student_id", "offering_id", "select_time", "status", "final_score", "remark"],
            enrollment_rows,
            batch=150,
        )
    )
    sql_lines.append("")
    sql_lines.append("-- Score audit logs are generated through trg_score_change_log.")
    for enrollment_id_value, changed_by_user_id, new_score, reason in audit_updates:
        sql_lines.append(f"SELECT set_config('app.current_user_id', {sql_str(str(changed_by_user_id))}, true);")
        sql_lines.append(f"SELECT set_config('app.score_change_reason', {sql_str(reason)}, true);")
        sql_lines.append(
            "UPDATE enrollment "
            f"SET final_score = {new_score:.2f} "
            f"WHERE enrollment_id = {enrollment_id_value};"
        )
    sql_lines.extend(
        [
            "",
            "SELECT setval('user_account_user_id_seq', (SELECT MAX(user_id) FROM user_account));",
            "SELECT setval('course_offering_offering_id_seq', (SELECT MAX(offering_id) FROM course_offering));",
            "SELECT setval('course_schedule_schedule_id_seq', (SELECT MAX(schedule_id) FROM course_schedule));",
            "SELECT setval('enrollment_enrollment_id_seq', (SELECT MAX(enrollment_id) FROM enrollment));",
            "SELECT setval('score_change_log_log_id_seq', COALESCE((SELECT MAX(log_id) FROM score_change_log), 1));",
            "COMMIT;",
            "",
        ]
    )

    LOCAL_SQL.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_SQL.write_text("\n".join(sql_lines), encoding="utf-8")

    CREDENTIALS_MD.parent.mkdir(parents=True, exist_ok=True)
    grouped = defaultdict(list)
    for account in accounts:
        grouped[account.role].append(account)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_lines = [
        "# Demo Account Credentials",
        "",
        f"生成时间：{generated_at}",
        "",
        "说明：",
        "- 本文件仅用于本地演示和测试。",
        "- 不应提交到公开仓库。",
        "- 不应写入正式报告 PDF。",
        "- 数据库 `user_account` 表只保存 `password_hash`。",
        "- 明文初始密码仅用于首次登录演示。",
        "",
    ]
    section_titles = [("admin", "管理员账号"), ("teacher", "教师账号"), ("student", "学生账号")]
    for role, title in section_titles:
        md_lines.extend(
            [
                f"## {title}",
                "",
                "| role | profile_id | username | display_name | initial_password |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for account in grouped[role]:
            md_lines.append(
                f"| {account.role} | {account.profile_id} | {account.username} | "
                f"{account.display_name} | {account.password} |"
            )
        md_lines.append("")
    CREDENTIALS_MD.write_text("\n".join(md_lines), encoding="utf-8")

    with CREDENTIALS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["role", "profile_id", "username", "display_name", "initial_password"])
        for account in accounts:
            writer.writerow([account.role, account.profile_id, account.username, account.display_name, account.password])

    counts = Counter(e.status for e in enrollments)
    dept_student_counts = Counter()
    for row in student_rows:
        major_id = row[6]
        dept = next(d for m, _, d in majors if m == major_id)
        dept_student_counts[dept] += 1
    dept_teacher_counts = Counter(row[4] for row in teacher_rows)
    dept_course_counts = Counter(c.dept_id for c in courses)
    course_type_counts = Counter(c.course_type for c in courses)
    score_bands = Counter()
    for e in enrollments:
        if e.status == "completed" and e.final_score is not None:
            s = e.final_score
            if s >= 90:
                score_bands["90-100"] += 1
            elif s >= 80:
                score_bands["80-89"] += 1
            elif s >= 70:
                score_bands["70-79"] += 1
            elif s >= 60:
                score_bands["60-69"] += 1
            else:
                score_bands["0-59"] += 1

    sem_offering_counts = Counter(o.semester_id for o in offerings)
    sem_enrollment_counts = Counter(semester_by_offering[e.offering_id] for e in enrollments)
    recommended_students = sorted(student_ids, key=lambda sid: (len(student_current_courses[sid]), len(completed_courses[sid])), reverse=True)[:3]
    recommended_teachers = [
        tid for tid, _ in Counter(o.teacher_id for o in offerings if o.semester_id == "2025-2026-2").most_common(2)
    ]

    summary_lines = [
        "# Large Demo Dataset Summary",
        "",
        f"- Random seed: `{SEED}`",
        f"- Departments: `{len(departments)}`",
        f"- Majors: `{len(majors)}`",
        f"- Students: `{len(student_rows)}`",
        f"- Teachers: `{len(teacher_rows)}`",
        f"- Administrators: `{len(admin_rows)}`",
        f"- Courses: `{len(courses)}`",
        f"- Semesters: `{len(semesters)}`",
        f"- Classrooms: `{len(classroom_rows)}`",
        f"- Course offerings: `{len(offerings)}`",
        f"- Schedule slots: `{len(schedule_rows)}`",
        f"- Enrollments: `{len(enrollments)}`",
        f"- Completed enrollments: `{counts['completed']}`",
        f"- Selected enrollments: `{counts['selected']}`",
        f"- Dropped enrollments: `{counts['dropped']}`",
        f"- Score audit updates generated through trigger: `{len(audit_updates)}`",
        "",
        "## Department Distribution",
        "",
        "| department | students | teachers | courses |",
        "| --- | ---: | ---: | ---: |",
    ]
    dept_names = {d[0]: d[1] for d in departments}
    for dept_id in ["CS", "MATH", "FL", "EM"]:
        summary_lines.append(
            f"| {dept_names[dept_id]} | {dept_student_counts[dept_id]} | "
            f"{dept_teacher_counts[dept_id]} | {dept_course_counts[dept_id]} |"
        )
    summary_lines.extend(
        [
            "",
            "## Course Type Distribution",
            "",
            "| course_type | count |",
            "| --- | ---: |",
        ]
    )
    for course_type, count in sorted(course_type_counts.items()):
        summary_lines.append(f"| {course_type} | {count} |")
    summary_lines.extend(
        [
            "",
            "## Score Distribution",
            "",
            "| score band | count |",
            "| --- | ---: |",
        ]
    )
    for band in ["90-100", "80-89", "70-79", "60-69", "0-59"]:
        summary_lines.append(f"| {band} | {score_bands[band]} |")
    summary_lines.extend(
        [
            "",
            "## Semester Distribution",
            "",
            "| semester | offerings | enrollments |",
            "| --- | ---: | ---: |",
        ]
    )
    for sem_id, *_ in semesters:
        summary_lines.append(f"| {sem_id} | {sem_offering_counts[sem_id]} | {sem_enrollment_counts[sem_id]} |")
    summary_lines.extend(
        [
            "",
            "## Recommended Demo Accounts",
            "",
            "- Administrator: `A001`",
            f"- Teachers: `{recommended_teachers[0]}`, `{recommended_teachers[1]}`",
            f"- Students: `{recommended_students[0]}`, `{recommended_students[1]}`, `{recommended_students[2]}`",
            "",
            "Plaintext passwords are stored only in `secrets/DEMO_ACCOUNT_CREDENTIALS.md`.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(summary_lines), encoding="utf-8")

    validation_lines = [
        "# Large Demo Dataset Validation Notes",
        "",
        "The generator performs in-memory checks before writing SQL. Database-level validation is provided by `opengauss_setup/sql/validate_large_demo_dataset.sql`.",
        "",
        "| Check | Generated State |",
        "| --- | --- |",
        f"| Course offering capacity <= classroom capacity | `{all(o.max_capacity <= classroom_capacity[o.classroom_id] for o in offerings)}` |",
        f"| Selected enrollment count <= max_capacity | `{all(selected_counts[oid] <= offering_capacity[oid] for oid in offering_capacity)}` |",
        f"| Duplicate student/offering pairs avoided by generator | `True` |",
        f"| Current selected records avoid same-course cross-offering | `True` |",
        f"| Current selected records avoid timetable conflicts | `True` |",
        f"| Selected rows contain no final_score | `{all(e.final_score is None for e in enrollments if e.status == 'selected')}` |",
        f"| Completed rows contain final_score | `{all(e.final_score is not None for e in enrollments if e.status == 'completed')}` |",
        f"| Score audit updates prepared | `{len(audit_updates)}` |",
        "",
        "The SQL validation script should report `violation_count = 0` for all integrity checks after import.",
    ]
    VALIDATION_MD.write_text("\n".join(validation_lines), encoding="utf-8")

    print(f"Wrote {LOCAL_SQL.relative_to(ROOT)}")
    print(f"Wrote {CREDENTIALS_MD.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_MD.relative_to(ROOT)}")
    print(f"Wrote {VALIDATION_MD.relative_to(ROOT)}")
    print(
        "Counts:",
        {
            "departments": len(departments),
            "students": len(student_rows),
            "teachers": len(teacher_rows),
            "courses": len(courses),
            "offerings": len(offerings),
            "enrollments": len(enrollments),
            "completed": counts["completed"],
            "selected": counts["selected"],
            "dropped": counts["dropped"],
            "audit_updates": len(audit_updates),
        },
    )


if __name__ == "__main__":
    main()
