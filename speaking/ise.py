# -*- coding: utf-8 -*-
"""讯飞语音评测（ISE 流式版）客户端封装。

协议依据：https://www.xfyun.cn/doc/Ise/IseAPI.html（2026-06-12 核对）
- 鉴权：hmac-sha256 签名拼 URL 参数（authorization / date / host）
- 流程：首帧 cmd=ssb 传参数与文本（ttp_skip=true）→ cmd=auw 分帧传音频
  （首帧 aus=1, 中间 aus=2, 末帧 aus=4 + data.status=2）→ 收 status=2 的
  base64 XML 结果
- 英文百分制：rst="entirety" + ise_unite="1" + extra_ability="multi_dimension"

纯逻辑模块：不 import streamlit，密钥由调用方传入（便于单测与复用）。
依赖：websocket-client（requirements.txt 已声明）。
"""
import base64
import hashlib
import hmac
import json
import ssl
import time
import xml.etree.ElementTree as ET
from email.utils import formatdate
from urllib.parse import urlencode

ISE_HOST = "ise-api.xfyun.cn"
ISE_PATH = "/v2/open-ise"

# 每帧 1280B。官方建议 40ms/帧，但 2026-06-12 冒烟实测整体 6.5–8.9 秒里大半
# 耗在按 40ms 发帧上；服务端是离线评测（凑齐 status=2 才算分），实践上可以
# 快发。降到 10ms/帧，5 秒音频的发送时间从 ~5s 降到 ~1.2s。若出现 10163/限流
# 类错误再回调到 0.04。
FRAME_SIZE = 1280
FRAME_INTERVAL = 0.01


class IseError(Exception):
    """评测失败。message 已含错误码与建议，可直接展示给家长。"""


def build_auth_url(api_key, api_secret, host=ISE_HOST, path=ISE_PATH, date=None):
    """生成带鉴权参数的 wss URL（date 可注入便于单测）。"""
    date = date or formatdate(usegmt=True)  # RFC1123 GMT
    origin = "host: %s\ndate: %s\nGET %s HTTP/1.1" % (host, date, path)
    sig = base64.b64encode(
        hmac.new(api_secret.encode("utf-8"), origin.encode("utf-8"),
                 hashlib.sha256).digest()).decode("ascii")
    auth_origin = ('api_key="%s", algorithm="hmac-sha256", '
                   'headers="host date request-line", signature="%s"') % (api_key, sig)
    auth = base64.b64encode(auth_origin.encode("utf-8")).decode("ascii")
    return "wss://%s%s?%s" % (host, path, urlencode(
        {"authorization": auth, "date": date, "host": host}))


def _first_frame(app_id, text, category):
    return {
        "common": {"app_id": app_id},
        "business": {
            "sub": "ise", "ent": "en_vip", "category": category,
            "cmd": "ssb", "text": "\ufeff" + text, "tte": "utf-8",
            "ttp_skip": True, "aue": "raw", "auf": "audio/L16;rate=16000",
            "rstcd": "utf8", "rst": "entirety", "ise_unite": "1",
            "extra_ability": "multi_dimension", "group": "pupil",
        },
        "data": {"status": 0},
    }


