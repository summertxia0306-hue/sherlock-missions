# -*- coding: utf-8 -*-
"""口语模块冒烟测试页（家长专用，?mode=smoke 进入，家长密码门）。

目的（02_口语模块方案 §6 第2步，开发前的硬闸）——三个高风险点各自独立验证：
  ① st.audio_input 在 iPad Safari / PC 浏览器能否录音（含采样率侦测）
  ② Streamlit 美国服务器 → 讯飞国内 API 的评分往返（延迟与稳定性）
  ③ 录音 wav 上传 sherlock-results 私有库（复用 RESULTS_TOKEN）

每步可独立成败，页面底部生成一段可复制的测试报告（微信发回给口语开发入档）。
本页是临时件：冒烟通过后保留为运维自检页，正式课件另由 speaking/page.py 实现。
"""
import base64
import datetime
import json
import os
import time
import urllib.error
import urllib.request

import streamlit as st

from speaking import ise, wavtools

# 跟读测试句（贴 3B 课本；第一句埋三单-s 听说复现）
SENTENCES = [
    "The apple tastes sweet.",
    "I can see a yellow kite.",
    "We like flying kites.",
]


def _secret(name):
    try:
        v = st.secrets.get(name, "")
    except Exception:
        v = ""
    return v or os.environ.get(name, "")


def _beijing_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def _upload_recording(wav_bytes):
    """录音 → sherlock-results 私有库 recordings/smoke/。→ (路径, 耗时秒)。"""
    tok, repo = _secret("RESULTS_TOKEN"), _secret("RESULTS_REPO")
    if not (tok and repo):
        raise RuntimeError("Secrets 缺 RESULTS_REPO / RESULTS_TOKEN，无法上传")
    path = "recordings/smoke/%s.wav" % _beijing_now().strftime("%m%d_%H%M%S")
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    payload = {"message": "smoke recording",
               "content": base64.b64encode(wav_bytes).decode("ascii")}
    req = urllib.request.Request(url, method="PUT",
                                 data=json.dumps(payload).encode("utf-8"))
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30):
        pass
    return path, round(time.time() - t0, 1)


def _gate():
    """家长密码门（与家长端同一密码）。"""
    if st.session_state.get("smoke_ok"):
        return True
    st.title("🧪 口语冒烟测试（家长专用）")
    pwd = st.text_input("家长密码", type="password")
    if st.button("进入"):
        if pwd == (_secret("PARENT_PASSWORD") or "xlk2026"):
            st.session_state["smoke_ok"] = True
            st.rerun()
        st.error("密码不对")
    return False


