import json

import streamlit as st
import streamlit.components.v1 as components

from config import SESSION_COOKIE_MAX_AGE_DAYS, SESSION_COOKIE_NAME


def get_auth_cookie() -> str | None:
    return st.context.cookies.get(SESSION_COOKIE_NAME)


def set_auth_cookie(token: str) -> None:
    _write_cookie_script(token=token, max_age_days=SESSION_COOKIE_MAX_AGE_DAYS, reload_page=True)


def clear_auth_cookie() -> None:
    _write_cookie_script(token="", max_age_days=0, reload_page=False)


def _write_cookie_script(token: str, max_age_days: int, reload_page: bool) -> None:
    name_js = json.dumps(SESSION_COOKIE_NAME)
    token_js = json.dumps(token)
    max_age = max_age_days * 24 * 60 * 60
    reload_js = "setTimeout(() => window.parent.location.reload(), 120);" if reload_page else ""

    components.html(
        f"""
        <script>
        const cookieName = {name_js};
        const cookieValue = encodeURIComponent({token_js});
        const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
        const cookie = `${{cookieName}}=${{cookieValue}}; path=/; max-age={max_age}; SameSite=Lax${{secure}}`;

        try {{
            window.parent.document.cookie = cookie;
        }} catch (err) {{
            document.cookie = cookie;
        }}

        {reload_js}
        </script>
        """,
        height=0,
    )
