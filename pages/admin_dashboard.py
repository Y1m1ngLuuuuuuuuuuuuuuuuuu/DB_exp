import pandas as pd
import streamlit as st

from db.connection import query, query_one
from pages._guards import require_role
from ui.components import render_app_header, render_empty_state, render_metric_card, render_section_title


def _count(sql: str) -> int:
    row = query_one(sql)
    return int(row["n"]) if row else 0


def render() -> None:
    require_role("admin")
    render_app_header(
        "管理员首页",
        "集中查看学生、教师、课程、教学班、选课记录和成绩审计日志。",
    )

    stats = {
        "在籍学生": _count("SELECT COUNT(*) n FROM student WHERE status='enrolled'"),
        "在职教师": _count("SELECT COUNT(*) n FROM teacher WHERE status='active'"),
        "开放课程": _count("SELECT COUNT(*) n FROM course WHERE status='active'"),
        "教学班": _count("SELECT COUNT(*) n FROM course_offering"),
        "当前选课": _count("SELECT COUNT(*) n FROM enrollment WHERE status='selected'"),
        "成绩日志": _count("SELECT COUNT(*) n FROM score_change_log"),
    }

    cols = st.columns(3)
    for idx, (label, val) in enumerate(stats.items()):
        with cols[idx % 3]:
            render_metric_card(label, val)

    left, right = st.columns([1.15, 0.85])

    with left:
        render_section_title("各班次选课情况", "按最近学期和已选人数排序。")
        rows = query(
            """
            SELECT course_name, teacher_name, selected_count,
                   max_capacity, semester_name, remaining_capacity
            FROM v_course_offering_detail
            ORDER BY semester_id DESC, selected_count DESC
            LIMIT 12
            """
        )
        if rows:
            df = pd.DataFrame(
                [
                    {
                        "学期": r["semester_name"],
                        "课程": r["course_name"],
                        "教师": r["teacher_name"],
                        "已选/上限": f"{r['selected_count']} / {r['max_capacity']}",
                        "剩余": r["remaining_capacity"],
                    }
                    for r in rows
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            render_empty_state("暂无班次数据", "创建教学班后会显示容量统计。")

    with right:
        render_section_title("各院系在籍学生人数")
        dept_rows = query(
            """
            SELECT d.dept_name, COUNT(s.student_id) cnt
            FROM department d
            LEFT JOIN major m ON d.dept_id = m.dept_id
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
        else:
            render_empty_state("暂无院系统计", "维护学生和专业数据后会生成统计。")

    render_section_title("最近成绩修改日志", "用于管理员审计成绩变更。")
    logs = query(
        """
        SELECT scl.changed_at, c.course_name, s.student_id, s.student_name,
               scl.old_score, scl.new_score, u.username AS changed_by, scl.reason
        FROM score_change_log scl
        JOIN enrollment e ON scl.enrollment_id = e.enrollment_id
        JOIN student s ON e.student_id = s.student_id
        JOIN course_offering co ON e.offering_id = co.offering_id
        JOIN course c ON co.course_id = c.course_id
        JOIN user_account u ON scl.changed_by_user_id = u.user_id
        ORDER BY scl.changed_at DESC
        LIMIT 10
        """
    )
    if logs:
        log_df = pd.DataFrame(
            [
                {
                    "时间": str(row["changed_at"]),
                    "课程": row["course_name"],
                    "学生": f"{row['student_id']} {row['student_name']}",
                    "原成绩": row["old_score"] if row["old_score"] is not None else "—",
                    "新成绩": row["new_score"],
                    "操作人": row["changed_by"],
                    "原因": row["reason"] or "—",
                }
                for row in logs
            ]
        )
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        render_empty_state("暂无成绩审计日志", "教师或管理员录入成绩后会自动产生记录。")
