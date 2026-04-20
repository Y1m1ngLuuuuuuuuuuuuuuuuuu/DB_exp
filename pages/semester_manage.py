import streamlit as st
import pandas as pd
from datetime import date
from pages._guards import require_role
from services.course_service import list_semesters, create_semester, update_semester

_STATUS_LABEL = {"planned": "未开放", "open": "选课中", "closed": "已结束"}
_STATUS_OPTIONS = ["planned", "open", "closed"]

def render() -> None:
    require_role("admin")
    st.header("学期管理")

    tab_list, tab_add = st.tabs(["学期列表", "新增学期"])

    with tab_list:
        semesters = list_semesters()
        if not semesters:
            st.info("暂无学期数据")
        else:
            df = pd.DataFrame([
                {
                    "学期ID":    s["semester_id"],
                    "学期名称":  s["semester_name"],
                    "开始日期":  str(s["start_date"]),
                    "结束日期":  str(s["end_date"]),
                    "选课开始":  str(s["selection_start"]),
                    "选课结束":  str(s["selection_end"]),
                    "状态":      _STATUS_LABEL.get(s["status"], s["status"]),
                }
                for s in semesters
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("修改学期")
            sem_map = {s["semester_id"]: s["semester_name"] for s in semesters}
            sel_sid = st.selectbox(
                "选择学期", list(sem_map.keys()),
                format_func=lambda x: f"{x}  {sem_map[x]}",
            )
            sel_sem = next(s for s in semesters if s["semester_id"] == sel_sid)

            with st.form("edit_semester"):
                new_name = st.text_input("学期名称", value=sel_sem["semester_name"])
                col1, col2 = st.columns(2)
                new_start = col1.date_input("开始日期", value=sel_sem["start_date"])
                new_end   = col2.date_input("结束日期", value=sel_sem["end_date"])
                col3, col4 = st.columns(2)
                new_sel_start = col3.date_input("选课开始", value=sel_sem["selection_start"])
                new_sel_end   = col4.date_input("选课结束", value=sel_sem["selection_end"])
                new_status = st.selectbox(
                    "状态", _STATUS_OPTIONS,
                    index=_STATUS_OPTIONS.index(sel_sem["status"]) if sel_sem["status"] in _STATUS_OPTIONS else 0,
                    format_func=lambda x: _STATUS_LABEL[x],
                )
                if st.form_submit_button("保存修改", type="primary"):
                    if new_end < new_start:
                        st.error("结束日期不能早于开始日期")
                    elif new_sel_end < new_sel_start:
                        st.error("选课结束日期不能早于选课开始日期")
                    else:
                        ok, msg = update_semester(sel_sid, {
                            "semester_name":   new_name,
                            "start_date":      new_start,
                            "end_date":        new_end,
                            "selection_start": new_sel_start,
                            "selection_end":   new_sel_end,
                            "status":          new_status,
                        })
                        st.success("保存成功！") if ok else st.error(f"保存失败：{msg}")
                        if ok:
                            st.rerun()

    with tab_add:
        with st.form("add_semester"):
            col1, col2 = st.columns(2)
            new_sid  = col1.text_input("学期ID *", placeholder="如 2025-2026-1")
            new_name = col2.text_input("学期名称 *", placeholder="如 2025-2026学年第一学期")
            col3, col4 = st.columns(2)
            new_start = col3.date_input("开始日期", value=date.today())
            new_end   = col4.date_input("结束日期", value=date.today())
            col5, col6 = st.columns(2)
            new_sel_s = col5.date_input("选课开始", value=date.today())
            new_sel_e = col6.date_input("选课结束", value=date.today())
            new_status = st.selectbox("初始状态", _STATUS_OPTIONS, format_func=lambda x: _STATUS_LABEL[x])

            if st.form_submit_button("创建学期", type="primary"):
                if not new_sid.strip() or not new_name.strip():
                    st.error("学期ID和名称不能为空")
                elif new_end < new_start:
                    st.error("结束日期不能早于开始日期")
                elif new_sel_e < new_sel_s:
                    st.error("选课结束日期不能早于选课开始日期")
                else:
                    ok, msg = create_semester({
                        "semester_id":    new_sid.strip(),
                        "semester_name":  new_name.strip(),
                        "start_date":     new_start,
                        "end_date":       new_end,
                        "selection_start": new_sel_s,
                        "selection_end":   new_sel_e,
                        "status":          new_status,
                    })
                    st.success("学期创建成功！") if ok else st.error(f"创建失败：{msg}")
                    if ok:
                        st.rerun()
