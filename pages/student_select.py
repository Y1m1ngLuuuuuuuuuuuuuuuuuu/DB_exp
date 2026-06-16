import pandas as pd
import streamlit as st

from db.connection import query
from pages._guards import require_role
from services.course_service import (
    get_active_semester,
    list_enrolled_offerings,
    list_offerings_for_student,
    list_semesters,
)
from services.selection_service import drop, enroll
from ui.components import (
    format_location,
    render_app_header,
    render_course_card,
    render_empty_state,
    render_error_message,
    render_section_title,
    render_success_message,
)

_TYPE_LABEL = {"required": "必修", "elective": "选修", "public": "公共"}
_STATUS_LABEL = {"selected": "已选", "dropped": "已退课", "completed": "已结课"}
_WEEKDAY_LABEL = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}


def _filter_available(rows: list[dict], keyword: str, course_type: str, has_seats_only: bool) -> list[dict]:
    filtered = rows
    if keyword:
        kw = keyword.strip().lower()
        filtered = [
            row for row in filtered
            if kw in str(row["course_name"]).lower() or kw in str(row["course_id"]).lower()
        ]
    if course_type != "all":
        filtered = [row for row in filtered if row["course_type"] == course_type]
    if has_seats_only:
        filtered = [row for row in filtered if int(row["seats_left"]) > 0]
    return filtered


def _filter_enrolled(rows: list[dict], keyword: str, course_type: str) -> list[dict]:
    filtered = rows
    if keyword:
        kw = keyword.strip().lower()
        filtered = [
            row for row in filtered
            if kw in str(row["course_name"]).lower() or kw in str(row["course_id"]).lower()
        ]
    if course_type != "all":
        filtered = [row for row in filtered if row["course_type"] == course_type]
    return filtered


