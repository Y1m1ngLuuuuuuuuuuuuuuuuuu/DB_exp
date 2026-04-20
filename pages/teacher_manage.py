import streamlit as st
import pandas as pd
from pages._guards import require_role
from db.connection import query
from services.teacher_service import list_teachers, create_teacher, update_teacher, delete_teacher

_GENDER_LABEL  = {"M": "男", "F": "女", "O": "其他"}
_STATUS_OPTIONS = ["active", "retired", "leave"]
_STATUS_LABEL   = {"active": "在职", "retired": "退休", "leave": "请假"}
_TITLE_OPTIONS  = ["教授", "副教授", "讲师", "助教", "其他"]

def render() -> None:
    require_role("admin")
    st.header("教师信息维护")

    tab_list, tab_add = st.tabs(["教师列表", "新增教师"])

    with tab_list:
        kw = st.text_input("搜索", placeholder="教师号 / 姓名")
        teachers = list_teachers(keyword=kw or None)

        if not teachers:
            st.info("无匹配教师")
            return

        df = pd.DataFrame([
            {
                "教师号": t["teacher_id"],
                "姓名":   t["teacher_name"],
                "性别":   _GENDER_LABEL.get(t.get("gender"), "-"),
                "职称":   t["title"] or "-",
                "院系":   t["dept_name"] or "-",
                "邮箱":   t["email"] or "-",
                "账号":   t["username"],
                "状态":   _STATUS_LABEL.get(t["status"], t["status"]),
            }
            for t in teachers
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("编辑教师信息")
        tids = [t["teacher_id"] for t in teachers]
        sel_tid = st.selectbox(
            "选择教师",
            tids,
            format_func=lambda x: next(
                f"{t['teacher_id']} {t['teacher_name']}" for t in teachers if t["teacher_id"] == x
            ),
        )
        sel = next(t for t in teachers if t["teacher_id"] == sel_tid)

        depts = query("SELECT dept_id, dept_name FROM department")
        dept_opts = {d["dept_id"]: d["dept_name"] for d in depts}
        dept_keys = list(dept_opts.keys())

        with st.form("edit_teacher"):
            col1, col2 = st.columns(2)
            new_name   = col1.text_input("姓名", value=sel["teacher_name"])
            new_gender = col2.selectbox(
                "性别", ["M", "F", "O"],
                index=["M", "F", "O"].index(sel.get("gender") or "M"),
                format_func=lambda x: _GENDER_LABEL[x],
            )
            col3, col4 = st.columns(2)
            cur_dept   = sel.get("dept_id") or (dept_keys[0] if dept_keys else None)
            new_dept   = col3.selectbox(
                "院系", dept_keys,
                index=dept_keys.index(cur_dept) if cur_dept in dept_keys else 0,
                format_func=lambda x: dept_opts[x],
            ) if dept_keys else None
            new_title  = col4.selectbox(
                "职称", _TITLE_OPTIONS,
                index=_TITLE_OPTIONS.index(sel["title"]) if sel.get("title") in _TITLE_OPTIONS else len(_TITLE_OPTIONS) - 1,
            )
            col5, col6 = st.columns(2)
            new_phone  = col5.text_input("电话", value=sel.get("phone") or "")
            new_email  = col6.text_input("邮箱", value=sel.get("email") or "")
            new_status = st.selectbox(
                "状态", _STATUS_OPTIONS,
                index=_STATUS_OPTIONS.index(sel["status"]) if sel["status"] in _STATUS_OPTIONS else 0,
                format_func=lambda x: _STATUS_LABEL[x],
            )

            c_save, c_del = st.columns(2)
            if c_save.form_submit_button("保存修改", type="primary"):
                ok, msg = update_teacher(sel_tid, {
                    "teacher_name": new_name, "gender": new_gender,
                    "dept_id": new_dept, "title": new_title,
                    "phone": new_phone, "email": new_email, "status": new_status,
                })
                st.success("保存成功！") if ok else st.error(f"保存失败：{msg}")
                if ok:
                    st.rerun()

            if c_del.form_submit_button("删除教师", type="secondary"):
                ok, msg = delete_teacher(sel_tid)
                st.success("删除成功！") if ok else st.error(f"删除失败：{msg}")
                if ok:
                    st.rerun()

    with tab_add:
        depts = query("SELECT dept_id, dept_name FROM department ORDER BY dept_id")
        dept_opts = {d["dept_id"]: d["dept_name"] for d in depts}

        with st.form("add_teacher"):
            col1, col2 = st.columns(2)
            teacher_id   = col1.text_input("教师号 *")
            teacher_name = col2.text_input("姓名 *")
            col3, col4   = st.columns(2)
            username     = col3.text_input("登录名 *")
            password     = col4.text_input("初始密码", value="123456", type="password")
            col5, col6   = st.columns(2)
            gender       = col5.selectbox("性别", ["M", "F", "O"], format_func=lambda x: _GENDER_LABEL[x])
            title        = col6.selectbox("职称", _TITLE_OPTIONS)
            col7, col8   = st.columns(2)
            dept_id      = col7.selectbox("所属院系", list(dept_opts.keys()), format_func=lambda x: dept_opts[x])
            phone        = col8.text_input("电话")
            email        = st.text_input("邮箱")

            if st.form_submit_button("添加教师", type="primary"):
                if not teacher_id.strip() or not teacher_name.strip() or not username.strip():
                    st.error("教师号、姓名、登录名不能为空")
                else:
                    ok, msg = create_teacher({
                        "teacher_id": teacher_id.strip(), "teacher_name": teacher_name.strip(),
                        "username": username.strip(), "password": password,
                        "gender": gender, "dept_id": dept_id,
                        "title": title, "phone": phone, "email": email,
                    })
                    st.success("教师添加成功！") if ok else st.error(f"添加失败：{msg}")
                    if ok:
                        st.rerun()
