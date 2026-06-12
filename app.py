# -*- coding: utf-8 -*-
"""Sherlock English Missions · 听力模块临时入口。

注意：这只是听力模块的极简路由，不是总系统首页。
统一架构的一级界面（口语练习 / 听力练习 两个入口）由 Codex 总架构师实现，
届时"听力练习"入口指向 listening.page.listening_home()，本文件被替换。
接口契约见 listening/CONTRACT.md。

URL 用法：
  儿童端听力主界面（默认）:  /
  直接打开某课:              /?course_id=W01D01
  家长端:                    /?mode=parent   （密码 = st.secrets 的 PARENT_PASSWORD）
  可选参数:                  student_id（默认 sherlock）
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
    # 直链访问（?course_id=…）只看课程状态是否"打开"，不受 open_date 限制——
    # 这是家长在解锁日前提前验收课程的通道；孩子的课程列表仍按 open_date 到期显示。
    if (course_id and course_id in progress.all_courses()
            and progress.get_course_status(course_id) == "open"):
        lpage.render_course(student_id, course_id)
    else:
        lpage.listening_home(student_id)