def _group_available_by_course(rows: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    for row in rows:
        course_id = row["course_id"]
        if course_id not in groups:
            groups[course_id] = {
                "course_id": course_id,
                "course_name": row["course_name"],
                "course_type": row["course_type"],
                "credit": row["credit"],
                "offerings": [],
            }
        groups[course_id]["offerings"].append(row)
    return list(groups.values())


def render() -> None:
    require_role("student")
    student_id = st.session_state.student_id

    semesters = list_semesters()
    if not semesters:
        render_app_header("课程选课", "当前没有学期数据。")
        render_empty_state("暂无学期", "请等待管理员创建学期后再进行选课。")
        return

    active = get_active_semester()
    sem_ids = [s["semester_id"] for s in semesters]
    default_index = sem_ids.index(active["semester_id"]) if active and active["semester_id"] in sem_ids else 0

    render_app_header("课程选课", "筛选课程、查看容量和时间安排，并提交选课或退课操作。")

    f1, f2, f3, f4 = st.columns([1.2, 1.2, 1, 1])
    semester_id = f1.selectbox(
        "学期",
        options=sem_ids,
        index=default_index,
        format_func=lambda sid: next(s["semester_name"] for s in semesters if s["semester_id"] == sid),
    )
    keyword = f2.text_input("课程搜索", placeholder="课程号 / 课程名")
    course_type = f3.selectbox(
        "课程类型",
        options=["all", "required", "elective", "public"],
        format_func=lambda value: "全部" if value == "all" else _TYPE_LABEL[value],
    )
    has_seats_only = f4.checkbox("仅看有余量", value=False)

    current_semester = next(s for s in semesters if s["semester_id"] == semester_id)
    if current_semester.get("status") != "open":
        st.info("当前选择的学期未处于开放选课状态，课程信息仅供查看。")
    elif current_semester.get("selection_start") and current_semester.get("selection_end"):
        st.caption(f"选课时间：{current_semester['selection_start']} 至 {current_semester['selection_end']}")

    tab_avail, tab_enrolled, tab_timetable = st.tabs(["可选课程", "已选课程", "我的课表"])

    with tab_avail:
        available = _filter_available(
            list_offerings_for_student(student_id, semester_id),
            keyword,
            course_type,
            has_seats_only,
        )
        course_groups = _group_available_by_course(available)
        render_section_title("可选课程", f"共 {len(course_groups)} 门课程、{len(available)} 个教学班符合条件。")
        if not available:
            render_empty_state("没有匹配课程", "可以调整筛选条件，或查看其他学期课程。")
        for group in course_groups:
            offerings = group["offerings"]
            total_seats = sum(int(row["seats_left"]) for row in offerings)
            total_capacity = sum(int(row["max_capacity"]) for row in offerings)
            type_label = _TYPE_LABEL.get(group["course_type"], group["course_type"])
            expander_label = (
                f"{group['course_id']} · {group['course_name']} ｜ "
                f"{type_label} ｜ {group['credit']} 学分 ｜ "
                f"{len(offerings)} 个教学班 ｜ 余量 {total_seats} / {total_capacity}"
            )

            with st.expander(expander_label, expanded=False):
                for idx, row in enumerate(offerings):
                    render_course_card(
                        f"教学班 {row['offering_id']}",
                        f"{row['teacher_name']} · {row.get('schedule_text') or '时间待定'}",
                        {
                            "班次": row["offering_id"],
                            "上课时间": row.get("schedule_text") or "时间待定",
                            "教师": row["teacher_name"],
                            "教室": format_location(row),
                            "余量": f"{row['seats_left']} / {row['max_capacity']}",
                        },
                        status="open" if row["seats_left"] > 0 else "closed",
                        status_label="可选" if row["seats_left"] > 0 else "已满",
                    )
                    b1, b2, _ = st.columns([1, 1, 4])
                    if row["seats_left"] > 0:
                        if b1.button("选课", key=f"enroll_{row['offering_id']}", type="primary"):
                            ok, msg = enroll(student_id, row["offering_id"])
                            if ok:
                                render_success_message("选课成功。")
                                st.rerun()
                            else:
                                render_error_message(msg)
                    else:
                        b1.button("名额已满", key=f"full_{row['offering_id']}", disabled=True)
                    b2.caption("数据库会检查容量、时间冲突、先修课程和同课跨班。")
                    if idx < len(offerings) - 1:
                        st.divider()

    with tab_enrolled:
        enrolled_all = list_enrolled_offerings(student_id, semester_id)
        enrolled = _filter_enrolled(enrolled_all, keyword, course_type)
        if len(enrolled) == len(enrolled_all):
            enrolled_caption = f"共 {len(enrolled)} 条选课记录。"
        else:
            enrolled_caption = f"共 {len(enrolled)} 条符合条件，全部 {len(enrolled_all)} 条。"
        render_section_title("已选课程", enrolled_caption)
        if not enrolled:
            render_empty_state("没有匹配课程", "可以调整搜索关键词或课程类型筛选条件。")
        for row in enrolled:
            status_label = _STATUS_LABEL.get(row["enroll_status"], row["enroll_status"])
            render_course_card(
                f"{row['course_id']} · {row['course_name']}",
                f"教学班 {row['offering_id']} · {row['teacher_name']}",
                {
                    "班次": row["offering_id"],
                    "学分": row["credit"],
                    "类型": _TYPE_LABEL.get(row["course_type"], row["course_type"]),
                    "上课时间": row.get("schedule_text") or "时间待定",
                    "成绩": row["final_score"] if row["final_score"] is not None else "待录入",
                    "绩点": row["gpa_point"] if row["gpa_point"] is not None else "-",
                },
                status=row["enroll_status"],
                status_label=status_label,
            )
            if row["enroll_status"] == "selected":
                if st.button("退课", key=f"drop_{row['enrollment_id']}", type="secondary"):
                    ok, msg = drop(row["enrollment_id"], student_id)
                    if ok:
                        render_success_message("退课成功。")
                        st.rerun()
                    else:
                        render_error_message(msg)

    with tab_timetable:
        rows = query(
            """
            SELECT weekday, start_section, end_section, course_name,
                   teacher_name, building, room_no, semester_id
            FROM v_student_timetable
            WHERE student_id=%s AND semester_id=%s
            ORDER BY weekday, start_section
            """,
            (student_id, semester_id),
        )
        render_section_title("我的课表", "按星期和节次展示当前 selected 状态课程。")
        if not rows:
            render_empty_state("暂无课表", "选择课程后，结构化课表会显示在这里。")
        else:
            df = pd.DataFrame(
                [
                    {
                        "星期": _WEEKDAY_LABEL.get(r["weekday"], r["weekday"]),
                        "节次": f"{r['start_section']}-{r['end_section']}",
                        "课程": r["course_name"],
                        "教师": r["teacher_name"],
                        "教室": f"{r['building'] or ''}{r['room_no'] or ''}".strip() or "待定",
                    }
                    for r in rows
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
