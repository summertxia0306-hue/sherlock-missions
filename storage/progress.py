# -*- coding: utf-8 -*-
"""进度/结果/课程状态的读写接口。

v1 实现 = 运行目录 _runtime/ 下的 JSON 文件：
- Community Cloud 重启/重部署会清空（设计已知，复制成绩通道兜底）。
- 接口保持稳定，统一架构换持久化后端时只改本文件。
"""
import datetime
import json
import os
import threading

_LOCK = threading.Lock()


def beijing_today():
    """Streamlit Cloud 服务器是 UTC，按北京时间(UTC+8)算"今天"。"""
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
COURSE_STATUSES = ("open", "closed", "hidden", "archived")


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


def save_result(result):
    """保存一次完成结果（结构见 listening/CONTRACT.md）。"""
    with _LOCK:
        data = _read("results.json", [])
        data.append(result)
        _write("results.json", data)


def list_results(course_id=None, student_id=None):
    data = _read("results.json", [])
    if course_id:
        data = [r for r in data if r.get("course_id") == course_id]
    if student_id:
        data = [r for r in data if r.get("student_id") == student_id]
    return data


def get_course_status(course_id):
    return _read("course_status.json", {}).get(course_id, "open")


def set_course_status(course_id, status):
    if status not in COURSE_STATUSES:
        raise ValueError(status)
    with _LOCK:
        data = _read("course_status.json", {})
        data[course_id] = status
        _write("course_status.json", data)


def all_courses():
    """扫描 content/listening 下全部课程，返回 {course_id: 元数据}（含状态）。"""
    from listening import models
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
                            "status": get_course_status(cid)}
        except Exception:
            continue
    return out


def visible_courses():
    """儿童端可见课程 = 状态 open 且已到 open_date（未填则不限日期）。

    open_date 支持"周日一次性推 5 课、周一到周五逐日自动解锁"的批量模式，
    不依赖运行期状态，服务器重启不影响。
    """
    today = beijing_today()
    return {cid: m for cid, m in all_courses().items()
            if m["status"] == "open"
            and (not m.get("open_date") or m["open_date"] <= today)}
