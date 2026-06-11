# -*- coding: utf-8 -*-
"""答题流程状态机（纯逻辑，不依赖 streamlit）。

step 序列：每个 section 一个 intro；普通题每题一步；shared_audio 的
section（短文）整组一步。与旧 HTML 版行为一致。
"""
from . import models


def build_steps(course):
    steps = []
    for sec in course["sections"]:
        steps.append({"t": "intro", "sec": sec["id"]})
        if sec.get("shared_audio"):
            steps.append({"t": "passage", "sec": sec["id"]})
        else:
            for q in sec["questions"]:
                steps.append({"t": "q", "qid": q["id"]})
    return steps


def section_by_id(course, sec_id):
    for sec in course["sections"]:
        if sec["id"] == sec_id:
            return sec
    raise KeyError(sec_id)


def is_correct(question, pick):
    """pick：选择题为选项下标 int；判断题为字符串（same/different/true/false）。"""
    if pick is None:
        return False
    return pick == question["answer"]


def pick_label(question, pick):
    """把作答转成人读标签：A/B/C 或 √/×；None → 未答。"""
    if pick is None:
        return "未答"
    t = question["type"]
    if t in models.CHOICE_TYPES:
        return chr(65 + pick) if isinstance(pick, int) else str(pick)
    if t == "sentence_judge":
        return "√" if pick == "same" else "×"
    if t == "passage_judge":
        return "√" if pick == "true" else "×"
    return str(pick)


def answered_count(course, answers):
    return sum(1 for q in course["_questions"] if answers.get(q["id"]) is not None)


def all_answered(course, answers):
    return answered_count(course, answers) == len(course["_questions"])
