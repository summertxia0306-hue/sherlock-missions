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


def _state(course_id, data_kind):
    key = progress.course_session_key("L", course_id, data_kind)
    if key not in st.session_state:
        st.session_state[key] = {"idx": -1, "answers": {}, "plays": {},
                                 "t0": None, "result": None,
                                 "submitted": False, "attempt": 1,
                                 "in_correction": False, "correction_done": False,
                                 "corr": None, "data_kind": data_kind}
    return st.session_state[key]


def _reset_for_retry(s):
    """提交后"再做一次"：attempt+1 使所有控件 key 失效，全新开始。"""
    s["attempt"] += 1
    s["idx"] = -1
    s["answers"] = {}
    s["plays"] = {}
    s["t0"] = None
    s["result"] = None
    s["submitted"] = False
    s["in_correction"] = False
    s["correction_done"] = False
    s["corr"] = None


@st.cache_resource(show_spinner=False)
def _load_course(course_id):
    return models.load_course(course_id)


def get_last_result(student_id, course_id):
    """统一系统接口：取该生该课最近一次正式结果，无则 None。"""
    rs = progress.list_results(
        course_id=course_id, student_id=student_id, data_kind="formal"
    )
    return rs[-1] if rs else None


def _shown_courses(metas, today):
    shown = []
    for cid in sorted(metas):
        m = metas[cid]
        if m["status"] in ("hidden", "archived"):
            continue
        if m.get("open_date") and m["open_date"] > today:
            continue
        shown.append((cid, m))
    return shown


def _recommended_course_id(shown, done):
    for cid, meta in shown:
        if meta["status"] == "closed":
            continue
        if cid not in done:
            return cid
    return None


def listening_home(student_id):
    """听力主界面（2026-06-12 家长定）：列出已开发课程；完成状态由"提交"
    自动产生（提交过=已完成），非家长控制；已完成可重做；
    隐藏/删除/未到开放日期的课程不显示；关闭的显示但锁定。"""
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("## 🎧 听力练习")
    today = progress.beijing_today()
    done = progress.completed_course_ids(
        progress.list_results(student_id=student_id)
    )
    metas = progress.all_courses()
    shown = _shown_courses(metas, today)
    recommended = _recommended_course_id(shown, done)
    student_window = progress.course_window(shown, done)
    if recommended:
        st.info("⭐ 当前推荐：%s（%s）" % (recommended, metas[recommended]["title"]))
    else:
        st.info("本阶段已完成，请等下一批课程。")
    if not student_window:
        st.info("今天还没有听力任务，请告诉爸爸妈妈。")
        return
    for cid, m in student_window:
        c1, c2, c3 = st.columns([4, 2, 2])
        recommendation = "　⭐ 当前推荐" if cid == recommended else ""
        c1.markdown("**%s**%s" % (m["title"], recommendation))
        c1.caption("%s · 第%s周第%s天" % (cid, m["week"], m["day"]))
        c2.markdown("✅ 已完成" if cid in done else "⬜ 未完成")
        if m["status"] == "closed":
            c3.button("🔒 未开放", key="go_" + cid, disabled=True,
                      use_container_width=True)
        else:
            label = "再做一遍" if cid in done else "开始"
            if c3.button(label, key="go_" + cid, use_container_width=True,
                         type="secondary" if cid in done else "primary"):
                st.query_params["course_id"] = cid
                st.rerun()


