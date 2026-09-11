# -*- coding: utf-8 -*-
"""自研录音组件封装 + 录音上传私有库。

为何不用 st.audio_input（2026-06-12 冒烟后家长四条反馈）：原生组件做不了
3-2-1 倒计时（孩子点了就读、开头被吃）、按钮太小、不能控制自动停止、
体验不可定制。本组件镜像 listening 限次播放组件的做法（免构建纯 HTML +
postMessage 协议），JS 端优先使用 MediaRecorder 采集并直接产出
16kHz/16bit/单声道 wav，服务端零转码直送讯飞。

组件返回值：{qid, take, dur, wav_b64} 或 None（孩子点"✅就用这个"才返回）。
"""
import base64
from array import array
import datetime
import io
import json
import math
import os
import sys
import time
import urllib.request
import wave

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


def _frame_correlation(left, right):
    """短帧皮尔逊相关度；近静音帧返回 None，避免把自然停顿判作重复。"""
    size = min(len(left), len(right))
    if size < 64:
        return None
    mean_left = sum(left[:size]) / size
    mean_right = sum(right[:size]) / size
    cross = power_left = power_right = 0.0
    for index in range(size):
        a = left[index] - mean_left
        b = right[index] - mean_right
        cross += a * b
        power_left += a * a
        power_right += b * b
    # 16-bit PCM 下约 -50 dBFS 以下视为停顿/底噪，不参与重复帧判断。
    if power_left / size < 100.0 ** 2 or power_right / size < 100.0 ** 2:
        return None
    return cross / math.sqrt(power_left * power_right)


def _has_duplicated_frames(samples, sample_rate):
    """识别 iPad 故障：约 85/93 ms 的采集帧按相邻对重复。"""
    # ScriptProcessor 4096 帧在常见 48 kHz / 44.1 kHz 输入下转成 16 kHz 后的长度。
    frame_sizes = {round(sample_rate * 4096 / rate) for rate in (48000, 44100)}
    for frame_size in frame_sizes:
        frames = [samples[start:start + frame_size]
                  for start in range(0, len(samples) - frame_size + 1, frame_size)]
        if len(frames) < 10:
            continue
        parity_hits = [0, 0]
        parity_pairs = [0, 0]
        for index in range(1, len(frames)):
            parity = index % 2
            parity_pairs[parity] += 1
            correlation = _frame_correlation(frames[index - 1], frames[index])
            if correlation is not None and correlation >= 0.95:
                parity_hits[parity] += 1
        for parity in (0, 1):
            other = 1 - parity
            if (parity_hits[parity] >= 5
                    and parity_hits[parity] / parity_pairs[parity] >= 0.35
                    and parity_hits[other] <= max(2, parity_hits[parity] // 5)):
                return True
    return False


def _has_alternating_silence(samples, sample_rate):
    """识别约 85/93 ms 空白帧与有声帧高规律交替。"""
    zero_runs = []
    start = None
    for index, value in enumerate(samples):
        if abs(value) <= 1 and start is None:
            start = index
        elif abs(value) > 1 and start is not None:
            zero_runs.append((start, index - start))
            start = None
    if start is not None:
        zero_runs.append((start, len(samples) - start))

    frame_sizes = {round(sample_rate * 4096 / rate) for rate in (48000, 44100)}
    for frame_size in frame_sizes:
        candidates = [(run_start, run_size) for run_start, run_size in zero_runs
                      if frame_size * 0.55 <= run_size <= frame_size * 1.35]
        if len(candidates) < 4:
            continue
        regular = sum(abs(candidates[index][0] - candidates[index - 1][0]
                          - 2 * frame_size) <= frame_size * 0.30
                      for index in range(1, len(candidates)))
        if regular >= 3 and regular / (len(candidates) - 1) >= 0.65:
            return True
    return False


def validate_wav_integrity(wav_data):
    """评分前校验录音结构与已知 iPad 断续模式。返回可诊断 verdict。"""
    try:
        with wave.open(io.BytesIO(wav_data), "rb") as reader:
            channels = reader.getnchannels()
            sample_width = reader.getsampwidth()
            sample_rate = reader.getframerate()
            frame_count = reader.getnframes()
            compression = reader.getcomptype()
            raw = reader.readframes(frame_count)
    except (EOFError, wave.Error):
        return {"ok": False, "reason": "invalid_wav"}

    if (channels != 1 or sample_width != 2 or sample_rate != 16000
            or compression != "NONE"):
        return {"ok": False, "reason": "invalid_wav"}
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    if frame_count < sample_rate * 0.4:
        return {"ok": False, "reason": "too_short"}
    peak = max((abs(value) for value in samples), default=0)
    if peak < round(32767 * 0.01):
        return {"ok": False, "reason": "silent"}
    if _has_alternating_silence(samples, sample_rate):
        return {"ok": False, "reason": "alternating_silence"}
    if _has_duplicated_frames(samples, sample_rate):
        return {"ok": False, "reason": "duplicated_frames"}
    return {"ok": True, "reason": "ok"}


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
