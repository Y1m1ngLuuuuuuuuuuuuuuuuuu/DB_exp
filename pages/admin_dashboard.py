import streamlit as st
import pandas as pd
from pages._guards import require_role
from db.connection import query_one, query

def render() -> None:
    require_role("admin")
    st.header("管理员首页")

    stats = {
        "在籍学生": query_one("SELECT COUNT(*) n FROM student WHERE status='enrolled'")["n"],
        "在职教师": query_one("SELECT COUNT(*) n FROM teacher WHERE status='active'")["n"],
        "开放课程": query_one("SELECT COUNT(*) n FROM course WHERE status='active'")["n"],
        "本期选课数": query_one(
            "SELECT COUNT(*) n FROM enrollment e "
            "JOIN course_offering co ON e.offering_id=co.offering_id "
            "JOIN semester s ON co.semester_id=s.semester_id "
            "WHERE s.status='open' AND e.status='selected'"
        )["n"],
    }
    cols = st.columns(4)
    for (label, val), col in zip(stats.items(), cols):
        col.metric(label, val)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("各班次选课情况（最近学期）")
        rows = query(
            """
            SELECT c.course_name, t.teacher_name,
                   co.selected_count, co.max_capacity, s.semester_name
            FROM course_offering co
            JOIN course   c ON co.course_id   = c.course_id
            JOIN teacher  t ON co.teacher_id  = t.teacher_id
            JOIN semester s ON co.semester_id = s.semester_id
            ORDER BY s.start_date DESC, co.selected_count DESC
            LIMIT 12
            """
        )
        if rows:
            df = pd.DataFrame([
                {
                    "学期":   r["semester_name"],
                    "课程":   r["course_name"],
                    "教师":   r["teacher_name"],
                    "已选/上限": f"{r['selected_count']} / {r['max_capacity']}",
                }
                for r in rows
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

    with right:
        st.subheader("各院系在籍学生人数")
        dept_rows = query(
            """
            SELECT d.dept_name, COUNT(s.student_id) cnt
            FROM department d
            LEFT JOIN major   m ON d.dept_id  = m.dept_id
            LEFT JOIN student s ON m.major_id = s.major_id AND s.status='enrolled'
            GROUP BY d.dept_id, d.dept_name
            ORDER BY cnt DESC
            """
        )
        if dept_rows:
            df2 = pd.DataFrame(
                [{"院系": r["dept_name"], "学生人数": r["cnt"]} for r in dept_rows]
            )
            st.bar_chart(df2.set_index("院系"))
