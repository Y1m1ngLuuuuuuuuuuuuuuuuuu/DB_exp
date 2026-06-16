from __future__ import annotations

import html

import streamlit as st

from ui.theme import friendly_error, status_badge_html


def render_app_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <section class="app-hero">
            <h1>{html.escape(title)}</h1>
            {subtitle_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str | None = None) -> None:
    render_app_header(title, subtitle)


def render_metric_card(
    label: str,
    value,
    delta: str | None = None,
    caption: str | None = None,
) -> None:
    caption_text = caption or delta
    help_html = f'<div class="app-muted">{html.escape(caption_text)}</div>' if caption_text else ""
    st.markdown(
        f"""
        <div class="app-card">
            <div class="app-muted">{html.escape(label)}</div>
            <div style="font-size:2rem;font-weight:760;line-height:1.15;margin-top:.25rem;">
                {html.escape(str(value))}
            </div>
            {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status: str | None, fallback: str | None = None) -> None:
    st.markdown(status_badge_html(status, fallback), unsafe_allow_html=True)


def render_section_title(title: str, description: str | None = None) -> None:
    desc = f'<div class="app-muted">{html.escape(description)}</div>' if description else ""
    st.markdown(
        f"""
        <div style="margin:1.35rem 0 .75rem 0;">
            <div class="app-card-title">{html.escape(title)}</div>
            {desc}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_card(title: str, description: str | None = None):
    desc = f'<div class="app-muted">{html.escape(description)}</div>' if description else ""
    st.markdown(
        f"""
        <div class="app-card" style="margin-top:1rem;">
            <div class="app-card-title">{html.escape(title)}</div>
            {desc}
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.container()


def render_empty_state(title: str, message: str, action_label: str | None = None) -> None:
    action = f"<br><span>{html.escape(action_label)}</span>" if action_label else ""
    st.markdown(
        f"""
        <div class="app-empty">
            <strong>{html.escape(title)}</strong>
            {html.escape(message)}{action}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_error_message(message: str | None) -> None:
    st.error(friendly_error(message))


def render_friendly_error(error) -> None:
    render_error_message(str(error) if error is not None else None)


def render_success_message(message: str) -> None:
    st.success(message)


def render_filter_bar(title: str | None = None, description: str | None = None):
    if title or description:
        render_section_title(title or "筛选", description)
    return st.container()


def course_card_html(
    title: str,
    subtitle: str,
    fields: dict[str, object],
    status: str | None = None,
    status_label: str | None = None,
) -> str:
    kv = "\n".join(
        f"<div><span>{html.escape(str(k))}</span><strong>{html.escape(str(v))}</strong></div>"
        for k, v in fields.items()
    )
    badge = status_badge_html(status, status_label) if status or status_label else ""
    return f"""
    <div class="app-card">
        <div class="app-row">
            <div>
                <div class="app-course-title">{html.escape(title)}</div>
                <div class="app-muted">{html.escape(subtitle)}</div>
            </div>
            <div>{badge}</div>
        </div>
        <div class="app-kv">{kv}</div>
    </div>
    """


def render_course_card(
    title: str,
    subtitle: str,
    fields: dict[str, object],
    status: str | None = None,
    status_label: str | None = None,
) -> None:
    st.markdown(course_card_html(title, subtitle, fields, status, status_label), unsafe_allow_html=True)


def format_location(row: dict) -> str:
    if row.get("building") and row.get("room_no"):
        return f"{row['building']}{row['room_no']}"
    return "待定"


def compact_number(value, suffix: str = "") -> str:
    if value is None:
        return "-"
    return f"{value}{suffix}"
