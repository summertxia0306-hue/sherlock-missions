# -*- coding: utf-8 -*-
"""进度/结果/课程状态的读写接口。

v1.1（2026-06-12）：新增 GitHub 私有仓库持久化后端，修复生产问题 #5
（平台重启/重新部署清空成绩与课程状态）。
- 配置（Streamlit 后台 Secrets，两行）：
    RESULTS_REPO = "你的用户名/sherlock-results"     ← 必须是【私有】仓库
    RESULTS_TOKEN = "github_pat_..."                  ← fine-grained token，仅该库 Contents 读写
- 已配置：成绩与课程状态写入该私有库（results.json / course_status.json），重启不丢。
- 未配置：自动退回 v1 行为（仅运行目录，重启即失）。
- 接口签名与 v1 完全一致，调用方无感知（CONTRACT §3 承诺）。
"""
import base64
import datetime
import json
import os
import threading
import time
import urllib.error
import urllib.request

_LOCK = threading.Lock()
COURSE_STATUSES = ("open", "closed", "hidden", "archived")
_TTL = 45
_cache = {}


def beijing_today():
    """Streamlit Cloud 服务器是 UTC，按北京时间(UTC+8)算"今天"。"""
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")


# ---------- 本地（运行目录）层：始终可用的快路径与兜底 ----------

def _runtime_dir():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(root, "_runtime")
    os.makedirs(d, exist_ok=True)
    return d


def _read(name, default):
    path = os.path.join(_runtime_dir(), name)
    if not os.path.isfile(path):
        return default
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def _write(name, data):
    path = os.path.join(_runtime_dir(), name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


# ---------- GitHub 私有库持久化层 ----------

def _gh_conf():
    tok = repo = ""
    try:
        import streamlit as st
        tok = st.secrets.get("RESULTS_TOKEN", "")
        repo = st.secrets.get("RESULTS_REPO", "")
    except Exception:
        pass
    tok = tok or os.environ.get("RESULTS_TOKEN", "")
    repo = repo or os.environ.get("RESULTS_REPO", "")
    if tok and repo:
        return tok, repo
    return None, None


def persistence_enabled():
    return _gh_conf()[0] is not None


def _gh_request(method, url, token, payload=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _remote_read(name, default, use_cache=True):
    """→ (data, sha)。未配置或网络失败 → (None, None) 哨兵，调用方退本地。"""
    tok, repo = _gh_conf()
    if not tok:
        return None, None
    now = time.time()
    if use_cache:
        hit = _cache.get(name)
        if hit and hit[0] > now:
            return hit[1], hit[2]
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, name)
    try:
        obj = _gh_request("GET", url, tok)
        data = json.loads(base64.b64decode(obj["content"]).decode("utf-8"))
        _cache[name] = (now + _TTL, data, obj["sha"])
        return data, obj["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            _cache[name] = (now + _TTL, default, None)
            return default, None
        return None, None
    except Exception:
        return None, None


def _remote_write(name, data, sha):
    tok, repo = _gh_conf()
    if not tok:
        return False
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, name)
    payload = {"message": "update %s (%s)" % (name, beijing_today()),
               "content": base64.b64encode(
                   json.dumps(data, ensure_ascii=False, indent=1).encode("utf-8")).decode("ascii")}
    if sha:
        payload["sha"] = sha
    obj = _gh_request("PUT", url, tok, payload)
    _cache[name] = (time.time() + _TTL, data, obj["content"]["sha"])
    return True


def _remote_append_result(result):
    for _attempt in range(2):
        cur, sha = _remote_read("results.json", [], use_cache=False)
        if cur is None:
            return False
        cur.append(result)
        try:
            _remote_write("results.json", cur, sha)
            return True
        except Exception:
            time.sleep(1.5)
    return False


# ---------- 对外接口（签名与 v1 一致） ----------

def save_result(result):
    """保存一次完成结果（结构见 listening/CONTRACT.md）。本地必写；已配置则同步云端。"""
    with _LOCK:
        data = _read("results.json", [])
        data.append(result)
        _write("results.json", data)
    if persistence_enabled():
        ok = _remote_append_result(result)
        if not ok:
            print("[progress] 警告：成绩云端写入失败，仅存本地；复制成绩文本通道仍有效")


def list_results(course_id=None, student_id=None):
    data = None
    if persistence_enabled():
        data, _sha = _remote_read("results.json", [])
    if data is None:
        data = _read("results.json", [])
    if course_id:
        data = [r for r in data if r.get("course_id") == course_id]
    if student_id:
        data = [r for r in data if r.get("student_id") == student_id]
    return data


def _status_map():
    m = None
    if persistence_enabled():
        m, _sha = _remote_read("course_status.json", {})
    if m is None:
        m = _read("course_status.json", {})
    return m


def get_course_status(course_id):
    return _status_map().get(course_id, "open")


def set_course_status(course_id, status):
    if status not in COURSE_STATUSES:
        raise ValueError(status)
    with _LOCK:
        data = _read("course_status.json", {})
        data[course_id] = status
        _write("course_status.json", data)
    if persistence_enabled():
        cur, sha = _remote_read("course_status.json", {}, use_cache=False)
        if cur is not None:
            cur[course_id] = status
            try:
                _remote_write("course_status.json", cur, sha)
            except Exception:
                print("[progress] 警告：课程状态云端写入失败，仅存本地")


def all_courses():
    """扫描 content/listening 下全部课程，返回 {course_id: 元数据}（含状态）。"""
    from listening import models
    statuses = _status_map()
    out = {}
    for path in models.list_course_files():
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            cid = data.get("course_id")
            if cid:
                out[cid] = {"title": data.get("title", ""),
                            "week": data.get("week"), "day": data.get("day"),
                            "course_type": data.get("course_type", ""),
                            "open_date": data.get("open_date"),
                            "status": statuses.get(cid, "open")}
        except Exception:
            continue
    return out


def visible_courses():
    """儿童端可见课程 = 状态 open 且已到 open_date（未填则不限日期）。"""
    today = beijing_today()
    return {cid: m for cid, m in all_courses().items()
            if m["status"] == "open"
            and (not m.get("open_date") or m["open_date"] <= today)}