def evaluate(app_id, api_key, api_secret, text, pcm16k,
             category="read_sentence", timeout=20, frame_interval=FRAME_INTERVAL):
    """对 16kHz/16bit/单声道 PCM 音频按目标文本评测。

    返回 dict（parse_result 的结果 + 计时）：
      total/accuracy/fluency/integrity: float 或 None
      words: [{"word":…, "score":float|None}]
      is_rejected: bool（乱读/无效音频）
      raw_xml: 原始结果 XML
      seconds: 整个评测调用耗时
    失败抛 IseError（含错误码与给家长看的建议）。
    """
    try:
        import websocket  # websocket-client
    except ImportError:
        raise IseError("缺少依赖 websocket-client（requirements.txt 需含它并重新部署）")

    t0 = time.time()
    url = build_auth_url(api_key, api_secret)
    try:
        ws = websocket.create_connection(
            url, timeout=timeout, sslopt={"cert_reqs": ssl.CERT_NONE})
    except websocket.WebSocketBadStatusException as e:
        raise IseError(
            "讯飞握手被拒（HTTP %s）。常见原因：APIKey/APISecret 抄错、"
            "服务器时间偏差>5分钟。原始信息：%s" % (getattr(e, "status_code", "?"), e))
    except Exception as e:
        raise IseError("连不上讯飞服务器（跨境网络问题的可能性最大）：%r" % e)

    try:
        ws.send(json.dumps(_first_frame(app_id, text, category)))
        # 音频分帧
        n = len(pcm16k)
        if n == 0:
            raise IseError("音频为空（录音失败或转码失败）")
        offset = 0
        first = True
        while offset < n:
            chunk = pcm16k[offset:offset + FRAME_SIZE]
            offset += FRAME_SIZE
            last = offset >= n
            frame = {
                "business": {"cmd": "auw",
                             "aus": 4 if last else (1 if first else 2)},
                "data": {"status": 2 if last else 1,
                         "data": base64.b64encode(chunk).decode("ascii")},
            }
            ws.send(json.dumps(frame))
            first = False
            if not last and frame_interval:
                time.sleep(frame_interval)

        # 收结果
        deadline = time.time() + timeout
        while True:
            if time.time() > deadline:
                raise IseError("等待评分结果超时（%ds）——跨境延迟或服务异常" % timeout)
            msg = json.loads(ws.recv())
            code = msg.get("code", -1)
            if code != 0:
                raise IseError("讯飞返回错误 code=%s message=%s sid=%s" % (
                    code, msg.get("message"), msg.get("sid")))
            data = msg.get("data") or {}
            if data.get("status") == 2:
                xml_text = base64.b64decode(data.get("data", "")).decode("utf-8")
                out = parse_result(xml_text)
                out["seconds"] = round(time.time() - t0, 1)
                out["sid"] = msg.get("sid", "")
                return out
    finally:
        try:
            ws.close()
        except Exception:
            pass


def evaluate_retry(app_id, api_key, api_secret, text, pcm16k, **kw):
    """evaluate + 失败自动重试 1 次（冒烟确认跨境偶发抖动的补救，方案 §7）。"""
    try:
        return evaluate(app_id, api_key, api_secret, text, pcm16k, **kw)
    except IseError:
        time.sleep(1.0)
        return evaluate(app_id, api_key, api_secret, text, pcm16k, **kw)


def _f(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def parse_result(xml_text):
    """解析评测结果 XML（防御式：英文句子题型，字段缺失不崩）。"""
    out = {"total": None, "accuracy": None, "fluency": None, "integrity": None,
           "standard": None, "is_rejected": False, "words": [],
           "raw_xml": xml_text}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    # 总分节点 = 第一个带 total_score 的元素（rec_paper 下的 read_sentence/read_chapter）
    paper = root.find(".//rec_paper")
    scope = paper if paper is not None else root
    for el in scope.iter():
        if "total_score" in el.attrib:
            out["total"] = _f(el.get("total_score"))
            out["accuracy"] = _f(el.get("accuracy_score"))
            out["fluency"] = _f(el.get("fluency_score"))
            out["integrity"] = _f(el.get("integrity_score"))
            out["standard"] = _f(el.get("standard_score"))
            out["is_rejected"] = (el.get("is_rejected") == "true")
            break
    for w in scope.iter("word"):
        content = (w.get("content") or "").strip()
        if not content or content in ("sil", "fil"):
            continue
        out["words"].append({"word": content, "score": _f(w.get("total_score"))})
    return out


def stars(total):
    """分数→星级（W1 从宽阈值，待实测分布后校准；冒烟页同时显示分数给家长）。"""
    if total is None:
        return 0
    if total >= 75:
        return 3
    if total >= 50:
        return 2
    return 1
