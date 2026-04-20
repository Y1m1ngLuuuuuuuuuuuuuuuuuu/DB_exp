import streamlit as st

def require_role(*allowed_roles: str) -> str:
    if not st.session_state.get("logged_in"):
        st.error("请先登录后再访问该页面。")
        st.stop()

    role = st.session_state.get("role")
    if allowed_roles and role not in allowed_roles:
        st.error("当前账号无权访问该页面。")
        st.stop()

    return role
