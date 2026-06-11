from __future__ import annotations

import html

import streamlit as st


STATUS_META = {
    "selected": ("已选", "#EAF3FF", "#0071E3"),
    "completed": ("已结课", "#EAF8EF", "#1C7C43"),
    "dropped": ("已退课", "#F1F2F4", "#6E6E73"),
    "open": ("开放", "#EAF3FF", "#0071E3"),
    "closed": ("关闭", "#F1F2F4", "#6E6E73"),
    "cancelled": ("取消", "#FFF2E8", "#B75A10"),
    "active": ("启用", "#EAF8EF", "#1C7C43"),
    "inactive": ("停用", "#F1F2F4", "#6E6E73"),
    "planned": ("未开放", "#F1F2F4", "#6E6E73"),
    "enrolled": ("在籍", "#EAF8EF", "#1C7C43"),
    "suspended": ("休学", "#FFF2E8", "#B75A10"),
    "graduated": ("毕业", "#EEF0FF", "#5145B5"),
}


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #F5F5F7;
            --app-surface: #FFFFFF;
            --app-text: #1D1D1F;
            --app-muted: #6E6E73;
            --app-border: rgba(29, 29, 31, 0.10);
            --app-blue: #0071E3;
            --app-blue-soft: #EAF3FF;
            --app-shadow: 0 18px 42px rgba(0, 0, 0, 0.055);
            --app-radius: 22px;
        }

        .stApp {
            background: var(--app-bg);
            color: var(--app-text);
        }

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        #MainMenu,
        header {
            visibility: hidden;
            height: 0;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1280px;
        }

        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.82);
            border-right: 1px solid var(--app-border);
            backdrop-filter: blur(18px);
        }

        [data-testid="stSidebarNav"] {
            display: none;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            color: var(--app-muted);
        }

        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--app-text);
        }

        div[data-testid="stMetric"] {
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: var(--app-radius);
            padding: 1rem 1.05rem;
            box-shadow: var(--app-shadow);
        }

        div[data-testid="stMetric"] label {
            color: var(--app-muted);
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 999px;
            border: 1px solid rgba(0, 113, 227, 0.12);
            min-height: 2.6rem;
            font-weight: 650;
            letter-spacing: 0;
        }

        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: var(--app-blue);
            border-color: var(--app-blue);
            color: #FFFFFF;
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: var(--app-blue);
            color: var(--app-blue);
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            background: #0066CC;
            color: #FFFFFF;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-baseweb="select"] > div,
        textarea {
            border-radius: 14px !important;
            border-color: rgba(29, 29, 31, 0.14) !important;
            background: #FFFFFF !important;
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stDataEditor"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--app-border);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.035);
        }

        div[data-testid="stTabs"] button {
            border-radius: 999px;
            padding: 0.55rem 1rem;
        }

        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--app-border);
            border-radius: 18px;
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.035);
        }

        .app-hero {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--app-border);
            border-radius: 28px;
            padding: 1.65rem 1.8rem;
            margin-bottom: 1.25rem;
            box-shadow: var(--app-shadow);
        }

        .app-hero h1 {
            font-size: clamp(2rem, 3.5vw, 3.4rem);
            line-height: 1.08;
            margin: 0 0 0.55rem 0;
            font-weight: 760;
        }

        .app-hero p {
            margin: 0;
            max-width: 780px;
            color: var(--app-muted);
            font-size: 1.02rem;
            line-height: 1.68;
        }

        .app-card {
            background: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: var(--app-radius);
            padding: 1.1rem 1.15rem;
            box-shadow: var(--app-shadow);
            margin-bottom: 1rem;
        }

        .app-card-title {
            font-weight: 720;
            font-size: 1.05rem;
            margin-bottom: 0.3rem;
            color: var(--app-text);
        }

        .app-muted {
            color: var(--app-muted);
            font-size: 0.94rem;
            line-height: 1.55;
        }

        .app-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.22rem 0.62rem;
            font-size: 0.78rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .app-empty {
            border: 1px dashed rgba(29, 29, 31, 0.18);
            border-radius: 22px;
            padding: 1.3rem 1.4rem;
            background: rgba(255, 255, 255, 0.66);
            color: var(--app-muted);
            margin: 0.75rem 0;
        }

        .app-empty strong {
            display: block;
            color: var(--app-text);
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }

        .app-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-start;
        }

        .app-course-title {
            font-size: 1.08rem;
            font-weight: 720;
            color: var(--app-text);
            margin: 0 0 0.25rem 0;
        }

        .app-kv {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 0.6rem 1rem;
            margin-top: 0.8rem;
        }

        .app-kv span {
            color: var(--app-muted);
            font-size: 0.8rem;
            display: block;
        }

        .app-kv strong {
            color: var(--app-text);
            font-size: 0.95rem;
            font-weight: 650;
        }

        .app-sidebar-title {
            font-size: 1.05rem;
            font-weight: 780;
            color: var(--app-text);
            margin-bottom: 0.15rem;
        }

        .app-sidebar-subtitle {
            color: var(--app-muted);
            font-size: 0.86rem;
            line-height: 1.45;
        }

        @media (max-width: 760px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .app-hero {
                padding: 1.25rem;
                border-radius: 22px;
            }
            .app-row {
                display: block;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge_html(status: str | None, fallback: str | None = None) -> str:
    key = status or ""
    label, bg, color = STATUS_META.get(key, (fallback or key or "未知", "#F1F2F4", "#6E6E73"))
    return (
        f'<span class="app-badge" style="background:{bg}; color:{color};">'
        f"{html.escape(str(label))}</span>"
    )


def friendly_error(message: str | None) -> str:
    if not message:
        return "操作失败，请稍后重试。"
    checks = [
        ("is full", "该教学班名额已满，请选择其他班次。"),
        ("名额已满", "该教学班名额已满，请选择其他班次。"),
        ("timetable conflict", "该课程与已选课程时间冲突。"),
        ("时间冲突", "该课程与已选课程时间冲突。"),
        ("another offering for course", "同一学期同一门课程只能选择一个教学班。"),
        ("同一学期同一门课程", "同一学期同一门课程只能选择一个教学班。"),
        ("prerequisite", "尚未满足先修课程要求。"),
        ("先修", "尚未满足先修课程要求。"),
        ("duplicate key", "该记录已存在，请勿重复提交。"),
        ("已选过", "该课程已经选择过，请勿重复提交。"),
        ("outside", "当前不在允许操作的时间窗口内。"),
        ("不在选", "当前不在允许操作的时间窗口内。"),
        ("cannot be dropped", "该选课记录当前不允许退课。"),
        ("不允许退课", "该选课记录当前不允许退课。"),
    ]
    for needle, friendly in checks:
        if needle in message:
            return friendly
    return message.splitlines()[0]
