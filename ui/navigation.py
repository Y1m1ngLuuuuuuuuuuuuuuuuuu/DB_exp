from __future__ import annotations

import streamlit as st


ROLE_LABELS = {
    "student": "学生端",
    "teacher": "教师端",
    "admin": "管理员端",
}


def render_sidebar_navigation(role: str, pages: dict[str, str], username: str | None) -> str | None:
    st.markdown(
        f"""
        <div class="app-sidebar-title">学生选课成绩管理系统</div>
        <div class="app-sidebar-subtitle">
            {ROLE_LABELS.get(role, role)} · {username or "-"}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    if not pages:
        st.warning("该角色暂无可用页面")
        return None
    return st.radio(
        "导航",
        list(pages.keys()),
        label_visibility="collapsed",
        key=f"nav_{role}",
    )


def render_sidebar(role: str, current_page: str | None = None, pages: dict[str, str] | None = None) -> str | None:
    available_pages = pages or {}
    if current_page and current_page in available_pages:
        page_names = list(available_pages.keys())
        st.session_state[f"nav_{role}"] = current_page if current_page in page_names else page_names[0]
    return render_sidebar_navigation(role, available_pages, st.session_state.get("username"))
