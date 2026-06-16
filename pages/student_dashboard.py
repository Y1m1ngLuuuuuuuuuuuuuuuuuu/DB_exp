from datetime import datetime

import pandas as pd
import streamlit as st

from db.connection import query, query_one
from pages._guards import require_role
from services.course_service import get_active_semester, list_enrolled_offerings
from services.score_service import get_student_transcript
from services.student_service import get_student_info
from ui.components import (
    render_app_header,
    render_empty_state,
    render_metric_card,
    render_section_title,
)


_WEEKDAY_LABEL = {
    1: "周一",
    2: "周二",
    3: "周三",
    4: "周四",
    5: "周五",
    6: "周六",
    7: "周日",
}


def render() -> None:
    require_role("student")
    student_id = st.session_state.student_id
    info = get_student_info(student_id) or {}
    semester = get_active_semester()
    student_name = info.get("student_name") or st.session_state.username

    render_app_header(f"你好，{student_name}")

    enrolled = []
    if semester:
        enrolled = list_enrolled_offerings(student_id, semester["semester_id"])
    transcript = get_student_transcript(student_id)
    selected = [row for row in enrolled if row["enroll_status"] == "selected"]
    completed = [row for row in transcript if row.get("final_score") is not None]
    avg_score = (
        sum(float(row["final_score"]) for row in completed) / len(completed)
        if completed
        else None
    )
    gpa_row = None
    if semester:
        gpa_row = query_one(
            """
            SELECT weighted_gpa, total_credits, completed_course_count
            FROM v_student_gpa_summary
            WHERE student_id=%s AND semester_id=%s
            """,
            (student_id, semester["semester_id"]),
        )

    has_gpa = bool(gpa_row and gpa_row.get("weighted_gpa") is not None)
    metric_columns = st.columns(4 if has_gpa else 3)
    c1, c2, c3 = metric_columns[:3]
    with c1:
        render_metric_card("当前已选课程", len(selected), "状态为 selected 的本学期课程")
    with c2:
        render_metric_card("本学期课程", len(enrolled), semester["semester_name"] if semester else "暂无学期")
    with c3:
        render_metric_card("已完成课程", len(completed), "已结课且有成绩记录")
    if has_gpa:
        with metric_columns[3]:
            render_metric_card(
                "加权绩点",
                f"{float(gpa_row['weighted_gpa']):.2f}",
                "由绩点规则视图动态计算",
            )

    render_section_title("今日课程", "按结构化课表视图汇总今天的课程安排。")
    today = datetime.now().isoweekday()
    today_rows = query(
        """
        SELECT course_name, teacher_name, building, room_no, start_section, end_section, semester_name
        FROM v_student_timetable
        WHERE student_id=%s AND weekday=%s
        ORDER BY start_section
        """,
        (student_id, today),
    )
    if today_rows:
        df = pd.DataFrame(
            [
                {
                    "星期": _WEEKDAY_LABEL[today],
                    "节次": f"{r['start_section']}-{r['end_section']}",
                    "课程": r["course_name"],
                    "教师": r["teacher_name"],
                    "教室": f"{r['building'] or ''}{r['room_no'] or ''}".strip() or "待定",
                    "学期": r["semester_name"],
                }
                for r in today_rows
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        render_empty_state("今天没有课程", "可以去课程选课页面查看本学期可选课程。")

    render_section_title("成绩概览", "仅展示已经完成并录入成绩的课程。")
    if completed:
        st.caption(f"平均成绩：{avg_score:.1f}" if avg_score is not None else "平均成绩：-")
        score_df = pd.DataFrame(
            [
                {
                    "课程": row["course_name"],
                    "学期": row["semester_name"],
                    "成绩": float(row["final_score"]),
                    "绩点": float(row["gpa_point"]) if row.get("gpa_point") is not None else None,
                    "等级": row.get("grade_label") or "-",
                }
                for row in completed[:8]
            ]
        )
        st.dataframe(score_df, use_container_width=True, hide_index=True)
    else:
        render_empty_state("暂无成绩", "已结课并录入成绩后，这里会显示最近成绩和绩点。")
