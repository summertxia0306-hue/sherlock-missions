# -*- coding: utf-8 -*-
"""课程数据加载与校验。不依赖 streamlit，可独立测试。

课程 JSON 结构见 content/listening/W01D01.json 与 10_Streamlit迁移设计_v1。
加载即校验：校验失败抛 CourseValidationError 并列出全部问题，拒绝加载。
"""
import json
import os
import re

CHOICE_TYPES = ("word_choice", "question_response", "dialogue_choice")
JUDGE_TYPES = ("sentence_judge", "passage_judge")
JUDGE_ANSWERS = {"sentence_judge": ("same", "different"),
                 "passage_judge": ("true", "false")}
VALID_ROLES = ("n", "f", "m")


class CourseValidationError(Exception):
    def __init__(self, course_id, errors):
        self.course_id = course_id
        self.errors = errors
        super().__init__("课程 %s 校验失败：\n- %s" % (course_id, "\n- ".join(errors)))


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def content_dir():
    return os.path.join(repo_root(), "content", "listening")


def list_course_files():
    d = content_dir()
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json"))


def load_course(path_or_id, check_audio=True):
    """按文件路径或课程 ID 加载课程；返回带 _questions 扁平索引的 dict。"""
    path = path_or_id
    if not os.path.sep in path_or_id and not path_or_id.endswith(".json"):
        path = os.path.join(content_dir(), path_or_id + ".json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    errors = validate_course(data, check_audio=check_audio)
    if errors:
        raise CourseValidationError(data.get("course_id", path), errors)
    _index(data)
    return data


def _index(course):
    """建扁平题目索引并把 section 级字段下放到每题。"""
    flat = []
    for sec in course["sections"]:
        for q in sec["questions"]:
            q["_section_id"] = sec["id"]
            q["_section_name"] = sec["name"]
            q["_max_plays"] = sec["max_plays"]
            q["_shared_audio"] = bool(sec.get("shared_audio"))
            flat.append(q)
    course["_questions"] = flat
    course["_by_id"] = {q["id"]: q for q in flat}


def validate_course(data, check_audio=True):
    errors = []
    root = repo_root()

    def need(obj, field, where):
        if field not in obj or obj[field] in (None, "", []):
            errors.append("%s 缺少字段 %s" % (where, field))
            return False
        return True

    for f in ("course_id", "title", "week", "day", "course_type", "sections", "scoring"):
        need(data, f, "课程")
    if errors:
        return errors

    od = data.get("open_date")
    if od is not None:
        if not isinstance(od, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", od):
            errors.append("open_date 必须是 YYYY-MM-DD 格式，当前: %r" % od)

    cid = data["course_id"]
    if not re.fullmatch(r"(?:W\d{2}D\d{2}|L[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})", cid or ""):
        errors.append("course_id 格式无效: %r" % cid)
    if cid.startswith("L"):
        pair_id = cid[1:]
        if data.get("pair_id") != pair_id or data.get("study_pack") != pair_id:
            errors.append("新学期课程 pair_id/study_pack 必须匹配 course_id")
    seen_ids = set()
    total_questions = 0

    if check_audio and need(data, "test_audio", cid):
        if not os.path.isfile(os.path.join(root, data["test_audio"])):
            errors.append("试音音频不存在: %s" % data["test_audio"])

    for sec in data["sections"]:
        sname = "%s/%s" % (cid, sec.get("id", "?"))
        for f in ("id", "name", "tip", "max_plays", "questions"):
            need(sec, f, sname)
        mp = sec.get("max_plays")
        if not isinstance(mp, int) or mp < 1 or mp > 9:
            errors.append("%s max_plays 必须是 1-9 的整数，当前: %r" % (sname, mp))
        if sec.get("shared_audio"):
            if need(sec, "passage_audio", sname) and check_audio:
                if not os.path.isfile(os.path.join(root, sec["passage_audio"])):
                    errors.append("%s 短文音频不存在: %s" % (sname, sec["passage_audio"]))
            need(sec, "passage_transcript", sname)

        for q in sec.get("questions", []):
            qname = "%s/Q%s" % (sname, q.get("id", "?"))
            total_questions += 1
            qid = q.get("id")
            if qid in seen_ids:
                errors.append("%s 题号重复" % qname)
            seen_ids.add(qid)
            if not need(q, "type", qname):
                continue
            t = q["type"]
            if t in CHOICE_TYPES:
                if need(q, "options", qname):
                    opts = q["options"]
                    if len(opts) != len(set(opts)):
                        errors.append("%s 选项重复" % qname)
                    ans = q.get("answer")
                    if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                        errors.append("%s answer 必须是 0-%d 的下标，当前: %r"
                                      % (qname, len(opts) - 1, ans))
                if t == "dialogue_choice":
                    need(q, "question_text", qname)
            elif t in JUDGE_TYPES:
                if q.get("answer") not in JUDGE_ANSWERS[t]:
                    errors.append("%s answer 必须是 %s，当前: %r"
                                  % (qname, "/".join(JUDGE_ANSWERS[t]), q.get("answer")))
                if t == "sentence_judge":
                    need(q, "display", qname)
                if t == "passage_judge":
                    need(q, "statement", qname)
            else:
                errors.append("%s 未知题型: %s" % (qname, t))

            need(q, "tag", qname)
            if t != "passage_judge":
                if need(q, "transcript", qname):
                    for part in q["transcript"]:
                        if (not isinstance(part, list) or len(part) != 2
                                or part[0] not in VALID_ROLES or not part[1].strip()):
                            errors.append("%s transcript 片段格式错: %r" % (qname, part))
                if need(q, "audio", qname) and check_audio:
                    if not os.path.isfile(os.path.join(root, q["audio"])):
                        errors.append("%s 音频不存在: %s" % (qname, q["audio"]))

    per = data.get("scoring", {}).get("per_question")
    total = data.get("scoring", {}).get("total")
    if not isinstance(per, int) or not isinstance(total, int) or per * total_questions != total:
        errors.append("计分不一致: %s题 × %r分 ≠ %r" % (total_questions, per, total))
    return errors
