from datetime import date

import pandas as pd
import streamlit as st

from db.connection import query
from pages._guards import require_role
from services.course_service import list_semesters
from services.score_service import get_score_change_log
from ui.components import (
    render_app_header,
    render_empty_state,
    render_filter_bar,
    render_metric_card,
    render_section_title,
)


def render() -> None:
    require_role("admin")
    render_app_header(
        "成绩审计日志",
        "按学期、教师、课程、学生和时间范围追踪成绩变更。",
    )

    total_log = query("SELECT COUNT(*) AS n FROM score_change_log")
    today_log = query(
        "SELECT COUNT(*) AS n FROM score_change_log WHERE changed_at::date = CURRENT_DATE"
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("累计日志", int(total_log[0]["n"]) if total_log else 0, caption="score_change_log")
    with c2:
        render_metric_card("今日修改", int(today_log[0]["n"]) if today_log else 0, caption="按 changed_at 统计")
    with c3:
        render_metric_card("审计来源", "数据库触发器", caption="trg_score_change_log")

    semesters = list_semesters()
    teachers = query("SELECT teacher_id, teacher_name FROM teacher ORDER BY teacher_id")

    with render_filter_bar("筛选条件", "所有筛选均作用于成绩审计日志查询，不修改数据。"):
        f1, f2, f3, f4 = st.columns([1.1, 1.1, 1.1, 1.1])
        semester_options = [""] + [s["semester_id"] for s in semesters]
        sem_map = {s["semester_id"]: s["semester_name"] for s in semesters}
        selected_semester = f1.selectbox(
            "学期",
            semester_options,
            format_func=lambda sid: "全部学期" if sid == "" else sem_map.get(sid, sid),
        )

        teacher_options = [""] + [t["teacher_id"] for t in teachers]
        teacher_map = {t["teacher_id"]: f"{t['teacher_id']} {t['teacher_name']}" for t in teachers}
        selected_teacher = f2.selectbox(
            "教师",
            teacher_options,
            format_func=lambda tid: "全部教师" if tid == "" else teacher_map.get(tid, tid),
        )

        course_keyword = f3.text_input("课程", placeholder="课程号 / 课程名")
        student_keyword = f4.text_input("学生", placeholder="学号 / 姓名")

        d0, d1, d2, d3 = st.columns([0.9, 1, 1, 0.8])
        use_date = d0.checkbox("按日期筛选")
        date_from = d1.date_input("开始日期", value=date.today(), disabled=not use_date)
        date_to = d2.date_input("结束日期", value=date.today(), disabled=not use_date)
        limit = d3.number_input("条数", 10, 500, 100, 10)

    logs = get_score_change_log(
        semester_id=selected_semester or None,
        teacher_id=selected_teacher or None,
        course_keyword=course_keyword.strip() or None,
        student_keyword=student_keyword.strip() or None,
        date_from=date_from if use_date else None,
        date_to=date_to if use_date else None,
        limit=int(limit),
    )

    render_section_title("日志明细", f"当前筛选结果 {len(logs)} 条。")
    if not logs:
        render_empty_state("暂无匹配日志", "可以放宽筛选条件，或在成绩录入后查看审计记录。")
        return

    df = pd.DataFrame(
        [
            {
                "时间": str(row["changed_at"]),
                "学期": row["semester_name"],
                "课程": f"{row['course_id']} {row['course_name']}",
                "教师": row["teacher_name"],
                "学生": f"{row['student_id']} {row['student_name']}",
                "原成绩": row["old_score"] if row["old_score"] is not None else "—",
                "新成绩": row["new_score"],
                "修改人": row["changed_by"],
                "原因": row["reason"] or "—",
            }
            for row in logs
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
