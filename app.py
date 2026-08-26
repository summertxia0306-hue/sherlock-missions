# -*- coding: utf-8 -*-
"""P5 只读迁移提示。

Streamlit 不再承载儿童 formal、家长 test 或运维提交入口。保留此页面仅用于
把旧书签引导到 CloudBase；本文件不得创建课程会话或写入学习数据。
"""

import streamlit as st


NEW_ENTRY = (
    "https://family24-d7gqb6r6m2d722f7a-1383960965."
    "tcloudbaseapp.com/sherlock-english/"
)

st.set_page_config(
    page_title="夏洛恪英语课程已迁移",
    page_icon="🌟",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("课程已迁移到新地址")
st.info("此旧地址现为只读提示，不再接受正式课程、家长测试或学习记录提交。")
st.link_button("打开新的正式学习入口", NEW_ENTRY, type="primary", use_container_width=True)
st.caption("旧课程记录已经迁移；请更新书签。")
