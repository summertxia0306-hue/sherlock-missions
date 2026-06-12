# -*- coding: utf-8 -*-
"""口语流程纯逻辑：星级、规则化评语、最佳成绩合并、结果组装。无 streamlit 依赖，可单测。

星级阈值（W1 从宽，2026-06-12 家长冒烟后定；待孩子真实分数分布后校准）：
  ≥75 → ⭐⭐⭐　≥50 → ⭐⭐　其余 → ⭐　拒识/无分 → 0星(算未完成本次录音)
评语原则（家长 2026-06-12 要求）：不给笼统评语，按逐词得分给具体提示——
  哪个词没读到、哪个词要再练；孩子端永不显示数字分数。
"""
import datetime

STAR3, STAR2 = 75, 50
WEAK_WORD = 40         # 词得分低于此 → "要再练"
MISS_WORD = 5          # 词得分低于此 → 视为"没读到"


def stars(total, is_rejected=False):
    if is_rejected or total is None:
        return 0
    if total >= STAR3:
        return 3
    if total >= STAR2:
        return 2
    return 1


def word_lights(eval_res):
    """逐词红绿灯：[(word, 'good'|'weak'|'miss')]"""
    out = []
    for w in eval_res.get("words", []):
        s = w.get("score")
        if s is None or s < MISS_WORD:
            out.append((w["word"], "miss"))
        elif s < WEAK_WORD:
            out.append((w["word"], "weak"))
        else:
            out.append((w["word"], "good"))
    return out


def feedback(eval_res):
    """→ (孩子看的中文提示, 弱词列表)。具体到词，不灌鸡汤。

    一致性硬规则（2026-06-12 家长实测纠错：曾出现 1 星却夸"真棒"）：
    评语必须与星级同向——不满 3 星时绝不说"真棒"，必须点出最该练的词；
    逐词都不差但总分低时，点名得分最低的词或提示整句连贯度。"""
    if eval_res.get("is_rejected") or eval_res.get("total") is None:
        return "好像没有听清你读的这句话。先听一遍示范，再大声读一次吧！", []
    lights = word_lights(eval_res)
    miss = [w for w, c in lights if c == "miss"]
    weak = [w for w, c in lights if c == "weak"]
    if miss or weak:
        parts = []
        if miss:
            parts.append("这些单词没读到：%s" % "、".join(miss))
        if weak:
            parts.append("这些单词再跟老师读一遍：%s" % "、".join(weak))
        return "。".join(parts) + "。再听一遍示范，重录试试！", miss + weak
    if stars(eval_res.get("total"), eval_res.get("is_rejected")) >= 3:
        return "读得真棒！每个单词都很清楚！", []
    # 没有明显坏词但总分不到三星 → 点名得分最低的词（一致性兜底）
    scored = [w for w in eval_res.get("words", []) if w.get("score") is not None]
    low = [w["word"] for w in sorted(scored, key=lambda x: x["score"])[:2]
           if w["score"] < 75]
    if low:
        return ("还差一点点！把这几个单词读得更清楚、更响亮：%s。"
                "听一遍示范再重录，冲三颗星！" % "、".join(low)), low
    return "单词都读对了！整句再读得连贯、响亮一点就更好，重录冲三颗星！", []


def best_take(takes):
    """多次录音取最高分的一次（都拒识则取最后一次）。"""
    if not takes:
        return None
    scored = [t for t in takes if t.get("total") is not None and not t.get("is_rejected")]
    if not scored:
        return takes[-1]
    return max(scored, key=lambda t: t["total"])


def build_result(course, qstates, student_id, t0):
    """组装结果（提交模型：调用方在孩子点"提交"时入库）。

    qstates: {qid: {"takes": [eval_res…], "recordings": [path…]}}
    结果含 listening 家长端兼容键（score/section_scores/wrong_answers/play_counts），
    防止统一成绩列表渲染时 KeyError。
    """
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    q_results, star_sum, score_sum, scored_n = [], 0, 0.0, 0
    for q in course["questions"]:
        st_q = qstates.get(q["id"], {})
        best = best_take(st_q.get("takes", []))
        n_stars = stars(best["total"], best.get("is_rejected")) if best else 0
        weak = feedback(best)[1] if best else []
        if best and best.get("total") is not None:
            score_sum += best["total"]
            scored_n += 1
        star_sum += n_stars
        take_stars = [(-1 if t.get("error")
                       else stars(t.get("total"), t.get("is_rejected")))
                      for t in st_q.get("takes", [])]
        q_results.append({
            "take_stars": take_stars,   # 每次录音星级（-1=评分失败），家长端/回传可见
            "id": q["id"], "type": q["type"],
            "text": q.get("text") or q.get("expected"),
            "stars": n_stars,
            "best_total": best.get("total") if best else None,
            "accuracy": best.get("accuracy") if best else None,
            "fluency": best.get("fluency") if best else None,
            "integrity": best.get("integrity") if best else None,
            "is_rejected": bool(best.get("is_rejected")) if best else True,
            "takes": len(st_q.get("takes", [])),
            "weak_words": weak,
            "recordings": st_q.get("recordings", []),
            "tag": q.get("tag", ""),
        })
    avg = round(score_sum / scored_n) if scored_n else 0
    result = {
        "student_id": student_id,
        "course_id": course["course_id"],
        "module": "speaking",
        "status": "completed",
        "score": avg,                       # 平均总分（家长看）
        "stars_total": star_sum,
        "stars_max": 3 * len(course["questions"]),
        "question_results": q_results,
        "duration_seconds": int((datetime.datetime.utcnow().timestamp()) - t0) if t0 else 0,
        "completed_at": now.strftime("%Y-%m-%d %H:%M"),
        # listening 家长端成绩列表兼容键
        "section_scores": {}, "wrong_answers": [], "play_counts": {},
    }
    result["result_text"] = _result_text(course, result)
    return result


def _result_text(course, result):
    type_zh = {"repeat": "跟读", "qa": "问答"}
    lines = ["【夏洛恪·口语 %s】%s" % (course["course_id"], result["completed_at"]),
             "%s｜总星 %d/%d｜平均分 %d｜用时 %d 分" % (
                 course["title"], result["stars_total"], result["stars_max"],
                 result["score"], max(1, result["duration_seconds"] // 60))]
    for qr in result["question_results"]:
        line = "Q%d %s %s：%s 分%s（录%d次）" % (
            qr["id"], type_zh.get(qr["type"], qr["type"]), qr["text"],
            "⭐" * qr["stars"] if qr["stars"] else "0星",
            "" if qr["best_total"] is None else " %d" % round(qr["best_total"]),
            qr["takes"])
        if len(qr.get("take_stars", [])) > 1:
            line += "｜各次星:" + "/".join(str(x) for x in qr["take_stars"])
        if qr["weak_words"]:
            line += "｜弱词: " + ",".join(qr["weak_words"])
        if qr["is_rejected"]:
            line += "｜未识别到有效朗读"
        lines.append(line)
    return "\n".join(lines)
