# -*- coding: utf-8 -*-
"""Streamlit 页面渲染：儿童端答题 + 家长端视图。

教学行为与旧 HTML 版等价（迁移指令 §七）：限次播放、短文共享次数、
分部分进度、交卷前不显示对错、自动计分、分项成绩、听满次数记录。
儿童端不展示：原文、答案、考点标签、家长操作（指令 §3.1）。
"""
import time

import streamlit as st

from . import engine, models
from . import results as results_mod
from .audio import limited_audio, merge_plays
from storage import progress

ZH_NUM = "一二三四五六七八九"

_CSS = """
<style>
div[role="radiogroup"] label p { font-size: 19px !important; }
div[role="radiogroup"] > label {
  border: 2px solid #d8dee5; border-radius: 12px; padding: 12px 14px;
  margin: 5px 0; width: 100%;
}
.showsent { background:#eef3f9; border-radius:12px; padding:14px 16px;
  font-size:20px; text-align:center; margin-bottom:8px; }
.qtext { font-size:19px; font-weight:600; text-align:center; margin-bottom:6px; }
.bignote { background:#fff8e1; border-left:4px solid #f0b429; padding:10px 14px;
  border-radius:6px; font-size:15px; color:#6b5510; }
.scorebig { font-size:46px; font-weight:700; text-align:center; color:#0f6e56; }
</style>
"""


def _state(course_id):
    key = "L_" + course_id
    if key not in st.session_state:
        st.session_state[key] = {"idx": -1, "answers": {}, "plays": {},
                                 "t0": None, "result": None}
    return st.session_state[key]


@st.cache_resource(show_spinner=False)
def _load_course(course_id):
    return models.load_course(course_id)


def get_last_result(student_id, course_id):
    """统一系统接口：取该生该课最近一次结果，无则 None。"""
    rs = progress.list_results(course_id=course_id, student_id=student_id)
    return rs[-1] if rs else None


def render_course(student_id, course_id):
    """渲染一节课。完成时结果已写入 storage.progress，并返回结果 dict。"""
    st.markdown(_CSS, unsafe_allow_html=True)
    try:
        course = _load_course(course_id)
    except models.CourseValidationError as e:
        st.error("课程数据有问题，请联系家长。\n\n" + str(e))
        return None
    except FileNotFoundError:
        st.error("找不到课程 %s" % course_id)
        return None

    s = _state(course_id)
    if s["result"]:
        _result_page(course, s["result"])
        return s["result"]

    steps = engine.build_steps(course)
    if s["idx"] < 0:
        _start_page(course, s)
    elif s["idx"] >= len(steps):
        _finish(course, s, student_id)
    else:
        step = steps[s["idx"]]
        _progress_header(course, s)
        if step["t"] == "intro":
            _intro_page(course, s, step["sec"])
        elif step["t"] == "q":
            _question_page(course, s, step["qid"], steps, student_id)
        else:
            _passage_page(course, s, step["sec"], steps, student_id)
    return None


def _progress_header(course, s):
    n = len(course["_questions"])
    done = engine.answered_count(course, s["answers"])
    st.progress(done / n, text="已完成 %d / %d 题" % (done, n))


