import streamlit as st
from pages._guards import require_role
from services.course_service import (
    get_active_semester,
    list_offerings_for_student,
    list_enrolled_offerings,
)
from services.selection_service import enroll, drop

_TYPE_LABEL = {"required": "必修", "elective": "选修", "public": "公共"}
_STATUS_LABEL = {"selected": "已选", "dropped": "已退课", "completed": "已结课"}

def render() -> None:
    require_role("student")
    student_id = st.session_state.student_id

    semester = get_active_semester()
    if not semester:
        st.warning("当前没有开放的学期数据")
        return

    st.header(f"学生选课  ·  {semester['semester_name']}")
    if semester.get("status") != "open":
        st.info("当前学期未处于开放选课状态，以下仅供查看。")
    elif semester.get("selection_start") and semester.get("selection_end"):
        st.caption(
            f"选课时间：{semester['selection_start']} 至 {semester['selection_end']}"
        )

    tab_avail, tab_enrolled = st.tabs(["可选课程", "已选课程"])

    with tab_avail:
        available = list_offerings_for_student(student_id, semester["semester_id"])
        if not available:
            st.info("当前学期暂无可选课程（或已全部选完）")
        for row in available:
            loc = f"{row['building']}{row['room_no']}" if row.get("building") else "待定"
            title = (
                f"**{row['course_id']}** {row['course_name']}"
                f"  ·  {row['teacher_name']}"
                f"  ·  {row.get('schedule_text') or '时间待定'}"
            )
            with st.expander(title):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("学分",     row["credit"])
                c2.metric("课程类型", _TYPE_LABEL.get(row["course_type"], row["course_type"]))
                c3.metric("剩余名额", row["seats_left"])
                c4.metric("上课地点", loc)

                if row["seats_left"] > 0:
                    if st.button("选课", key=f"enroll_{row['offering_id']}", type="primary"):
                        ok, msg = enroll(student_id, row["offering_id"])
                        st.success("选课成功！") if ok else st.error(f"选课失败：{msg}")
                        if ok:
                            st.rerun()
                else:
                    st.warning("名额已满")

    with tab_enrolled:
        enrolled = list_enrolled_offerings(student_id, semester["semester_id"])
        if not enrolled:
            st.info("本学期尚未选择任何课程")
        for row in enrolled:
            status = _STATUS_LABEL.get(row["enroll_status"], row["enroll_status"])
            title = (
                f"**{row['course_id']}** {row['course_name']}"
                f"  ·  {row['teacher_name']}"
                f"  ·  [{status}]"
            )
            with st.expander(title):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("学分",   row["credit"])
                c2.metric("类型",   _TYPE_LABEL.get(row["course_type"], row["course_type"]))
                c3.metric("成绩",   row["final_score"] if row["final_score"] is not None else "待录入")
                c4.metric("绩点",   row["gpa_point"]   if row["gpa_point"]   is not None else "-")

                if row["enroll_status"] == "selected":
                    if st.button("退课", key=f"drop_{row['enrollment_id']}", type="secondary"):
                        ok, msg = drop(row["enrollment_id"], student_id)
                        st.success("退课成功！") if ok else st.error(f"退课失败：{msg}")
                        if ok:
                            st.rerun()
