# -*- coding: utf-8 -*-
"""Generate parent transcript and answer documents for review courses 41-50."""
import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(os.path.dirname(ROOT), "Week6")


def load(module, course_id):
    path = os.path.join(ROOT, "content", module, course_id + ".json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def clips_text(clips):
    return " / ".join(text for _role, text in clips)


def correct_option(question):
    return question["options"][question["answer"]]


def listening_doc():
    lines = [
        "# W01D41-50 听力答案与原文（家长版）",
        "",
        "> 范围：4A M1U1-M3U2 综合复习。仅供家长核对，儿童端不展示原文、答案和考点。",
        "",
    ]
    for number in range(41, 51):
        course = load("listening", "W01D%02d" % number)
        lines.extend(["## %s · %s" % (course["course_id"], course["title"]), "", course["scope"], ""])
        for section in course["sections"]:
            lines.extend(["### %s" % section["name"], ""])
            if section.get("shared_audio"):
                lines.append("**短文原文**：%s" % clips_text(section["passage_transcript"]))
                lines.append("")
            for question in section["questions"]:
                qid = question["id"]
                qtype = question["type"]
                if qtype == "word_choice":
                    detail = "原文：%s；答案：%s" % (clips_text(question["transcript"]), correct_option(question))
                elif qtype == "sentence_judge":
                    detail = "原文：%s；屏显：%s；答案：%s" % (
                        clips_text(question["transcript"]), question["display"],
                        "相同" if question["answer"] == "same" else "不同",
                    )
                elif qtype == "question_response":
                    detail = "问句：%s；答案：%s" % (clips_text(question["transcript"]), correct_option(question))
                elif qtype == "dialogue_choice":
                    detail = "对话：%s；问题：%s；答案：%s" % (
                        clips_text(question["transcript"][:-1]), question["question_text"], correct_option(question)
                    )
                else:
                    detail = "判断句：%s；答案：%s" % (
                        question["statement"], "正确" if question["answer"] == "true" else "错误"
                    )
                lines.append("%d. %s" % (qid, detail))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def speaking_doc():
    lines = [
        "# S01D41-50 口语课文与答案（家长版）",
        "",
        "> 每课 6 题 repeat + 2 题 QA。数字评分、弱词和录音只在家长端查看。",
        "",
    ]
    for number in range(41, 51):
        course = load("speaking", "S01D%02d" % number)
        lines.extend(["## %s · %s" % (course["course_id"], course["title"]), "", course["scope"], ""])
        for question in course["questions"]:
            if question["type"] == "repeat":
                lines.append("%d. Repeat: %s" % (question["id"], question["text"]))
            else:
                lines.append("%d. QA: %s -> %s（%s）" % (
                    question["id"], question["question"], question["expected"], question["hint"]
                ))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main():
    write(os.path.join(OUT_DIR, "W01D41-50_听力答案与原文_家长版.md"), listening_doc())
    write(os.path.join(OUT_DIR, "S01D41-50_口语课文与答案_家长版.md"), speaking_doc())
    print("parent documents written to", OUT_DIR)


if __name__ == "__main__":
    main()
