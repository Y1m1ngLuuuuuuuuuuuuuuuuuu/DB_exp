"""
pages/course_manage.py —— 课程信息维护（管理员）
"""
import streamlit as st
import pandas as pd
from pages._guards import require_role
from db.connection import query
from services.course_service import (
    list_courses,
    create_course,
    update_course,
    delete_course,
    list_offerings,
    create_offering,
    update_offering,
    delete_offering,
    list_semesters,
    list_classrooms,
)

_TYPE_LABEL = {"required": "必修", "elective": "选修", "public": "公共"}
_TYPE_OPTIONS = ["required", "elective", "public"]
_OFFERING_STATUS_OPTIONS = ["open", "closed", "cancelled"]
_OFFERING_STATUS_LABEL = {"open": "开放", "closed": "关闭", "cancelled": "取消"}


def render() -> None:
    require_role("admin")
    st.header("课程与开课安排维护")

    tab_list, tab_add, tab_offering = st.tabs(["课程列表", "新增课程", "开课安排"])

    # ── 课程列表 ─────────────────────────────────────────────
    with tab_list:
        kw = st.text_input("搜索课程", placeholder="课程号 / 课程名")
        courses = list_courses(keyword=kw or None, include_inactive=True)

        if not courses:
            st.info("无匹配课程")
        else:
            df = pd.DataFrame([
                {
                    "课程号":   c["course_id"],
                    "课程名":   c["course_name"],
                    "类型":     _TYPE_LABEL.get(c["course_type"], c["course_type"]),
                    "学分":     float(c["credit"]),
                    "学时":     c["total_hours"],
                    "开课院系": c["dept_name"] or "-",
                    "状态":     c["status"],
                }
                for c in courses
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 快速修改状态
            st.subheader("修改课程信息")
            course_ids = [c["course_id"] for c in courses]
            sel_cid = st.selectbox("选择课程", course_ids,
                                   format_func=lambda x: next(
                                       f"{c['course_id']} {c['course_name']}"
                                       for c in courses if c["course_id"] == x
                                   ))
            sel_course = next(c for c in courses if c["course_id"] == sel_cid)

            depts = query("SELECT dept_id, dept_name FROM department")
            dept_opts = {d["dept_id"]: d["dept_name"] for d in depts}

            with st.form("edit_course"):
                col1, col2 = st.columns(2)
                new_name = col1.text_input("课程名", value=sel_course["course_name"])
                new_type = col2.selectbox(
                    "类型", _TYPE_OPTIONS,
                    index=_TYPE_OPTIONS.index(sel_course["course_type"]),
                    format_func=lambda x: _TYPE_LABEL[x],
                )
                col3, col4 = st.columns(2)
                new_credit = col3.number_input("学分", 0.5, 10.0, float(sel_course["credit"]), 0.5)
                new_hours  = col4.number_input("学时", 8, 200, int(sel_course["total_hours"]), 8)
                dept_keys  = list(dept_opts.keys())
                cur_dept   = sel_course.get("dept_id") or (dept_keys[0] if dept_keys else None)
                new_dept   = st.selectbox(
                    "开课院系", dept_keys,
                    index=dept_keys.index(cur_dept) if cur_dept in dept_keys else 0,
                    format_func=lambda x: dept_opts[x],
                ) if dept_keys else None
                new_desc   = st.text_area("简介", value=sel_course.get("description") or "")
                new_status = st.selectbox(
                    "状态", ["active", "inactive"],
                    index=0 if sel_course["status"] == "active" else 1,
                )
                if st.form_submit_button("保存修改", type="primary"):
                    ok, msg = update_course(sel_cid, {
                        "course_name": new_name, "course_type": new_type,
                        "credit": new_credit, "total_hours": new_hours,
                        "dept_id": new_dept, "description": new_desc,
                        "status": new_status,
                    })
                    st.success("保存成功！") if ok else st.error(f"保存失败：{msg}")
                    if ok:
                        st.rerun()

            st.divider()
            st.markdown("**删除课程**（已有开课安排的课程无法删除，请先删除相关班次）")
            if st.button("删除该课程", type="secondary"):
                ok, msg = delete_course(sel_cid)
                st.success("删除成功！") if ok else st.error(f"删除失败：{msg}")
                if ok:
                    st.rerun()

    # ── 新增课程 ─────────────────────────────────────────────
    with tab_add:
        depts = query("SELECT dept_id, dept_name FROM department")
        dept_opts = {d["dept_id"]: d["dept_name"] for d in depts}

        with st.form("add_course"):
            col1, col2 = st.columns(2)
            course_id   = col1.text_input("课程号 *")
            course_name = col2.text_input("课程名 *")
            col3, col4  = st.columns(2)
            course_type = col3.selectbox("课程类型", _TYPE_OPTIONS, format_func=lambda x: _TYPE_LABEL[x])
            dept_id     = col4.selectbox("开课院系", list(dept_opts.keys()), format_func=lambda x: dept_opts[x])
            col5, col6  = st.columns(2)
            credit      = col5.number_input("学分", 0.5, 10.0, 3.0, 0.5)
            total_hours = col6.number_input("总学时", 8, 200, 48, 8)
            description = st.text_area("课程简介")

            if st.form_submit_button("添加课程", type="primary"):
                if not course_id.strip() or not course_name.strip():
                    st.error("课程号和课程名不能为空")
                else:
                    ok, msg = create_course({
                        "course_id": course_id.strip(), "course_name": course_name.strip(),
                        "course_type": course_type, "credit": credit,
                        "total_hours": int(total_hours), "dept_id": dept_id,
                        "description": description,
                    })
                    st.success("课程添加成功！") if ok else st.error(f"添加失败：{msg}")
                    if ok:
                        st.rerun()

    # ── 开课安排维护 ──────────────────────────────────────────
    with tab_offering:
        semesters = list_semesters()
        semester_map = {s["semester_id"]: s["semester_name"] for s in semesters}
        courses = list_courses(include_inactive=True)
        teachers = query(
            "SELECT teacher_id, teacher_name, dept_id FROM teacher WHERE status='active' ORDER BY teacher_id"
        )
        classrooms = list_classrooms()

        if not semesters or not courses or not teachers:
            st.warning("学期、课程或教师基础数据不完整，暂时无法维护开课安排。")
            return

        course_map = {c["course_id"]: f"{c['course_id']} {c['course_name']}" for c in courses}
        teacher_map = {t["teacher_id"]: f"{t['teacher_id']} {t['teacher_name']}" for t in teachers}
        classroom_map = {
            c["classroom_id"]: f"{c['classroom_id']} {c['building']}-{c['room_no']} / {c['capacity']}人"
            for c in classrooms
        }
        classroom_options = [""] + list(classroom_map.keys())

        st.subheader("当前开课班次")
        semester_filter = st.selectbox(
            "选择学期",
            options=list(semester_map.keys()),
            format_func=lambda x: semester_map[x],
            key="offering_semester_filter",
        )
        offerings = list_offerings(semester_id=semester_filter)

        if offerings:
            offering_df = pd.DataFrame([
                {
                    "班次ID": o["offering_id"],
                    "学期": o["semester_name"],
                    "课程": f"{o['course_id']} {o['course_name']}",
                    "教师": o["teacher_name"],
                    "教室": f"{o['building']}-{o['room_no']}" if o.get("building") else "待定",
                    "容量": o["max_capacity"],
                    "已选": o["selected_count"],
                    "状态": _OFFERING_STATUS_LABEL.get(o["status"], o["status"]),
                    "时间": o.get("schedule_text") or "-",
                }
                for o in offerings
            ])
            st.dataframe(offering_df, use_container_width=True, hide_index=True)
        else:
            st.info("该学期暂无开课安排")

        st.divider()
        subtab_edit, subtab_add = st.tabs(["编辑班次", "新增班次"])

        with subtab_edit:
            if not offerings:
                st.info("当前没有可编辑的开课班次")
            else:
                offering_ids = [o["offering_id"] for o in offerings]
                selected_oid = st.selectbox(
                    "选择班次",
                    options=offering_ids,
                    format_func=lambda x: next(
                        f"{o['offering_id']} · {o['course_id']} {o['course_name']} · {o['teacher_name']}"
                        for o in offerings if o["offering_id"] == x
                    ),
                )
                selected = next(o for o in offerings if o["offering_id"] == selected_oid)
                current_classroom = ""
                if selected.get("building") and selected.get("room_no"):
                    current_classroom = next(
                        (
                            c["classroom_id"] for c in classrooms
                            if c["building"] == selected["building"] and c["room_no"] == selected["room_no"]
                        ),
                        "",
                    )

                with st.form("edit_offering_form"):
                    c1, c2 = st.columns(2)
                    st.text_input(
                        "课程",
                        value=f"{selected['course_id']} {selected['course_name']}",
                        disabled=True,
                    )
                    st.text_input("学期", value=selected["semester_name"], disabled=True)
                    new_teacher = c1.selectbox(
                        "任课教师",
                        options=list(teacher_map.keys()),
                        index=list(teacher_map.keys()).index(selected["teacher_id"]),
                        format_func=lambda x: teacher_map[x],
                    )
                    new_status = c2.selectbox(
                        "班次状态",
                        options=_OFFERING_STATUS_OPTIONS,
                        index=_OFFERING_STATUS_OPTIONS.index(selected["status"]),
                        format_func=lambda x: _OFFERING_STATUS_LABEL[x],
                    )
                    c3, c4 = st.columns(2)
                    new_classroom = c3.selectbox(
                        "教室",
                        options=classroom_options,
                        index=classroom_options.index(current_classroom) if current_classroom in classroom_options else 0,
                        format_func=lambda x: "待定" if x == "" else classroom_map[x],
                    )
                    new_capacity = c4.number_input(
                        "容量",
                        min_value=max(int(selected["selected_count"]), 1),
                        max_value=200,
                        value=int(selected["max_capacity"]),
                        step=5,
                    )
                    new_schedule = st.text_input(
                        "上课时间",
                        value=selected.get("schedule_text") or "",
                        placeholder="例如：周二 3-4 节 / 周四 5-6 节",
                    )

                    save_col, delete_col = st.columns(2)
                    if save_col.form_submit_button("保存班次修改", type="primary"):
                        ok, msg = update_offering(
                            int(selected_oid),
                            {
                                "teacher_id": new_teacher,
                                "classroom_id": new_classroom or None,
                                "max_capacity": int(new_capacity),
                                "schedule_text": new_schedule.strip(),
                                "status": new_status,
                            },
                        )
                        st.success("班次修改成功！") if ok else st.error(f"修改失败：{msg}")
                        if ok:
                            st.rerun()

                    if delete_col.form_submit_button("删除班次", type="secondary"):
                        ok, msg = delete_offering(int(selected_oid))
                        st.success("班次删除成功！") if ok else st.error(f"删除失败：{msg}")
                        if ok:
                            st.rerun()

        with subtab_add:
            with st.form("add_offering_form"):
                c1, c2 = st.columns(2)
                semester_id = c1.selectbox(
                    "学期 *",
                    options=list(semester_map.keys()),
                    format_func=lambda x: semester_map[x],
                )
                course_id = c2.selectbox(
                    "课程 *",
                    options=list(course_map.keys()),
                    format_func=lambda x: course_map[x],
                )
                c3, c4 = st.columns(2)
                teacher_id = c3.selectbox(
                    "任课教师 *",
                    options=list(teacher_map.keys()),
                    format_func=lambda x: teacher_map[x],
                )
                classroom_id = c4.selectbox(
                    "教室",
                    options=classroom_options,
                    format_func=lambda x: "待定" if x == "" else classroom_map[x],
                )
                c5, c6 = st.columns(2)
                max_capacity = c5.number_input("容量", min_value=1, max_value=200, value=40, step=5)
                status = c6.selectbox(
                    "班次状态",
                    options=_OFFERING_STATUS_OPTIONS,
                    format_func=lambda x: _OFFERING_STATUS_LABEL[x],
                )
                schedule_text = st.text_input(
                    "上课时间",
                    placeholder="例如：周三 1-2 节 / 周五 3-4 节",
                )

                if st.form_submit_button("新增班次", type="primary"):
                    ok, msg = create_offering(
                        {
                            "semester_id": semester_id,
                            "course_id": course_id,
                            "teacher_id": teacher_id,
                            "classroom_id": classroom_id or None,
                            "max_capacity": int(max_capacity),
                            "schedule_text": schedule_text.strip(),
                            "status": status,
                        }
                    )
                    st.success("开课班次创建成功！") if ok else st.error(f"创建失败：{msg}")
                    if ok:
                        st.rerun()