def render():
    if not _gate():
        return
    log = st.session_state.setdefault("smoke_log", [])

    st.title("🧪 口语冒烟测试")
    st.caption("三个风险点逐项验证，PC 和 iPad 各完整跑一遍。出错不要紧——出错信息本身就是测试结果，照样复制回传。")

    # ---- 第0步：配置自检 ----
    st.subheader("第0步 · 配置自检")
    conf = {}
    cols = st.columns(5)
    for col, name in zip(cols, ("XF_APPID", "XF_API_KEY", "XF_API_SECRET",
                                "RESULTS_REPO", "RESULTS_TOKEN")):
        conf[name] = bool(_secret(name))
        col.write(("✅ " if conf[name] else "❌ ") + name)
    if not all(conf[k] for k in ("XF_APPID", "XF_API_KEY", "XF_API_SECRET")):
        st.warning("讯飞三项有缺 → 第2步会失败。请到 Streamlit 后台 Settings → Secrets 补齐（值不带【】括号）。")
    if not hasattr(st, "audio_input"):
        st.error("当前 Streamlit 版本无 audio_input 组件（需重新部署以更新版本）")
        return

    # ---- 第1步：录音 ----
    st.subheader("第1步 · 录音（验 iPad Safari 兼容性）")
    target = st.selectbox("跟读句（对着话筒读这句）", SENTENCES)
    audio = st.audio_input("点击话筒开始/停止录音")
    wav_bytes = None
    if audio is not None:
        wav_bytes = audio.getvalue()
        try:
            nch, sw, rate, dur = wavtools.wav_info(wav_bytes)
            st.success("✅ 录到声音：%.1f 秒 | 设备采样率 %d Hz | %d 声道 | %d bit"
                       % (dur, rate, nch, sw * 8))
            if dur < 0.5:
                st.warning("录音太短（<0.5秒），请重录")
        except wavtools.WavError as e:
            st.error("❌ 录音数据无法解析：%s（这条信息很重要，请回传）" % e)
            wav_bytes = None

    # ---- 第2步：讯飞评分 ----
    st.subheader("第2步 · 讯飞评分（验跨境延迟与童声评分）")
    if st.button("🚀 开始评分", disabled=wav_bytes is None):
        entry = {"time": _beijing_now().strftime("%H:%M:%S"), "句子": target}
        try:
            with st.spinner("转码并发往讯飞评测…"):
                pcm, info = wavtools.to_pcm16k(wav_bytes)
                res = ise.evaluate(_secret("XF_APPID"), _secret("XF_API_KEY"),
                                   _secret("XF_API_SECRET"), target, pcm)
            entry.update({"结果": "成功", "耗时秒": res["seconds"],
                          "总分": res["total"]})
            st.session_state["smoke_last"] = (res, info)
        except (ise.IseError, wavtools.WavError) as e:
            entry.update({"结果": "失败：%s" % e})
            st.session_state.pop("smoke_last", None)
            st.error("❌ 评分失败：%s" % e)
        log.append(entry)

    if "smoke_last" in st.session_state:
        res, info = st.session_state["smoke_last"]
        st.write("⭐" * ise.stars(res["total"]) + "（孩子将来只看到星级；下面的分数只给家长）")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("总分", res["total"])
        c2.metric("准确度", res["accuracy"])
        c3.metric("流利度", res["fluency"])
        c4.metric("完整度", res["integrity"])
        c5.metric("评测耗时", "%s 秒" % res["seconds"])
        if res["is_rejected"]:
            st.warning("引擎判定为无效朗读（乱读/非目标句）——如果你读的是对的，这条要回传")
        if res["words"]:
            st.table([{"单词": w["word"], "得分": w["score"]} for w in res["words"]])
        with st.expander("原始 XML（给口语开发看）"):
            st.code(res["raw_xml"][:3000], language="xml")

    # ---- 第3步：私有库上传 ----
    st.subheader("第3步 · 录音上传私有库")
    if st.button("☁️ 上传这段录音", disabled=wav_bytes is None):
        try:
            with st.spinner("上传中…"):
                path, secs = _upload_recording(wav_bytes)
            st.success("✅ 已上传：%s（%.1f 秒，%.0f KB）。可去 GitHub 私有库确认能播放。"
                       % (path, secs, len(wav_bytes) / 1024))
            log.append({"time": _beijing_now().strftime("%H:%M:%S"),
                        "结果": "上传成功 %s 用时%s秒" % (path, secs)})
        except Exception as e:
            st.error("❌ 上传失败：%r" % e)
            log.append({"time": _beijing_now().strftime("%H:%M:%S"),
                        "结果": "上传失败：%r" % e})

    # ---- 测试报告 ----
    st.subheader("📨 测试报告（复制 → 微信发回）")
    lines = ["【口语冒烟测试报告】%s" % _beijing_now().strftime("%Y-%m-%d %H:%M"),
             "设备：（请注明 PC浏览器名 或 iPad Safari）",
             "配置：" + " ".join(("%s=%s" % (k, "有" if v else "缺"))
                               for k, v in conf.items())]
    lines += ["%s | %s" % (e["time"], " | ".join("%s:%s" % (k, v)
              for k, v in e.items() if k != "time")) for e in log]
    st.code("\n".join(lines), language=None)
    st.caption("建议每端至少评分 3 次（看耗时波动），其中 1 次故意乱读（看引擎会不会拒识）。")
