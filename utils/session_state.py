import streamlit as st

from services.auth_service import get_student_id, get_teacher_id


def apply_login_state(user: dict, token: str | None = None) -> None:
    st.session_state.logged_in = True
    st.session_state.user_id = user["user_id"]
    st.session_state.username = user["username"]
    st.session_state.role = user["role"]
    st.session_state.student_id = None
    st.session_state.teacher_id = None
    st.session_state.session_token = token

    if user["role"] == "student":
        st.session_state.student_id = get_student_id(user["user_id"])
    elif user["role"] == "teacher":
        st.session_state.teacher_id = get_teacher_id(user["user_id"])
