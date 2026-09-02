# -*- coding: utf-8 -*-
"""Sherlock English Missions · 总入口。

路由规则：
  /                          儿童端首页：听力 / 口语
  /?module=listening         听力课程列表
  /?module=speaking          口语课程列表
  /?course_id=W01D01         直接打开课程；普通直链属于儿童正式入口
  /?mode=parent              家长端
  /?mode=test&course_id=...  已认证家长测试入口
  /?mode=smoke               口语冒烟/运维自检页
  /?student_id=xxx           可选，默认 sherlock
"""
import importlib

import streamlit as st

st.set_page_config(
    page_title="English Missions",
    page_icon="🌟",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from listening import page as lpage
from speaking import models as smodels
from speaking import page as spage
from storage import progress

# Streamlit Cloud can keep imported submodules alive across a hot rerun. Reload
# shared progress first, then page/model modules, so a deploy cannot mix module
# versions when a page starts using a new progress helper.
progress = importlib.reload(progress)
lpage = importlib.reload(lpage)
spage = importlib.reload(spage)
smodels = importlib.reload(smodels)

qp = st.query_params
student_id = qp.get("student_id", "sherlock")
mode = qp.get("mode", "child")
course_id = qp.get("course_id", None)
module = qp.get("module", None)

_HOME_CSS = """
<style>
.entry { border:3px solid #d8dee5; border-radius:18px; padding:22px 10px;
  text-align:center; font-size:22px; font-weight:700; margin:6px 0;
  background:#f8fafc; }
.entry .big { font-size:52px; display:block; margin-bottom:6px; }
</style>
"""


def _course_status_ok(cid, courses):
    meta = courses.get(cid)
    return bool(
        meta
        and meta.get("publication_status", "formal") == "formal"
        and meta.get("status") == "open"
    )


def _home():
    st.markdown(_HOME_CSS, unsafe_allow_html=True)
    st.markdown("## 🌟 夏洛恪的英语任务")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="entry"><span class="big">🎧</span>听力练习</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "进入听力", key="go_listen", type="primary", use_container_width=True
        ):
            st.query_params["module"] = "listening"
            st.rerun()
    with c2:
        st.markdown(
            '<div class="entry"><span class="big">🗣️</span>口语练习</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "进入口语", key="go_speak", type="primary", use_container_width=True
        ):
            st.query_params["module"] = "speaking"
            st.rerun()


def _back_home():
    if st.button("← 回到首页", key="home_btn"):
        for key in ("module", "course_id"):
            if key in st.query_params:
                del st.query_params[key]
        st.rerun()


if mode == "parent":
    pick = st.radio(
        "选择模块",
        ["🎧 听力", "🗣️ 口语"],
        horizontal=True,
        key="parent_module",
        label_visibility="collapsed",
    )
    if pick.endswith("听力"):
        lpage.parent_view()
    else:
        spage.parent_view()
elif mode == "smoke":
    from speaking import smoke

    smoke.render()
elif mode == "test":
    try:
        data_kind = progress.submission_data_kind(
            "test",
            parent_authenticated=bool(st.session_state.get("parent_authenticated")),
        )
    except PermissionError:
        st.error("家长测试入口未授权。请先进入家长端并通过密码验证。")
        if st.button("进入家长端", type="primary", use_container_width=True):
            st.query_params.clear()
            st.query_params["mode"] = "parent"
            st.rerun()
        st.stop()

    if not course_id:
        st.error("测试入口缺少课程编号，请返回家长端重新选择。")
        st.stop()
    if course_id.startswith("S"):
        courses = smodels.all_courses()
        known = course_id in courses
        render = spage.render_course
    else:
        courses = progress.all_courses()
        known = course_id in courses
        render = lpage.render_course
    if known and courses[course_id].get("status") == "open":
        st.warning("🧪 家长测试模式：本次成绩和录音标记为 test，不计入孩子完成状态。")
        render(student_id, course_id, data_kind=data_kind)
    else:
        st.error("课程不存在或当前状态不可用：%s" % course_id)
elif course_id:
    if course_id.startswith("S"):
        courses = smodels.all_courses()
        known = course_id in courses
        render = spage.render_course
        home = spage.speaking_home
    else:
        courses = progress.all_courses()
        known = course_id in courses
        render = lpage.render_course
        home = lpage.listening_home
    _back_home()
    if known and _course_status_ok(course_id, courses):
        render(student_id, course_id, data_kind="formal")
    else:
        home(student_id)
elif module == "listening":
    _back_home()
    lpage.listening_home(student_id)
elif module == "speaking":
    _back_home()
    spage.speaking_home(student_id)
else:
    _home()
