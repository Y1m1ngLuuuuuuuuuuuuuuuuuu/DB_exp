"""
pages/student_manage.py —— 学生信息维护（管理员）
"""
import streamlit as st
import pandas as pd
from pages._guards import require_role
from db.connection import query
from services.student_service import list_students, create_student, update_student, delete_student

_GENDER_LABEL = {"M": "男", "F": "女", "O": "其他"}
_STATUS_OPTIONS = ["enrolled", "suspended", "graduated", "dropped"]
_STATUS_LABEL   = {"enrolled": "在籍", "suspended": "休学", "graduated": "已毕业", "dropped": "退学"}


def render() -> None:
    require_role("admin")
    st.header("学生信息维护")

    tab_list, tab_add = st.tabs(["学生列表", "新增学生"])

    # ── 学生列表 ─────────────────────────────────────────────
    with tab_list:
        kw = st.text_input("搜索", placeholder="学号 / 姓名")
        students = list_students(keyword=kw or None)

        if not students:
            st.info("无匹配学生")
            return

        df = pd.DataFrame([
            {
                "学号":   s["student_id"],
                "姓名":   s["student_name"],
                "性别":   _GENDER_LABEL.get(s.get("gender"), "-"),
                "入学年": s["enroll_year"],
                "班级":   s["class_name"] or "-",
                "专业":   s["major_name"] or "-",
                "院系":   s["dept_name"]  or "-",
                "邮箱":   s["email"]      or "-",
                "账号":   s["username"],
                "状态":   _STATUS_LABEL.get(s["status"], s["status"]),
            }
            for s in students
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 编辑 / 删除
        st.subheader("编辑学生信息")
        sids = [s["student_id"] for s in students]
        sel_sid = st.selectbox(
            "选择学生",
            sids,
            format_func=lambda x: next(
                f"{s['student_id']} {s['student_name']}" for s in students if s["student_id"] == x
            ),
        )
        sel = next(s for s in students if s["student_id"] == sel_sid)

        with st.form("edit_student"):
            col1, col2 = st.columns(2)
            new_name   = col1.text_input("姓名", value=sel["student_name"])
            new_gender = col2.selectbox(
                "性别", ["M", "F", "O"],
                index=["M", "F", "O"].index(sel.get("gender") or "M"),
                format_func=lambda x: _GENDER_LABEL[x],
            )
            col3, col4 = st.columns(2)
            new_class  = col3.text_input("班级", value=sel.get("class_name") or "")
            new_status = col4.selectbox(
                "学籍状态", _STATUS_OPTIONS,
                index=_STATUS_OPTIONS.index(sel["status"]) if sel["status"] in _STATUS_OPTIONS else 0,
                format_func=lambda x: _STATUS_LABEL[x],
            )
            col5, col6 = st.columns(2)
            new_phone  = col5.text_input("电话", value=sel.get("phone") or "")
            new_email  = col6.text_input("邮箱", value=sel.get("email") or "")

            c_save, c_del = st.columns(2)
            if c_save.form_submit_button("保存修改", type="primary"):
                ok, msg = update_student(sel_sid, {
                    "student_name": new_name, "gender": new_gender,
                    "class_name": new_class, "status": new_status,
                    "phone": new_phone, "email": new_email,
                })
                st.success("保存成功！") if ok else st.error(f"保存失败：{msg}")
                if ok:
                    st.rerun()

            if c_del.form_submit_button("删除学生", type="secondary"):
                ok, msg = delete_student(sel_sid)
                st.success("删除成功！") if ok else st.error(f"删除失败：{msg}")
                if ok:
                    st.rerun()

    # ── 新增学生 ─────────────────────────────────────────────
    with tab_add:
        majors = query("SELECT major_id, major_name FROM major ORDER BY major_id")
        major_opts = {m["major_id"]: m["major_name"] for m in majors}

        with st.form("add_student"):
            col1, col2 = st.columns(2)
            student_id   = col1.text_input("学号 *")
            student_name = col2.text_input("姓名 *")
            col3, col4   = st.columns(2)
            username     = col3.text_input("登录名 *")
            password     = col4.text_input("初始密码", value="123456", type="password")
            col5, col6   = st.columns(2)
            gender       = col5.selectbox("性别", ["M", "F", "O"], format_func=lambda x: _GENDER_LABEL[x])
            enroll_year  = col6.number_input("入学年份", 2000, 2030, 2025)
            col7, col8   = st.columns(2)
            major_id     = col7.selectbox("专业", list(major_opts.keys()), format_func=lambda x: major_opts[x])
            class_name   = col8.text_input("班级")
            col9, col10  = st.columns(2)
            phone        = col9.text_input("电话")
            email        = col10.text_input("邮箱")

            if st.form_submit_button("添加学生", type="primary"):
                if not student_id.strip() or not student_name.strip() or not username.strip():
                    st.error("学号、姓名、登录名不能为空")
                else:
                    ok, msg = create_student({
                        "student_id": student_id.strip(), "student_name": student_name.strip(),
                        "username": username.strip(), "password": password,
                        "gender": gender, "enroll_year": int(enroll_year),
                        "major_id": major_id, "class_name": class_name,
                        "phone": phone, "email": email,
                    })
                    st.success("学生添加成功！") if ok else st.error(f"添加失败：{msg}")
                    if ok:
                        st.rerun()
