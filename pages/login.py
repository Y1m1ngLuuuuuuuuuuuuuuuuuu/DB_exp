import streamlit as st

from services.auth_service import create_session, login
from ui.theme import inject_global_css
from utils.auth_cookie import set_auth_cookie
from utils.session_state import apply_login_state


def render() -> None:
    inject_global_css()
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stAppViewContainer"] { margin-left: 0; }
        .block-container { max-width: 1180px; }
        </style>
        <div style='height:2vh'></div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([0.85, 1.7, 0.85])
    with center:
        st.markdown(
            """
            <section class="app-hero" style="text-align:left;margin-bottom:1rem;">
                <h1 style="font-size:2.25rem;">学生选课成绩管理系统</h1>
                <p>Course Selection & Academic Records</p>
            </section>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="app-card" style="padding:1.35rem 1.35rem .35rem 1.35rem;">
                <div class="app-card-title">登录</div>
                <div class="app-muted">使用学号、教师号或管理员编号进入系统。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("账号", placeholder="例如 A001 / T001 / 20240001")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submitted = st.form_submit_button("登录系统", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("账号和密码不能为空。")
            else:
                user = login(username.strip(), password)
                if user:
                    token = create_session(user["user_id"])
                    apply_login_state(user, token)
                    set_auth_cookie(token)
                    st.success("登录成功，正在进入系统...")
                    st.stop()
                else:
                    st.error("账号或密码错误，请检查后重试。")

        st.markdown(
            """
            <div class="app-empty">
                <strong>演示账号</strong>
                学生使用学号登录，教师使用教师号登录，管理员使用管理员编号登录。
                初始密码仅保存在本地凭据文件中，页面不会读取或展示明文密码。
            </div>
            """,
            unsafe_allow_html=True,
        )
