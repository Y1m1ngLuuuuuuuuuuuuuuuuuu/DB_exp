"""
pages/student_report.py —— 学生个人成绩单
"""
import streamlit as st
import pandas as pd
from pages._guards import require_role
from services.score_service import get_student_transcript
from services.student_service import get_student_info

_TYPE_LABEL = {"required": "必修", "elective": "选修", "public": "公共"}


def render() -> None:
    require_role("student")
    student_id = st.session_state.student_id

    info = get_student_info(student_id)
    if info:
        st.header(f"成绩单  ·  {info['student_name']}（{student_id}）")
        c1, c2, c3 = st.columns(3)
        c1.caption(f"专业：{info.get('major_name', '-')}")
        c2.caption(f"班级：{info.get('class_name', '-')}")
        c3.caption(f"院系：{info.get('dept_name', '-')}")
    else:
        st.header("我的成绩单")

    records = get_student_transcript(student_id)
    if not records:
        st.info("暂无已结课成绩记录")
        return

    # 汇总统计
    total_credit  = sum(float(r["credit"]) for r in records)
    passed        = [r for r in records if r["final_score"] is not None and float(r["final_score"]) >= 60]
    avg_score     = sum(float(r["final_score"]) for r in records if r["final_score"]) / len(records)
    weighted_gpa  = sum(float(r["credit"]) * float(r["gpa_point"] or 0) for r in records)
    avg_gpa       = weighted_gpa / total_credit if total_credit else 0

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("已修门数",   len(records))
    m2.metric("累计学分",   f"{total_credit:.1f}")
    m3.metric("平均成绩",   f"{avg_score:.1f}")
    m4.metric("加权绩点",   f"{avg_gpa:.2f}")
    st.divider()

    df = pd.DataFrame([
        {
            "学期":     r["semester_name"],
            "课程名":   r["course_name"],
            "类型":     _TYPE_LABEL.get(r["course_type"], r["course_type"]),
            "学分":     float(r["credit"]),
            "任课教师": r["teacher_name"],
            "成绩":     float(r["final_score"]) if r["final_score"] is not None else None,
            "绩点":     float(r["gpa_point"])   if r["gpa_point"]   is not None else None,
        }
        for r in records
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