def render_course(student_id, course_id, data_kind="formal"):
    """渲染一节课。提交模型：交卷只出成绩单；孩子点"提交"才写入
    storage.progress 并返回结果 dict（未提交返回 None）。可重做再提交，
    每次提交一条记录（attempt 递增）。"""
    st.markdown(_CSS, unsafe_allow_html=True)
    if st.button("← 返回家长端" if data_kind == "test" else "← 返回课程列表",
                 key="back_%s_%s" % (data_kind, course_id)):
        if data_kind == "test":
            st.query_params.clear()
            st.query_params["mode"] = "parent"
        elif "course_id" in st.query_params:
            del st.query_params["course_id"]
        st.rerun()
    try:
        course = _load_course(course_id)
    except models.CourseValidationError as e:
        st.error("课程数据有问题，请联系家长。\n\n" + str(e))
        return None
    except FileNotFoundError:
        st.error("找不到课程 %s" % course_id)
        return None

    s = _state(course_id, data_kind)
    if s.get("in_correction"):
        _correction_page(course, s)
        return None
    if s["result"]:
        _result_page(course, s)
        return s["result"] if s["submitted"] else None

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
                      s["plays"].get("test", 0),
                      key="au_test_%s_a%d" % (course["course_id"], s["attempt"]),
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
                      key="au_%s_%s_a%d" % (course["course_id"], qid, s["attempt"]))
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
                    key="r_%s_%s_a%d" % (course["course_id"], qid, s["attempt"]),
                    label_visibility="collapsed")
    if st.button("确认，下一题", type="primary", disabled=pick is None,
                 use_container_width=True, key="ok_%s_a%d" % (qid, s["attempt"])):
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
                      key="au_%s_%s_a%d" % (course["course_id"], sec_id, s["attempt"]),
                      label="短文还能听")
    merge_plays(s["plays"], sec_id, v)

    picks = {}
    for q in qs:
        picks[q["id"]] = st.radio("%d. %s" % (q["id"], q["statement"]),
                                  ["√ 对", "× 错"], index=None, horizontal=True,
                                  key="r_%s_%s_a%d" % (course["course_id"], q["id"], s["attempt"]))
    all_done = all(p is not None for p in picks.values())
    if st.button("全部完成，交卷", type="primary", disabled=not all_done,
                 use_container_width=True):
        for q in qs:
            s["answers"][q["id"]] = "true" if picks[q["id"]] == "√ 对" else "false"
        s["idx"] += 1
        _finish(course, s, student_id)
        st.rerun()


def _finish(course, s, student_id):
    """交卷：只生成结果不入库。入库发生在孩子点"提交"时（家长定的提交模型）。"""
    if s["result"]:
        return
    result = results_mod.build_result(course, s["answers"], s["plays"],
                                      student_id, s["t0"])
    result["data_kind"] = s["data_kind"]
    result["attempt"] = s["attempt"]
    if s["attempt"] > 1:
        result["result_text"] += "\n（本课第 %d 次完成·重做仅作参考）" % s["attempt"]
    s["result"] = result


def _result_page(course, s):
    result = s["result"]
    st.markdown("## 🎉 做完啦，辛苦了！")
    if s["attempt"] > 1:
        st.caption("本课第 %d 次完成" % s["attempt"])
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

    if not s["submitted"]:
        if st.button("📨 提交成绩给爸爸妈妈", type="primary", use_container_width=True,
                     key="submit_a%d" % s["attempt"]):
            progress.save_result(result)
            s["submitted"] = True
            st.rerun()
        st.caption("点提交后，爸爸妈妈在家长端就能看到这次成绩。不提交就没有记录哦。")
    else:
        st.success("成绩已提交 ✓ 爸爸妈妈在家长端可以看到了")
        if st.button("再做一次（重新开始本课）", use_container_width=True,
                     key="retry_a%d" % s["attempt"]):
            _reset_for_retry(s)
            st.rerun()

    if course.get("course_type") != "diagnostic" and result["wrong_answers"]:
        if s.get("correction_done"):
            st.info("✏️ 订正已完成：%s" % "  ".join(
                "%d%s" % (k, v) for k, v in sorted(s["corr"]["log"].items())))
        else:
            if st.button("✏️ 错题订正（%d 题）" % len(result["wrong_answers"]),
                         use_container_width=True, key="corr_a%d" % s["attempt"]):
                s["in_correction"] = True
                s["corr"] = {"queue": [w["id"] for w in result["wrong_answers"]],
                             "i": 0, "phase": "try1", "log": {}}
                st.rerun()
            st.caption("订正=把错题再听再做一遍，不用提交。"
                       "建议先订正，再复制成绩——这样成绩里带订正情况。")

    st.markdown('<div class="bignote">另外：点下面成绩框右上角的复制图标，'
                '打开微信发给<b>文件传输助手</b>（给 AI 老师登记错题本用）。</div>',
                unsafe_allow_html=True)
    st.code(result["result_text"], language=None)


