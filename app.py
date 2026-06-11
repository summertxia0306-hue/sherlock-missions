# -*- coding: utf-8 -*-
"""Sherlock English Missions · 听力模块临时入口。

注意：这只是听力模块的极简路由，不是总系统首页。
总首页 / 任务地图 / 星星规则由 Codex 的统一架构接管，届时本文件被替换，
listening 包按 listening/CONTRACT.md 的接口被调用。

URL 用法：
  儿童端（默认）:  /?course_id=W01D01
  家长端:          /?mode=parent      （需密码，st.secrets 的 PARENT_PASSWORD）
  可选参数:        student_id（默认 sherlock）
"""
import streamlit as st

st.set_page_config(page_title="English Missions 听力", page_icon="🎧",
                   layout="centered", initial_sidebar_state="collapsed")

from listening import page as lpage
from storage import progress

qp = st.query_params
student_id = qp.get("student_id", "sherlock")
mode = qp.get("mode", "child")
course_id = qp.get("course_id", None)

if mode == "parent":
    lpage.parent_view()
else:
    courses = progress.visible_courses()
    if not courses:
        st.info("今天还没有开放的听力任务，请告诉爸爸妈妈。")
    elif course_id and course_id in courses:
        lpage.render_course(student_id, course_id)
    elif len(courses) == 1:
        lpage.render_course(student_id, list(courses)[0])
    else:
        st.markdown("## 🎧 选择今天的听力任务")
        for cid, meta in courses.items():
            if st.button("%s · %s" % (cid, meta.get("title", "")),
                         key="pick_" + cid, use_container_width=True):
                st.query_params["course_id"] = cid
                st.rerun()
