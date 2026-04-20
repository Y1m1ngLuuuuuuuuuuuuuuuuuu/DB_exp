import importlib
import streamlit as st
from config import APP_TITLE, APP_ICON

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

_SESSION_DEFAULTS: dict = {
    "logged_in":  False,
    "user_id":    None,
    "username":   None,
    "role":       None,
    "student_id": None,
    "teacher_id": None,
}

for _k, _v in _SESSION_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if not st.session_state.logged_in:
    from pages.login import render as render_login
    render_login()
    st.stop()

role = st.session_state.role

_NAV: dict[str, dict[str, str]] = {
    "student": {
        "我的选课":   "pages.student_select",
        "我的成绩单": "pages.student_report",
    },
    "teacher": {
        "成绩管理":   "pages.score_manage",
    },
    "admin": {
        "管理员首页": "pages.admin_dashboard",
        "学期管理":   "pages.semester_manage",
        "开课安排":   "pages.offering_manage",
        "课程维护":   "pages.course_manage",
        "成绩管理":   "pages.score_manage",
        "学生维护":   "pages.student_manage",
        "教师维护":   "pages.teacher_manage",
    },
}

pages = _NAV.get(role, {})

with st.sidebar:
    st.title(APP_TITLE)
    st.caption(f"登录身份：**{st.session_state.username}**（{role}）")
    st.divider()

    if pages:
        choice = st.radio("导航", list(pages.keys()), label_visibility="collapsed")
    else:
        st.warning("该角色暂无可用页面")
        choice = None

    st.divider()
    if st.button("退出登录", use_container_width=True):
        logout()

if choice and choice in pages:
    try:
        mod = importlib.import_module(pages[choice])
        mod.render()
    except ModuleNotFoundError as exc:
        st.error(f"页面模块未找到：{exc}\n\n请确认 `{pages[choice]}.py` 已创建。")
    except AttributeError:
        st.error(f"`{pages[choice]}` 中缺少 `render()` 函数。")
