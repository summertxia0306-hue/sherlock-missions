# -*- coding: utf-8 -*-
"""自研录音组件封装 + 录音上传私有库。

为何不用 st.audio_input（2026-06-12 冒烟后家长四条反馈）：原生组件做不了
3-2-1 倒计时（孩子点了就读、开头被吃）、按钮太小、不能控制自动停止、
体验不可定制。本组件镜像 listening 限次播放组件的做法（免构建纯 HTML +
postMessage 协议），JS 端直接产出 16kHz/16bit/单声道 wav（ScriptProcessor
采集 + 线性重采样），服务端零转码直送讯飞。

组件返回值：{qid, take, dur, wav_b64} 或 None（孩子点"✅就用这个"才返回）。
"""
import base64
import datetime
import json
import os
import time
import urllib.request

import streamlit.components.v1 as components
from storage import progress

_FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
_component = components.declare_component("sherlock_recorder", path=_FRONTEND)


def record(qid, key, take=1, max_sec=20, countdown=3, label=None):
    """渲染录音按钮。返回 {qid, take, dur, wav_b64} 或 None。
    调用方用 key 区分题目与录次（key 变 = 全新组件实例）。"""
    return _component(qid=str(qid), take=int(take), max_sec=int(max_sec),
                      countdown=int(countdown), label=label, key=key, default=None)


def wav_bytes(value):
    """组件返回值 → (wav bytes, pcm bytes)。wav 含 44 字节头，pcm 即去头数据。"""
    raw = base64.b64decode(value["wav_b64"])
    return raw, raw[44:]


def upload_recording(wav, course_id, qid, take, secrets_get):
    """录音存 sherlock-results 私有库 recordings/{course_id}/。失败抛异常。
    → (路径, 耗时秒)。secrets_get: name->value 的取值函数（隔离 streamlit）。"""
    tok = secrets_get("RESULTS_TOKEN")
    repo = secrets_get("RESULTS_REPO")
    if not (tok and repo):
        raise RuntimeError("未配置 RESULTS_REPO / RESULTS_TOKEN")
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%m%d_%H%M%S")
    path = "recordings/%s/%s_q%02d_t%d.wav" % (course_id, now, int(qid), int(take))
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    payload = {"message": "recording %s q%s" % (course_id, qid),
               "content": base64.b64encode(wav).decode("ascii")}
    req = urllib.request.Request(url, method="PUT",
                                 data=json.dumps(payload).encode("utf-8"))
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30):
        pass
    return path, round(time.time() - t0, 1)


def classify_recordings(items, metadata):
    """给录音列表补明确 data_kind；旧无元数据文件保守按 test。"""
    out = []
    for item in items:
        row = dict(item)
        meta = metadata.get(row["path"])
        value = meta.get("data_kind") if isinstance(meta, dict) else meta
        row["data_kind"] = progress.normalize_data_kind(value)
        out.append(row)
    return out


def list_recordings(course_id, secrets_get):
    """家长端录音箱：列出某课全部录音并补 data_kind。"""
    tok = secrets_get("RESULTS_TOKEN")
    repo = secrets_get("RESULTS_REPO")
    if not (tok and repo):
        return []
    url = "https://api.github.com/repos/%s/contents/recordings/%s" % (repo, course_id)
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            items = json.loads(resp.read().decode("utf-8"))
        rows = [{"name": it["name"], "path": it["path"], "size": it["size"]}
                for it in items if it["type"] == "file" and it["name"].endswith(".wav")]
        return classify_recordings(rows, progress.recording_kind_map())
    except Exception:
        return []


def fetch_recording(path, secrets_get):
    """按路径取回单个录音的 wav bytes（家长端试听）。"""
    tok = secrets_get("RESULTS_TOKEN")
    repo = secrets_get("RESULTS_REPO")
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/vnd.github.raw+json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()
