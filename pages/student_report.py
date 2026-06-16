import pandas as pd
import streamlit as st

from pages._guards import require_role
from services.score_service import get_student_transcript
from services.student_service import get_student_info
from ui.components import render_app_header, render_empty_state, render_metric_card, render_section_title

_TYPE_LABEL = {"required": "必修", "elective": "选修", "public": "公共"}


def render() -> None:
    require_role("student")
    student_id = st.session_state.student_id

    info = get_student_info(student_id)
    if info:
        subtitle = (
            f"{info.get('major_name', '-')} · {info.get('class_name', '-')} · "
            f"{info.get('dept_name', '-')}"
        )
        title = f"{info['student_name']} 的成绩与绩点"
    else:
        title = "成绩与绩点"
        subtitle = "已结课课程的成绩和绩点汇总。"
    render_app_header(title, subtitle)

    records = get_student_transcript(student_id)
    if not records:
        render_empty_state("暂无成绩记录", "课程结课并录入成绩后，这里会展示成绩单。")
        return

    total_credit = sum(float(r["credit"]) for r in records)
    scored = [r for r in records if r["final_score"] is not None]
    passed = [r for r in scored if float(r["final_score"]) >= 60]
    avg_score = sum(float(r["final_score"]) for r in scored) / len(scored) if scored else None
    weighted_gpa = sum(float(r["credit"]) * float(r["gpa_point"] or 0) for r in records)
    avg_gpa = weighted_gpa / total_credit if total_credit else None

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("已修门数", len(records), "completed 状态课程")
    with m2:
        render_metric_card("累计学分", f"{total_credit:.1f}", f"通过 {len(passed)} 门课程")
    with m3:
        render_metric_card("平均成绩", f"{avg_score:.1f}" if avg_score is not None else "-", "百分制成绩")
    with m4:
        render_metric_card("加权绩点", f"{avg_gpa:.2f}" if avg_gpa is not None else "-", "由绩点规则视图计算")

    render_section_title("成绩明细")
    df = pd.DataFrame(
        [
            {
                "学期": r["semester_name"],
                "课程名": r["course_name"],
                "类型": _TYPE_LABEL.get(r["course_type"], r["course_type"]),
                "学分": float(r["credit"]),
                "任课教师": r["teacher_name"],
                "成绩": float(r["final_score"]) if r["final_score"] is not None else None,
                "等级": r.get("grade_label") or "-",
                "绩点": float(r["gpa_point"]) if r["gpa_point"] is not None else None,
            }
            for r in records
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
