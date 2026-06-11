import pandas as pd
import streamlit as st

from db.connection import query
from pages._guards import require_role
from services.course_service import get_active_semester, list_offerings
from services.teacher_service import get_teacher_info
from ui.components import (
    render_app_header,
    render_empty_state,
    render_metric_card,
    render_section_title,
)


def render() -> None:
    require_role("teacher")
    teacher_id = st.session_state.teacher_id
    info = get_teacher_info(teacher_id) or {}
    semester = get_active_semester()
    teacher_name = info.get("teacher_name") or st.session_state.username

    render_app_header(
        f"{teacher_name}，欢迎回来",
        "这里汇总本学期教学班、学生名单和成绩录入进度。",
    )

    offerings = list_offerings(
        semester_id=semester["semester_id"] if semester else None,
        teacher_id=teacher_id,
    )
    offering_ids = [o["offering_id"] for o in offerings]
    stats = {"student_count": 0, "pending_score": 0, "completed_score": 0}
    if offering_ids:
        rows = query(
            """
            SELECT
                SUM(CASE WHEN e.status <> 'dropped' THEN 1 ELSE 0 END) AS student_count,
                SUM(CASE WHEN e.final_score IS NULL AND e.status <> 'dropped' THEN 1 ELSE 0 END) AS pending_score,
                SUM(CASE WHEN e.final_score IS NOT NULL AND e.status = 'completed' THEN 1 ELSE 0 END) AS completed_score
            FROM enrollment e
            WHERE e.offering_id = ANY(%s)
            """,
            (offering_ids,),
        )
        if rows:
            stats = rows[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("本学期教学班", len(offerings), semester["semester_name"] if semester else "全部学期")
    with c2:
        render_metric_card("学生人数", int(stats.get("student_count") or 0), "未退课选课记录")
    with c3:
        render_metric_card("待录入成绩", int(stats.get("pending_score") or 0), "成绩为空的有效选课")
    with c4:
        render_metric_card("已完成录入", int(stats.get("completed_score") or 0), "状态为 completed 的成绩")

    render_section_title("我的教学班", "容量、已选人数和上课时间来自课程详情视图。")
    if not offerings:
        render_empty_state("暂无教学班", "当前学期还没有分配给你的教学班。")
        return

    df = pd.DataFrame(
        [
            {
                "班次ID": row["offering_id"],
                "课程": f"{row['course_id']} {row['course_name']}",
                "学期": row["semester_name"],
                "时间": row.get("schedule_text") or "-",
                "教室": f"{row.get('building') or ''}{row.get('room_no') or ''}".strip() or "待定",
                "已选/容量": f"{row['selected_count']} / {row['max_capacity']}",
                "状态": row["status"],
            }
            for row in offerings
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    render_section_title("最近成绩修改", "由成绩审计日志表记录。")
    recent = query(
        """
        SELECT scl.changed_at, c.course_name, s.student_id, s.student_name,
               scl.old_score, scl.new_score, scl.reason
        FROM score_change_log scl
        JOIN enrollment e ON scl.enrollment_id = e.enrollment_id
        JOIN student s ON e.student_id = s.student_id
        JOIN course_offering co ON e.offering_id = co.offering_id
        JOIN course c ON co.course_id = c.course_id
        WHERE co.teacher_id=%s
        ORDER BY scl.changed_at DESC
        LIMIT 8
        """,
        (teacher_id,),
    )
    if recent:
        log_df = pd.DataFrame(
            [
                {
                    "时间": str(row["changed_at"]),
                    "课程": row["course_name"],
                    "学生": f"{row['student_id']} {row['student_name']}",
                    "原成绩": row["old_score"] if row["old_score"] is not None else "—",
                    "新成绩": row["new_score"],
                    "原因": row["reason"] or "—",
                }
                for row in recent
            ]
        )
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        render_empty_state("暂无成绩修改记录", "录入或修改成绩后，审计日志会显示在这里。")