def _correction_page(course, s):
    """错题订正流 v2（2026-06-12 家长修订）：
    第一遍 = 盲订正：只重听 + 重做，不显示原文、不显示任何答案信息；
    再错才显示【原文】（只有原文，永远不显示"你选了X/正确答案是Y"），
    看原文再听再做第二遍；第二遍无论对错都结束该题，全程不揭示答案。
    没有提交按钮（订正是教学动作，入档只作备注、不计掌握判定）。
    红线例外收窄：原文只在第二遍尝试时展示；正确答案任何时候不展示。"""
    c = s["corr"]
    queue = c["queue"]
    cid = course["course_id"]

    if c["i"] >= len(queue):
        st.markdown("## ✏️ 订正完成，真棒！")
        summary = "  ".join("%d%s" % (k, v) for k, v in sorted(c["log"].items()))
        st.write("订正结果：" + summary)
        st.caption("✓=订正一次就对　✓²=看原文后做对　✗=还要再练")
        if not s["correction_done"]:
            s["result"]["corrections"] = {str(k): v for k, v in c["log"].items()}
            s["result"]["result_text"] += "\n订正（教学用·不计判定）：" + summary
            s["correction_done"] = True
        st.caption("订正不用提交。回到成绩单记得复制成绩发给爸爸妈妈。")
        if st.button("返回成绩单", type="primary", use_container_width=True):
            s["in_correction"] = False
            st.rerun()
        return

    qid = queue[c["i"]]
    q = course["_by_id"][qid]
    phase = c["phase"]
    st.markdown("#### ✏️ 错题订正 %d / %d　·　第 %d 题" % (c["i"] + 1, len(queue), qid))

    if q["type"] == "passage_judge":
        sec = engine.section_by_id(course, q["_section_id"])
        lines = [t[1] for t in sec["passage_transcript"]]
        audio_path = sec["passage_audio"]
    else:
        role_name = {"n": "", "f": "女：", "m": "男："}
        lines = [role_name[r] + t for r, t in q["transcript"]]
        audio_path = q["audio"]

    def _question_widgets():
        if q["type"] == "sentence_judge":
            st.markdown('<div class="showsent">%s</div>' % q["display"],
                        unsafe_allow_html=True)
            return ["✓　一样 / 对", "✗　不一样 / 不对"], ["same", "different"]
        if q["type"] == "passage_judge":
            st.markdown('<div class="qtext">%s</div>' % q["statement"],
                        unsafe_allow_html=True)
            return ["√ 对", "× 错"], ["true", "false"]
        if q["type"] == "dialogue_choice":
            st.markdown('<div class="qtext">%s</div>' % q["question_text"],
                        unsafe_allow_html=True)
        return (["%s.　%s" % (chr(65 + i), o) for i, o in enumerate(q["options"])],
                list(range(len(q["options"]))))

    def _next_button(label_ok):
        nxt = "下一题" if c["i"] + 1 < len(queue) else "完成订正"
        if st.button(nxt, type="primary", use_container_width=True,
                     key="cnext_%s_a%d" % (qid, s["attempt"])):
            c["i"] += 1
            c["phase"] = "try1"
            st.rerun()

    if phase in ("try1", "try2"):
        if phase == "try1":
            st.caption("这道题刚才没做对。再听一遍，重新选一选！")
            ckey = "c%s" % qid
        else:
            st.warning("还不对哦。看看下面的原文，再听一遍，再试一次！")
            st.markdown('<div class="showsent" style="font-size:17px;text-align:left">'
                        '📖 原文：<br>' + "<br>".join(lines) + '</div>',
                        unsafe_allow_html=True)
            ckey = "d%s" % qid
        v = limited_audio(audio_path, ckey, 2, s["plays"].get(ckey, 0),
                          key="au_%s_%s_%s_a%d" % (ckey, cid, qid, s["attempt"]),
                          label="再听一遍，还能听")
        merge_plays(s["plays"], ckey, v)

        labels, canon = _question_widgets()
        pick = st.radio("再选一次", labels, index=None,
                        key="cr_%s_%s_%s_a%d" % (phase, cid, qid, s["attempt"]),
                        label_visibility="collapsed")
        if st.button("确认", type="primary", disabled=pick is None,
                     use_container_width=True,
                     key="cok_%s_%s_a%d" % (phase, qid, s["attempt"])):
            ok = engine.is_correct(q, canon[labels.index(pick)])
            if phase == "try1":
                if ok:
                    c["log"][qid] = "✓"
                    c["phase"] = "ok"
                else:
                    c["phase"] = "try2"
            else:
                c["log"][qid] = "✓²" if ok else "✗"
                c["phase"] = "ok" if ok else "fail"
            st.rerun()
    elif phase == "ok":
        st.success("答对啦！🎉")
        _next_button("ok")
    else:
        st.info("没关系，这道题我们以后再练，不着急。")
        _next_button("fail")


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

    st.session_state["parent_authenticated"] = True
    tab1, tab2, tab3, tab4 = st.tabs(
        ["成绩记录", "课程管理", "原文与答案", "家长测试"]
    )

    with tab1:
        if progress.persistence_enabled():
            st.caption("☁️ 云端持久化已启用（GitHub 私有结果库），重启不丢")
        else:
            st.warning("未配置云端持久化（Secrets 缺 RESULTS_REPO / RESULTS_TOKEN），"
                       "成绩仅存运行内存，重启即清空。配置方法见部署指南第 5 步。")
        rs = [
            r for r in progress.list_results()
            if r.get("module", "listening") != "speaking"
        ]
        if not rs:
            st.info("还没有成绩记录。")
        for r in reversed(rs):
            kind = r["data_kind"]
            kind_icon = "✅" if kind == "formal" else "🧪"
            kind_label = progress.data_kind_label(kind)
            tag_n = "（第%d次）" % r["attempt"] if r.get("attempt", 1) > 1 else ""
            with st.expander("%s %s · %s · %s · %d分%s"
                             % (kind_icon, kind_label, r.get("completed_at", "?"),
                                r["course_id"], r["score"], tag_n)):
                if kind == "test":
                    st.warning("开发/家长测试：仅用于验收和排障，不计入孩子完成状态或学习档案。")
                else:
                    st.success("正式学习记录")
                st.write({"数据类型": kind,
                          "用时(秒)": r.get("duration_seconds", 0),
                          "分项": r.get("section_scores", {}),
                          "播放次数": r.get("play_counts", {})})
                if r.get("wrong_answers"):
                    st.table(r["wrong_answers"])
                else:
                    st.success("全对")
                st.code(r.get("result_text", ""), language=None)

    with tab2:
        st.caption("**打开**=孩子列表可见可做（默认）｜**关闭**=列表显示但锁定🔒｜"
                   "**隐藏**=列表不显示｜**删除**=永久下架（网页端不真删 GitHub 文件，"
                   "重新部署会还原文件但状态保持下架）。"
                   "已配置云端持久化时状态重启不丢，否则重启回到打开。")
        st.caption("今天（北京时间）：%s ｜带开放日期的课程到期自动出现在孩子列表"
                   % progress.beijing_today())
        zh_label = {"open": "打开", "closed": "关闭", "hidden": "隐藏", "archived": "删除"}
        order = list(progress.COURSE_STATUSES)
        opts = [zh_label[k] for k in order]
        for cid, meta in sorted(progress.all_courses().items()):
            c1, c2 = st.columns([3, 2])
            extra = ("　·　%s 开放" % meta["open_date"]) if meta.get("open_date") else ""
            c1.write("**%s** %s%s" % (cid, meta["title"], extra))
            picked = c2.selectbox("状态", opts,
                                  index=order.index(meta["status"]),
                                  key="st_" + cid, label_visibility="collapsed")
            new = order[opts.index(picked)]
            if new != meta["status"]:
                progress.set_course_status(cid, new)
                st.rerun()

    with tab3:
        ids = sorted(progress.all_courses())
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

    with tab4:
        st.warning("此处打开的课程会把成绩标记为 test；测试记录不会点亮儿童端“已完成”。")
        for cid, meta in sorted(progress.all_courses().items()):
            c1, c2 = st.columns([4, 2])
            c1.write("**%s** %s" % (cid, meta["title"]))
            if c2.button("测试打开", key="ltest_" + cid,
                         use_container_width=True):
                st.query_params.clear()
                st.query_params["mode"] = "test"
                st.query_params["course_id"] = cid
                st.rerun()
