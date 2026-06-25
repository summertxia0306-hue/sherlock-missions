# -*- coding: utf-8 -*-
"""计分、错题汇总、结果契约组装（纯逻辑，不依赖 streamlit）。

结果结构是与统一系统（Codex）的稳定契约，字段说明见 listening/CONTRACT.md。
result_text 是给"复制成绩→微信→AI 入档"兜底通道的人读文本，
格式与旧 HTML 版成绩单保持一致，AI 侧解析逻辑不用改。
"""
import time

from . import engine


def build_result(course, answers, plays_used, student_id,
                 started_at, finished_at=None):
    finished_at = finished_at or time.time()
    per = course["scoring"]["per_question"]

    section_scores = {}
    section_names = {}
    details = {}
    wrong = []
    used_up = []

    for sec in course["sections"]:
        section_scores[sec["id"]] = 0
        section_names[sec["id"]] = sec["name"]
        details[sec["id"]] = []

    for q in course["_questions"]:
        sid = q["_section_id"]
        pick = answers.get(q["id"])
        ok = engine.is_correct(q, pick)
        if ok:
            section_scores[sid] += per
            details[sid].append("%d✓" % q["id"])
        else:
            picked = engine.pick_label(q, pick)
            correct = engine.pick_label(q, q["answer"])
            details[sid].append("%d✗选%s(应%s)" % (q["id"], picked, correct))
            wrong.append({"id": q["id"], "picked": picked, "correct": correct,
                          "tag": q["tag"], "section": sid})
        play_key = q["_section_id"] if q["_shared_audio"] else q["id"]
        if not q["_shared_audio"] and plays_used.get(play_key, 0) >= q["_max_plays"]:
            used_up.append("Q%d" % q["id"])

    total = sum(section_scores.values())
    duration = int(finished_at - started_at) if started_at else 0

    result = {
        "student_id": student_id,
        "course_id": course["course_id"],
        "data_kind": "formal",
        "status": "completed",
        "score": total,
        "duration_seconds": duration,
        "section_scores": section_scores,
        "wrong_answers": wrong,
        "play_counts": {str(k): v for k, v in plays_used.items()},
        "completed_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(finished_at)),
    }
    result["result_text"] = _result_text(course, result, details, used_up)
    return result


def _result_text(course, result, details, used_up):
    n = len(course["_questions"])
    lines = []
    lines.append("【夏洛恪·%s %s】%s 用时约%d分钟"
                 % (course["title"], course["course_id"],
                    result["completed_at"], round(result["duration_seconds"] / 60.0)))
    lines.append("总分 %d/%d（%d题×%d分）"
                 % (result["score"], course["scoring"]["total"],
                    n, course["scoring"]["per_question"]))
    zh = "一二三四五六七八九"
    for i, sec in enumerate(course["sections"]):
        sid = sec["id"]
        lines.append("%s %s %d/%d：%s"
                     % (zh[i], sec["name"], result["section_scores"][sid],
                        course["scoring"]["per_question"] * len(sec["questions"]),
                        " ".join(details[sid])))
    lines.append("听满次数的题：" + ("、".join(used_up) if used_up else "无"))
    lines.append("（请把本段完整发给AI登记档案）")
    return "\n".join(lines)
