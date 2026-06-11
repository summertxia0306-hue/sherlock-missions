# -*- coding: utf-8 -*-
"""受限播放组件（设计文档 决策B）。

st.audio 自带进度条可无限重播，无法满足"播放次数限制不能通过普通页面
操作绕过"。本组件：服务端持有已播次数（session_state），前端只负责
播放与上报点击事件；任意 rerun 后次数不丢、不重置。
前端是免构建的纯 HTML（listening/frontend/index.html），实现 Streamlit
组件 postMessage 协议。
"""
import os

import streamlit.components.v1 as components

_FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
_component = components.declare_component("limited_audio", path=_FRONTEND)


def audio_url(repo_path):
    """repo 内 static/xxx 路径 → GitHub 原始文件 URL。"""
    assert repo_path.startswith("static/"), repo_path
    return "https://raw.githubusercontent.com/summertxia0306-hue/sherlock-missions/main/" + repo_path


def limited_audio(repo_path, qid, max_plays, used, key, label="还能听"):
    """渲染播放按钮；返回前端上报值 {qid, used, ts} 或 None。

    调用方负责：used_new = max(used, value['used'])（仅当 value['qid']==qid）。
    """
    return _component(src=audio_url(repo_path), qid=str(qid),
                      max_plays=int(max_plays), used=int(used),
                      label=label, key=key, default=None)


def merge_plays(ss_plays, play_key, value):
    """把组件返回值并入 session 播放计数表，返回当前已播次数。"""
    used = ss_plays.get(play_key, 0)
    if value and str(value.get("qid")) == str(play_key):
        used = max(used, int(value.get("used", 0)))
        ss_plays[play_key] = used
    return used
