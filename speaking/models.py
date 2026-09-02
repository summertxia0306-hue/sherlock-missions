# -*- coding: utf-8 -*-
"""口语课程 JSON 加载与校验（镜像 listening/models.py 的"加载即校验"模式）。

课程文件：content/speaking/{course_id}.json，course_id 形如 S01D01。
题型两种（02_口语模块方案 §1，W1 只用这两种）：
  repeat：跟读。必填 text（孩子看到并跟读的句子）+ audio（示范音）
  qa：听问答。必填 question（仅家长可见）+ expected（目标答案，评测文本）
      + hint（屏显 emoji/提示，孩子据此知道答什么）+ audio（问题音）
"""
import datetime
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content", "speaking")
QUESTION_TYPES = ("repeat", "qa")
COURSE_TYPES = ("training", "weekly_review")
MAX_TAKES = 3          # 最多计 3 次有效评分；第 3 次仍不足 3 星可"先过这题"
DEMO_PLAYS = 2         # 示范/问题音可听次数（每次不到 3 星会重置回 2，见 page._consume_take）


class CourseValidationError(Exception):
    pass


def list_course_files():
    if not os.path.isdir(CONTENT_DIR):
        return []
    return sorted(os.path.join(CONTENT_DIR, f)
                  for f in os.listdir(CONTENT_DIR) if f.endswith(".json"))


def eval_text(q):
    """该题送讯飞评测的目标文本。"""
    return q["text"] if q["type"] == "repeat" else q["expected"]


def validate_course(course, check_audio=True):
    """→ 错误列表（空 = 通过）。"""
    errs = []

    def need(cond, msg):
        if not cond:
            errs.append(msg)

    cid = course.get("course_id", "")
    need(re.fullmatch(r"(?:S\d{2}D\d{2}|S[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})", cid or ""), "course_id 格式无效：%r" % cid)
    if cid.startswith("S") and "-" in cid:
        pair_id = cid[1:]
        need(course.get("pair_id") == pair_id and course.get("study_pack") == pair_id,
             "新学期课程 pair_id/study_pack 必须匹配 course_id")
    need(course.get("title"), "缺 title")
    need(course.get("course_type", "training") in COURSE_TYPES,
         "course_type 非法：%r" % course.get("course_type"))
    od = course.get("open_date")
    if od:
        try:
            datetime.datetime.strptime(od, "%Y-%m-%d")
        except ValueError:
            errs.append("open_date 格式应为 YYYY-MM-DD：%r" % od)

    qs = course.get("questions") or []
    need(qs, "没有题目")
    ids = [q.get("id") for q in qs]
    need(ids == list(range(1, len(qs) + 1)), "题号必须为 1..n 连续：%r" % ids)

    for q in qs:
        tag = "Q%s" % q.get("id")
        t = q.get("type")
        if t not in QUESTION_TYPES:
            errs.append("%s type 非法：%r" % (tag, t))
            continue
        if t == "repeat":
            need(q.get("text"), "%s repeat 缺 text" % tag)
        else:
            need(q.get("question"), "%s qa 缺 question" % tag)
            need(q.get("expected"), "%s qa 缺 expected" % tag)
            need(q.get("hint"), "%s qa 缺 hint（孩子的答题线索）" % tag)
        txt = (q.get("text") or q.get("expected") or "")
        need(not re.search(r"[一-鿿]", txt),
             "%s 评测文本不应含中文：%r" % (tag, txt[:30]))
        audio = q.get("audio", "")
        need(audio.startswith("static/audio/speaking/"),
             "%s audio 路径应在 static/audio/speaking/ 下：%r" % (tag, audio))
        if check_audio and audio:
            need(os.path.isfile(os.path.join(ROOT, audio)),
                 "%s 音频文件不存在：%s（先跑 tools/make_audio_speaking.py）" % (tag, audio))
    return errs


def load_course(course_id, check_audio=True):
    path = os.path.join(CONTENT_DIR, course_id + ".json")
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, encoding="utf-8") as fh:
        course = json.load(fh)
    errors = validate_course(course, check_audio=check_audio)
    if errors:
        raise CourseValidationError("课程 %s 校验失败：\n- %s"
                                    % (course_id, "\n- ".join(errors)))
    course["_by_id"] = {q["id"]: q for q in course["questions"]}
    return course


def all_courses():
    """{course_id: 元数据}（含家长可设状态，状态存储复用 storage.progress）。"""
    from storage import progress
    out = {}
    for path in list_course_files():
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            cid = d.get("course_id")
            if cid:
                out[cid] = {"title": d.get("title", ""), "week": d.get("week"),
                            "day": d.get("day"),
                            "course_type": d.get("course_type", "training"),
                            "publication_status": d.get(
                                "publication_status", "formal"
                            ),
                            "open_date": d.get("open_date"),
                            "status": progress.get_course_status(cid)}
        except Exception:
            continue
    return out


def visible_courses():
    from storage import progress
    today = progress.beijing_today()
    return {cid: m for cid, m in all_courses().items()
            if m.get("publication_status") == "formal"
            and m["status"] == "open"
            and (not m.get("open_date") or m["open_date"] <= today)}
