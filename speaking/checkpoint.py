# -*- coding: utf-8 -*-
"""Small, private speaking progress snapshots; never a learning result."""
import hashlib
import json


VERSION = 1


def _signature(course):
    questions = json.dumps(course["questions"], sort_keys=True,
                           ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(questions.encode("utf-8")).hexdigest()


def snapshot(course, state):
    """Save only what is needed to continue and build the eventual result."""
    questions = {}
    for qid, item in state.get("q", {}).items():
        questions[str(qid)] = {
            "takes": [{key: value for key, value in take.items() if key != "raw_xml"}
                      for take in item.get("takes", [])],
            "recordings": list(item.get("recordings", [])),
            "recording_records": list(item.get("recording_records", [])),
            "done": bool(item.get("done")),
            "passed_by_safety": bool(item.get("passed_by_safety")),
        }
    return {
        "version": VERSION,
        "course_signature": _signature(course),
        "idx": int(state["idx"]),
        "attempt": int(state["attempt"]),
        "t0": state.get("t0"),
        "submitted": bool(state.get("submitted")),
        "q": questions,
    }


def restore(course, saved):
    """Reject stale/corrupt snapshots rather than attach answers to new content."""
    if not isinstance(saved, dict) or saved.get("version") != VERSION:
        return None
    if saved.get("course_signature") != _signature(course):
        return None
    n = len(course["questions"])
    idx = saved.get("idx")
    attempt = saved.get("attempt")
    if not isinstance(idx, int) or not 0 <= idx <= n:
        return None
    if not isinstance(attempt, int) or attempt < 1:
        return None
    if saved.get("submitted") and idx != n:
        return None
    raw_q = saved.get("q")
    if not isinstance(raw_q, dict):
        return None
    qstates = {}
    for key, item in raw_q.items():
        if not isinstance(key, str) or not key.isdecimal() or not isinstance(item, dict):
            return None
        qid = int(key)
        if not 1 <= qid <= n or not isinstance(item.get("takes"), list):
            return None
        qstates[qid] = item
    if any(not qstates.get(qid, {}).get("done") for qid in range(1, idx + 1)):
        return None
    return {"idx": idx, "attempt": attempt, "t0": saved.get("t0"),
            "submitted": bool(saved.get("submitted")), "q": qstates}
