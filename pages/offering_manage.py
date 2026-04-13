"""
pages/offering_manage.py —— 开课安排管理（管理员）
为课程分配教师、教室、学期，管理开课班次。
"""
import streamlit as st
import pandas as pd
from pages._guards import require_role
from db.connection import query
from services.course_service import (
    list_semesters, list_offerings,
    list_courses, list_classrooms,
    create_offering, update_offering, delete_offering,
)

_STATUS_LABEL = {"open": "开放选课", "closed": "已关闭", "cancelled": "已取消"}
_STATUS_OPTIONS = ["open", "closed", "cancelled"]


def render() -> None:
    require_role("admin")
    st.header("开课安排管理")

    tab_list, tab_add = st.tabs(["班次列表", "新增开课班次"])

    # ── 辅助数据 ─────────────────────────────────────────────────
    semesters  = list_semesters()
    courses    = list_courses(include_inactive=False)
    teachers   = query("SELECT teacher_id, teacher_name FROM teacher WHERE status='active' ORDER BY teacher_id")
    classrooms = list_classrooms()

    sem_map  = {s["semester_id"]: s["semester_name"] for s in semesters}
    crs_map  = {c["course_id"]:   f"{c['course_id']} {c['course_name']}" for c in courses}
    tch_map  = {t["teacher_id"]:  t["teacher_name"] for t in teachers}
    cls_map  = {c["classroom_id"]: f"{c['building']}{c['room_no']}（容量 {c['capacity']}）"
                for c in classrooms}

    if not semesters:
        st.warning("请先在「学期管理」中创建学期")
        return

    # ── 班次列表 ─────────────────────────────────────────────────
    with tab_list:
        sel_sem_id = st.selectbox(
            "选择学期",
            list(sem_map.keys()),
            format_func=lambda x: sem_map[x],
            key="ofm_sem",
        )
        offerings = list_offerings(semester_id=sel_sem_id)

        if not offerings:
            st.info("该学期暂无开课班次")
        else:
            df = pd.DataFrame([
                {
                    "班次ID":    o["offering_id"],
                    "课程":      f"{o['course_id']} {o['course_name']}",
                    "教师":      o["teacher_name"],
                    "教室":      f"{o['building'] or ''}{o['room_no'] or ''}".strip() or "-",
                    "上课时间":  o["schedule_text"] or "-",
                    "已选/上限": f"{o['selected_count']} / {o['max_capacity']}",
                    "状态":      _STATUS_LABEL.get(o["status"], o["status"]),
                }
                for o in offerings
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 编辑 / 删除
            st.subheader("修改 / 删除班次")
            off_opts = {o["offering_id"]: f"ID={o['offering_id']}  {o['course_id']} {o['course_name']} — {o['teacher_name']}"
                        for o in offerings}
            sel_oid = st.selectbox("选择班次", list(off_opts.keys()), format_func=lambda x: off_opts[x])
            sel_off = next(o for o in offerings if o["offering_id"] == sel_oid)

            with st.form("edit_offering"):
                tch_keys = list(tch_map.keys())
                cur_tch  = sel_off["teacher_id"]
                new_tch  = st.selectbox(
                    "任课教师", tch_keys,
                    index=tch_keys.index(cur_tch) if cur_tch in tch_keys else 0,
                    format_func=lambda x: tch_map[x],
                )
                cls_keys = [None] + list(cls_map.keys())
                cur_cls  = sel_off.get("classroom_id") or None
                new_cls  = st.selectbox(
                    "教室（可选）", cls_keys,
                    index=cls_keys.index(cur_cls) if cur_cls in cls_keys else 0,
                    format_func=lambda x: cls_map[x] if x else "（不指定）",
                )
                col1, col2 = st.columns(2)
                new_cap  = col1.number_input("容量上限", 1, 500, int(sel_off["max_capacity"]))
                new_sch  = col2.text_input("上课时间", value=sel_off["schedule_text"] or "")
                new_stat = st.selectbox(
                    "状态", _STATUS_OPTIONS,
                    index=_STATUS_OPTIONS.index(sel_off["status"]) if sel_off["status"] in _STATUS_OPTIONS else 0,
                    format_func=lambda x: _STATUS_LABEL[x],
                )
                if st.form_submit_button("保存修改", type="primary"):
                    ok, msg = update_offering(sel_oid, {
                        "teacher_id":    new_tch,
                        "classroom_id":  new_cls,
                        "max_capacity":  new_cap,
                        "schedule_text": new_sch,
                        "status":        new_stat,
                    })
                    st.success("保存成功！") if ok else st.error(f"保存失败：{msg}")
                    if ok:
                        st.rerun()

            st.divider()
            st.markdown("**删除班次**（仅允许删除无在选学生的班次）")
            if st.button("删除该班次", type="secondary"):
                ok, msg = delete_offering(sel_oid)
                st.success("删除成功！") if ok else st.error(f"删除失败：{msg}")
                if ok:
                    st.rerun()

    # ── 新增开课班次 ──────────────────────────────────────────────
    with tab_add:
        if not courses:
            st.warning("请先在「课程信息维护」中添加课程")
            return
        if not teachers:
            st.warning("请先在「教师维护」中添加教师")
            return

        with st.form("add_offering"):
            col1, col2 = st.columns(2)
            sem_keys = list(sem_map.keys())
            new_sem  = col1.selectbox("学期 *", sem_keys, format_func=lambda x: sem_map[x])
            crs_keys = list(crs_map.keys())
            new_crs  = col2.selectbox("课程 *", crs_keys, format_func=lambda x: crs_map[x])

            col3, col4 = st.columns(2)
            tch_keys = list(tch_map.keys())
            new_tch  = col3.selectbox("任课教师 *", tch_keys, format_func=lambda x: tch_map[x])
            cls_keys = [None] + list(cls_map.keys())
            new_cls  = col4.selectbox(
                "教室（可选）", cls_keys,
                format_func=lambda x: cls_map[x] if x else "（不指定）",
            )

            col5, col6 = st.columns(2)
            new_cap  = col5.number_input("容量上限 *", 1, 500, 40)
            new_sch  = col6.text_input("上课时间", placeholder="如：周一 1-2节")
            new_stat = st.selectbox("状态", _STATUS_OPTIONS, format_func=lambda x: _STATUS_LABEL[x])

            if st.form_submit_button("创建班次", type="primary"):
                ok, msg = create_offering({
                    "course_id":    new_crs,
                    "semester_id":  new_sem,
                    "teacher_id":   new_tch,
                    "classroom_id": new_cls,
                    "max_capacity": new_cap,
                    "schedule_text": new_sch,
                    "status":       new_stat,
                })
                st.success("班次创建成功！") if ok else st.error(f"创建失败：{msg}")
                if ok:
                    st.rerun()
