import streamlit as st
import pandas as pd
from pages._guards import require_role
from services.course_service import list_semesters, list_offerings
from services.score_service import (
    can_manage_offering_score,
    get_enrollments_for_offering,
    update_score,
    get_score_distribution,
    get_score_change_log,
)

def render() -> None:
    role       = require_role("teacher", "admin")
    user_id    = st.session_state.user_id
    teacher_id = st.session_state.get("teacher_id")

    st.header("成绩管理")

    tab_entry, tab_log = st.tabs(["成绩录入", "修改日志"])

    semesters = list_semesters()
    if not semesters:
        st.info("暂无学期数据")
        return

    sem_map = {s["semester_id"]: s["semester_name"] for s in semesters}
    sel_sem = st.selectbox(
        "学期",
        options=list(sem_map.keys()),
        format_func=lambda x: sem_map[x],
    )

    offerings = list_offerings(
        semester_id=sel_sem,
        teacher_id=None if role == "admin" else teacher_id,
    )
    if not offerings:
        st.info("该学期暂无开课班次")
        return

    off_map = {
        o["offering_id"]: f"{o['course_id']} {o['course_name']} — {o['teacher_name']}"
        for o in offerings
    }
    sel_oid = st.selectbox(
        "课程班次",
        options=list(off_map.keys()),
        format_func=lambda x: off_map[x],
    )

    with tab_entry:
        allowed, msg = can_manage_offering_score(sel_oid, role, teacher_id)
        if not allowed:
            st.error(msg)
        else:
            students = get_enrollments_for_offering(sel_oid)
            if not students:
                st.info("该班次暂无选课学生")
            else:
                st.subheader(f"学生名单  ·  共 {len(students)} 人")

                df = pd.DataFrame([
                    {
                        "enrollment_id": s["enrollment_id"],
                        "学号":           s["student_id"],
                        "姓名":           s["student_name"],
                        "班级":           s["class_name"] or "-",
                        "成绩（0-100）":  float(s["final_score"]) if s["final_score"] is not None else None,
                    }
                    for s in students
                ]).set_index("enrollment_id")

                edited = st.data_editor(
                    df,
                    column_config={
                        "学号":          st.column_config.TextColumn(disabled=True),
                        "姓名":          st.column_config.TextColumn(disabled=True),
                        "班级":          st.column_config.TextColumn(disabled=True),
                        "成绩（0-100）": st.column_config.NumberColumn(
                            min_value=0.0, max_value=100.0, step=0.5, format="%.1f"
                        ),
                    },
                    use_container_width=True,
                )

                reason = st.text_input("修改原因（可选）", placeholder="如：期末成绩录入 / 更正笔误")

                if st.button("保存所有成绩", type="primary"):
                    saved, errors = 0, []
                    for eid, row in edited.iterrows():
                        score_val = row["成绩（0-100）"]
                        if score_val is not None:
                            ok, emsg = update_score(
                                int(eid), float(score_val), user_id, reason,
                                role=role, teacher_id=teacher_id,
                            )
                            if ok:
                                saved += 1
                            else:
                                errors.append(f"enrollment_id={eid}: {emsg}")
                    if saved:
                        st.success(f"已保存 {saved} 条成绩")
                    if errors:
                        st.error("\n".join(errors))
                    if saved:
                        st.rerun()

                dist = get_score_distribution(sel_oid)
                if dist:
                    st.divider()
                    st.subheader("成绩分布")
                    dist_df = pd.DataFrame(list(dist.items()), columns=["分数段", "人数"])
                    st.bar_chart(dist_df.set_index("分数段"))

    with tab_log:
        logs = get_score_change_log(offering_id=sel_oid)
        if not logs:
            st.info("该班次暂无成绩修改记录")
        else:
            log_df = pd.DataFrame([
                {
                    "时间":     str(lg["changed_at"]),
                    "学号":     lg["student_id"],
                    "姓名":     lg["student_name"],
                    "原成绩":   lg["old_score"] if lg["old_score"] is not None else "—",
                    "新成绩":   lg["new_score"],
                    "操作人":   lg["changed_by"],
                    "原因":     lg["reason"] or "—",
                }
                for lg in logs
            ])
            st.dataframe(log_df, use_container_width=True, hide_index=True)
