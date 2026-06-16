import pandas as pd
import streamlit as st
from datetime import date

from db.connection import query
from pages._guards import require_role
from services.course_service import list_offerings, list_semesters
from services.score_service import (
    can_manage_offering_score,
    get_enrollments_for_offering,
    get_score_change_log,
    get_score_distribution,
    update_score,
)
from ui.components import (
    render_app_header,
    render_empty_state,
    render_error_message,
    render_filter_bar,
    render_metric_card,
    render_section_title,
    render_success_message,
)


def render() -> None:
    role = require_role("teacher", "admin")
    user_id = st.session_state.user_id
    teacher_id = st.session_state.get("teacher_id")

    render_app_header(
        "成绩管理",
        "录入成绩时会在数据库事务中写入成绩审计日志。",
    )

    semesters = list_semesters()
    if not semesters:
        render_empty_state("暂无学期数据", "请先由管理员创建学期。")
        return

    sem_map = {s["semester_id"]: s["semester_name"] for s in semesters}
    c1, c2 = st.columns([1, 2])
    sel_sem = c1.selectbox(
        "学期",
        options=list(sem_map.keys()),
        format_func=lambda x: sem_map[x],
    )

    offerings = list_offerings(
        semester_id=sel_sem,
        teacher_id=None if role == "admin" else teacher_id,
    )
    if not offerings:
        render_empty_state("该学期暂无开课班次", "切换学期后再查看成绩。")
        return

    off_map = {
        o["offering_id"]: f"{o['course_id']} {o['course_name']} · {o['teacher_name']}"
        for o in offerings
    }
    sel_oid = c2.selectbox(
        "教学班",
        options=list(off_map.keys()),
        format_func=lambda x: off_map[x],
    )
    selected_offering = next(o for o in offerings if o["offering_id"] == sel_oid)
    students = get_enrollments_for_offering(sel_oid)
    pending = [s for s in students if s["final_score"] is None and s["status"] != "dropped"]
    completed = [s for s in students if s["final_score"] is not None and s["status"] == "completed"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("选课学生", len(students), "不含已删除记录")
    with m2:
        render_metric_card("待录成绩", len(pending), "成绩为空")
    with m3:
        render_metric_card("已录成绩", len(completed), "completed 状态")
    with m4:
        render_metric_card("容量", f"{selected_offering['selected_count']} / {selected_offering['max_capacity']}", "已选 / 上限")

    tab_entry, tab_log = st.tabs(["成绩录入", "审计日志"])

    with tab_entry:
        allowed, msg = can_manage_offering_score(sel_oid, role, teacher_id)
        if not allowed:
            render_error_message(msg)
            return

        if not students:
            render_empty_state("该班次暂无学生", "学生选课后会出现在名单中。")
            return

        render_section_title("学生名单", "修改成绩后请填写原因并确认保存。")
        df = pd.DataFrame(
            [
                {
                    "enrollment_id": s["enrollment_id"],
                    "学号": s["student_id"],
                    "姓名": s["student_name"],
                    "班级": s["class_name"] or "-",
                    "状态": s["status"],
                    "绩点": float(s["gpa_point"]) if s["gpa_point"] is not None else None,
                    "成绩（0-100）": float(s["final_score"]) if s["final_score"] is not None else None,
                }
                for s in students
            ]
        ).set_index("enrollment_id")

        edited = st.data_editor(
            df,
            column_config={
                "学号": st.column_config.TextColumn(disabled=True),
                "姓名": st.column_config.TextColumn(disabled=True),
                "班级": st.column_config.TextColumn(disabled=True),
                "状态": st.column_config.TextColumn(disabled=True),
                "绩点": st.column_config.NumberColumn(disabled=True, format="%.2f"),
                "成绩（0-100）": st.column_config.NumberColumn(
                    min_value=0.0, max_value=100.0, step=0.5, format="%.1f"
                ),
            },
            use_container_width=True,
        )

        reason = st.text_input("修改原因", placeholder="如：期末成绩录入 / 更正笔误")
        confirmed = st.checkbox("我确认保存后将写入成绩审计日志")
        if st.button("保存成绩", type="primary", disabled=not confirmed):
            saved, errors = 0, []
            for eid, row in edited.iterrows():
                score_val = row["成绩（0-100）"]
                if score_val is not None:
                    ok, emsg = update_score(
                        int(eid),
                        float(score_val),
                        user_id,
                        reason,
                        role=role,
                        teacher_id=teacher_id,
                    )
                    if ok:
                        saved += 1
                    else:
                        errors.append(f"{row['学号']} {row['姓名']}：{emsg}")
            if saved:
                render_success_message(f"已保存 {saved} 条成绩。")
            if errors:
                render_error_message("；".join(errors))
            if saved:
                st.rerun()

        render_section_title("成绩分布", "保存成绩后按分数段自动汇总。")
        dist = get_score_distribution(sel_oid)
        if dist:
            dist_df = pd.DataFrame(list(dist.items()), columns=["分数段", "人数"])
            st.bar_chart(dist_df.set_index("分数段"))
        else:
            render_empty_state("暂无成绩分布", "当前班次还没有可统计的成绩。")

    with tab_log:
        render_section_title("成绩修改审计日志", "日志由数据库触发器自动写入。")
        with render_filter_bar("日志筛选", "可按课程、教师、学生和时间范围检索审计记录。"):
            if role == "admin":
                teachers = query(
                    "SELECT teacher_id, teacher_name FROM teacher WHERE status='active' ORDER BY teacher_id"
                )
                teacher_options = [""] + [t["teacher_id"] for t in teachers]
                teacher_map = {t["teacher_id"]: f"{t['teacher_id']} {t['teacher_name']}" for t in teachers}
            else:
                teacher_options = [teacher_id]
                teacher_map = {teacher_id: teacher_id}

            f1, f2, f3, f4 = st.columns([1.1, 1.1, 1.1, 1.1])
            filter_teacher = f1.selectbox(
                "教师",
                teacher_options,
                format_func=lambda value: "全部教师" if value == "" else teacher_map.get(value, value),
                disabled=role != "admin",
            )
            filter_course = f2.text_input("课程", placeholder="课程号 / 课程名")
            filter_student = f3.text_input("学生", placeholder="学号 / 姓名")
            filter_limit = f4.number_input("显示条数", 10, 500, 100, 10)
            d0, d1, d2 = st.columns([0.9, 1, 1])
            use_date = d0.checkbox("按日期筛选", key="score_log_use_date")
            date_from = d1.date_input("开始日期", value=date.today(), disabled=not use_date)
            date_to = d2.date_input("结束日期", value=date.today(), disabled=not use_date)

        logs = get_score_change_log(
            offering_id=None if role == "admin" else sel_oid,
            semester_id=sel_sem,
            teacher_id=(filter_teacher or None) if role == "admin" else teacher_id,
            course_keyword=filter_course.strip() or None,
            student_keyword=filter_student.strip() or None,
            date_from=date_from if use_date else None,
            date_to=date_to if use_date else None,
            limit=int(filter_limit),
        )
        if not logs:
            render_empty_state("暂无修改日志", "成绩首次录入或修改后会产生审计记录。")
        else:
            log_df = pd.DataFrame(
                [
                    {
                        "时间": str(lg["changed_at"]),
                        "学期": lg["semester_name"],
                        "课程": lg["course_name"],
                        "教师": lg["teacher_name"],
                        "学号": lg["student_id"],
                        "姓名": lg["student_name"],
                        "原成绩": lg["old_score"] if lg["old_score"] is not None else "—",
                        "新成绩": lg["new_score"],
                        "操作人": lg["changed_by"],
                        "原因": lg["reason"] or "—",
                    }
                    for lg in logs
                ]
            )
            st.dataframe(log_df, use_container_width=True, hide_index=True)
