"""
pages/login.py —— 登录页
"""
import streamlit as st
from services.auth_service import login, get_student_id, get_teacher_id


def render() -> None:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("📚 选课管理系统")
        st.subheader("用户登录")

        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入登录名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submitted = st.form_submit_button("登 录", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("用户名和密码不能为空")
            else:
                user = login(username, password)
                if user:
                    st.session_state.logged_in  = True
                    st.session_state.user_id    = user["user_id"]
                    st.session_state.username   = user["username"]
                    st.session_state.role       = user["role"]
                    if user["role"] == "student":
                        st.session_state.student_id = get_student_id(user["user_id"])
                    elif user["role"] == "teacher":
                        st.session_state.teacher_id = get_teacher_id(user["user_id"])
                    st.rerun()
                else:
                    st.error("用户名或密码错误，或账号已被禁用")

        st.divider()
        st.caption(
            "测试账号（密码均为 **123456**）：  \n"
            "`admin` 管理员 · `t_zhang` / `t_li` 教师 · `s_001` / `s_002` / `s_003` 学生"
        )