def _start_page(course, s):
    st.markdown("## 🎧 %s" % course["title"])
    st.caption("Week%s · 第%s天 · 共 %d 题 · 大约 %s 分钟"
               % (course["week"], course["day"],
                  len(course["_questions"]), course.get("est_minutes", 20)))
    st.markdown('<div class="bignote">小朋友：每道题先<b>点大绿圆按钮</b>听录音，'
                '再选答案，最后点蓝色按钮进入下一题。听不懂也没关系，选一个你觉得'
                '最像的。做完才能看到对错哦。</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("**第一步：点下面的按钮试试声音**")
    v = limited_audio(course["test_audio"], "test", 99,
                      s["plays"].get("test", 0), key="au_test_" + course["course_id"],
                      label="试音，想听几遍都行，还能听")
    tried = merge_plays(s["plays"], "test", v) > 0
    if st.button("开始做题", type="primary", disabled=not tried,
                 use_container_width=True):
        s["idx"] = 0
        s["t0"] = time.time()
        st.rerun()
    if not tried:
        st.caption("先点上面的绿色按钮试音，听到声音后就可以开始啦")


def _intro_page(course, s, sec_id):
    sec = engine.section_by_id(course, sec_id)
    sec_no = [x["id"] for x in course["sections"]].index(sec_id)
    st.markdown("## 第%s部分 · %s" % (ZH_NUM[sec_no], sec["name"]))
    st.write(sec["tip"])
    if sec.get("shared_audio"):
        st.caption("短文可以听 %d 遍（%d 个小题共用）" % (sec["max_plays"], len(sec["questions"])))
    else:
        st.caption("共 %d 题 · 每题可以听 %d 遍" % (len(sec["questions"]), sec["max_plays"]))
    if st.button("开始这部分", type="primary", use_container_width=True):
        s["idx"] += 1
        st.rerun()


def _question_page(course, s, qid, steps, student_id):
    q = course["_by_id"][qid]
    st.markdown("#### 第 %d 题" % qid)
    st.caption(q["_section_name"] + "：" + engine.section_by_id(course, q["_section_id"])["tip"])

    v = limited_audio(q["audio"], qid, q["_max_plays"], s["plays"].get(qid, 0),
                      key="au_%s_%s" % (course["course_id"], qid))
    merge_plays(s["plays"], qid, v)

    if q["type"] == "sentence_judge":
        st.markdown('<div class="showsent">%s</div>' % q["display"],
                    unsafe_allow_html=True)
        labels = ["✓　一样 / 对", "✗　不一样 / 不对"]
        canon = ["same", "different"]
    else:
        if q["type"] == "dialogue_choice":
            st.markdown('<div class="qtext">%s</div>' % q["question_text"],
                        unsafe_allow_html=True)
        labels = ["%s.　%s" % (chr(65 + i), opt) for i, opt in enumerate(q["options"])]
        canon = list(range(len(q["options"])))

    pick = st.radio("选择答案", labels, index=None,
                    key="r_%s_%s" % (course["course_id"], qid),
                    label_visibility="collapsed")
    if st.button("确认，下一题", type="primary", disabled=pick is None,
                 use_container_width=True, key="ok_%s" % qid):
        s["answers"][qid] = canon[labels.index(pick)]
        s["idx"] += 1
        if s["idx"] >= len(steps):
            _finish(course, s, student_id)
        st.rerun()


def _passage_page(course, s, sec_id, steps, student_id):
    sec = engine.section_by_id(course, sec_id)
    qs = sec["questions"]
    st.markdown("#### 第 %d–%d 题 · %s" % (qs[0]["id"], qs[-1]["id"], sec["name"]))
    st.caption(sec["tip"])

    v = limited_audio(sec["passage_audio"], sec_id, sec["max_plays"],
                      s["plays"].get(sec_id, 0),
                      key="au_%s_%s" % (course["course_id"], sec_id),
                      label="短文还能听")
    merge_plays(s["plays"], sec_id, v)

    picks = {}
    for q in qs:
        picks[q["id"]] = st.radio("%d. %s" % (q["id"], q["statement"]),
                                  ["√ 对", "× 错"], index=None, horizontal=True,
                                  key="r_%s_%s" % (course["course_id"], q["id"]))
    all_done = all(p is not None for p in picks.values())
    if st.button("全部完成，交卷", type="primary", disabled=not all_done,
                 use_container_width=True):
        for q in qs:
            s["answers"][q["id"]] = "true" if picks[q["id"]] == "√ 对" else "false"
        s["idx"] += 1
        _finish(course, s, student_id)
        st.rerun()


def _finish(course, s, student_id):
    if s["result"]:
        return
    result = results_mod.build_result(course, s["answers"], s["plays"],
                                      student_id, s["t0"])
    progress.save_result(result)
    s["result"] = result


def _result_page(course, result):
    st.markdown("## 🎉 做完啦，辛苦了！")
    st.markdown('<div class="scorebig">%d <span style="font-size:20px;color:#5b6b7a">'
                '/ %d</span></div>' % (result["score"], course["scoring"]["total"]),
                unsafe_allow_html=True)
    rows = []
    per = course["scoring"]["per_question"]
    for sec in course["sections"]:
        rows.append({"部分": sec["name"],
                     "得分": "%d / %d" % (result["section_scores"][sec["id"]],
                                          per * len(sec["questions"]))})
    st.table(rows)
    st.markdown('<div class="bignote"><b>重要：先回传成绩再关页面！</b><br>'
                '点下面成绩框右上角的复制图标，打开微信发给<b>文件传输助手</b>；'
                '或者直接<b>截图本页</b>发到微信。</div>', unsafe_allow_html=True)
    st.code(result["result_text"], language=None)


def parent_view():
    st.markdown("## 👨‍👩‍👦 家长端 · 听力")
    try:
        expected = st.secrets.get("PARENT_PASSWORD", "")
    except Exception:
        expected = ""
    if not expected:
        st.warning("尚未在 Streamlit 后台设置 PARENT_PASSWORD（Settings → Secrets），"
                   "临时密码为 xlk2026，部署后请尽快设置。")
        expected = "xlk2026"
    pwd = st.text_input("家长密码", type="password")
    if pwd != expected:
        if pwd:
            st.error("密码不对")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["成绩记录", "课程管理", "原文与答案"])

    with tab1:
        rs = progress.list_results()
        if not rs:
            st.info("本次运行期内还没有成绩记录（服务重启会清空，复制成绩通道是权威渠道）。")
        for r in reversed(rs):
            with st.expander("%s · %s · %d分" % (r.get("completed_at", "?"),
                                                 r["course_id"], r["score"])):
                st.write({"用时(秒)": r["duration_seconds"],
                          "分项": r["section_scores"],
                          "播放次数": r["play_counts"]})
                if r["wrong_answers"]:
                    st.table(r["wrong_answers"])
                else:
                    st.success("全对")
                st.code(r.get("result_text", ""), language=None)

    with tab2:
        st.caption("hidden/closed/archived 的课程，孩子端都不可见；"
                   "状态存在运行目录，服务重启会回到 open。固定课件资产在 GitHub，"
                   "此处不提供删除。")
        st.caption("今天（北京时间）：%s ｜带开放日期的课程到期自动对孩子可见"
                   % progress.beijing_today())
        for cid, meta in progress.all_courses().items():
            c1, c2 = st.columns([3, 2])
            extra = ("　·　%s 开放" % meta["open_date"]) if meta.get("open_date") else ""
            c1.write("**%s** %s%s" % (cid, meta["title"], extra))
            new = c2.selectbox("状态", progress.COURSE_STATUSES,
                               index=progress.COURSE_STATUSES.index(meta["status"]),
                               key="st_" + cid, label_visibility="collapsed")
            if new != meta["status"]:
                progress.set_course_status(cid, new)
                st.rerun()

    with tab3:
        ids = list(progress.all_courses())
        if not ids:
            st.info("没有课程")
            return
        cid = st.selectbox("选择课程", ids)
        try:
            course = models.load_course(cid, check_audio=False)
        except models.CourseValidationError as e:
            st.error(str(e))
            return
        role_name = {"n": "旁白", "f": "女", "m": "男"}
        for sec in course["sections"]:
            st.markdown("**%s**（每题 %d 遍）" % (sec["name"], sec["max_plays"]))
            if sec.get("shared_audio"):
                st.write("短文原文：" + " ".join(t[1] for t in sec["passage_transcript"]))
            for q in sec["questions"]:
                lines = []
                if q["type"] != "passage_judge":
                    lines = ["%s: %s" % (role_name[r], t) for r, t in q["transcript"]]
                ans = engine.pick_label(q, q["answer"])
                if q["type"] in models.CHOICE_TYPES:
                    ans += ". " + q["options"][q["answer"]]
                body = q.get("display") or q.get("statement") or q.get("question_text") or ""
                st.markdown("- **Q%d** %s　｜录音：%s　｜答案：**%s**　｜考点：%s%s"
                            % (q["id"], body, " / ".join(lines), ans, q["tag"],
                               ("　｜" + q["parent_note"]) if q.get("parent_note") else ""))
