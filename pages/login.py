import streamlit as st
from services.auth_service import create_session, login
from utils.auth_cookie import set_auth_cookie
from utils.session_state import apply_login_state

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
                    token = create_session(user["user_id"])
                    apply_login_state(user, token)
                    set_auth_cookie(token)
                    st.success("登录成功，正在进入系统...")
                    st.stop()
                else:
                    st.error("用户名或密码错误，或账号已被禁用")

        st.divider()
        st.caption(
            "测试账号（密码均为 **123456**）：  \n"
            "`admin` 管理员 · `t_zhang` / `t_li` 教师 · `s_001` / `s_002` / `s_003` 学生"
        )
