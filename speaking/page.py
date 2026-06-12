# -*- coding: utf-8 -*-
"""口语模块页面：儿童端主界面/课件流 + 家长端。

镜像 listening/page.py 的全部模式（提交模型/信息隔离/课程状态/主界面卡片）。
口语特有规则（02_方案 + 2026-06-12 家长反馈）：
- 每题最多录 3 次取最高（重录机制即订正，无独立订正流）
- 孩子端只见星级 + 逐词红绿灯 + 具体到词的中文提示，永不见数字分数
- 示范/问题音可听 2 遍（复用 listening 限次播放组件）
- 每次"就用这个"的录音：先评分，后台上传私有库（失败不阻塞做题）
"""
import os
import time

import streamlit as st

from . import engine, ise, models, recorder
from listening.audio import limited_audio, merge_plays  # 只调用，不改其内部
from storage import progress

_CSS = """
<style>
.bigsent { background:#eef3f9; border-radius:14px; padding:18px;
  font-size:26px; font-weight:700; text-align:center; margin:8px 0; }
.hintbox { background:#fff7ed; border:2px dashed #fb923c; border-radius:14px;
  padding:16px; font-size:24px; font-weight:700; text-align:center; margin:8px 0; }
.starbig { font-size:44px; text-align:center; }
.fb { background:#f0fdf4; border-left:4px solid #16a34a; padding:10px 14px;
  border-radius:8px; font-size:17px; }
.fb.bad { background:#fef2f2; border-color:#dc2626; }
.wl { display:inline-block; padding:4px 10px; margin:3px; border-radius:10px;
  font-size:18px; font-weight:600; }
.wl.good { background:#dcfce7; color:#14532d; }
.wl.weak { background:#fef9c3; color:#713f12; }
.wl.miss { background:#fee2e2; color:#7f1d1d; text-decoration:line-through; }
.bignote { background:#fff8e1; border-left:4px solid #f0b429; padding:10px 14px;
  border-radius:6px; font-size:15px; color:#6b5510; }
</style>
"""

TYPE_ZH = {"repeat": "跟读", "qa": "听话回答"}


def _secret(name):
    try:
        v = st.secrets.get(name, "")
    except Exception:
        v = ""
    return v or os.environ.get(name, "")


def _state(course_id):
    key = "S_" + course_id
    if key not in st.session_state:
        st.session_state[key] = {"idx": -1, "q": {}, "t0": None, "result": None,
                                 "submitted": False, "attempt": 1}
    return st.session_state[key]


def _qstate(s, qid):
    return s["q"].setdefault(qid, {"takes": [], "recordings": [], "done": False})


def _reset_for_retry(s):
    s["attempt"] += 1
    s["idx"] = -1
    s["q"] = {}
    s["t0"] = None
    s["result"] = None
    s["submitted"] = False


@st.cache_resource(show_spinner=False)
def _load_course(course_id):
    return models.load_course(course_id)


def get_last_result(student_id, course_id):
    rs = progress.list_results(course_id=course_id, student_id=student_id)
    return rs[-1] if rs else None


# ---------------- 儿童端 ----------------

def speaking_home(student_id):
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("## 🗣️ 口语练习")
    today = progress.beijing_today()
    done = {r["course_id"] for r in progress.list_results(student_id=student_id)}
    metas = models.all_courses()
    shown = []
    for cid in sorted(metas):
        m = metas[cid]
        if m["status"] in ("hidden", "archived"):
            continue
        if m.get("open_date") and m["open_date"] > today:
            continue
        shown.append((cid, m))
    if not shown:
        st.info("今天还没有口语任务，请告诉爸爸妈妈。")
        return
    for cid, m in shown:
        c1, c2, c3 = st.columns([4, 2, 2])
        c1.markdown("**%s**" % m["title"])
        c1.caption("%s · 第%s周第%s天" % (cid, m["week"], m["day"]))
        c2.markdown("✅ 已完成" if cid in done else "⬜ 未完成")
        if m["status"] == "closed":
            c3.button("🔒 未开放", key="sgo_" + cid, disabled=True,
                      use_container_width=True)
        else:
            label = "再做一遍" if cid in done else "开始"
            if c3.button(label, key="sgo_" + cid, use_container_width=True,
                         type="secondary" if cid in done else "primary"):
                st.query_params["course_id"] = cid
                st.rerun()


def render_course(student_id, course_id):
    st.markdown(_CSS, unsafe_allow_html=True)
    if st.button("← 返回课程列表", key="sback_" + course_id):
        if "course_id" in st.query_params:
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

    s = _state(course_id)
    if s["result"]:
        _result_page(course, s)
        return s["result"] if s["submitted"] else None

    qs = course["questions"]
    if s["idx"] < 0:
        _start_page(course, s)
    elif s["idx"] >= len(qs):
        _finish(course, s, student_id)
        st.rerun()
    else:
        n_done = sum(1 for q in qs if _qstate(s, q["id"])["done"])
        st.progress(n_done / len(qs), text="已完成 %d / %d 题" % (n_done, len(qs)))
        _question_page(course, s, qs[s["idx"]], student_id)
    return None


def _start_page(course, s):
    st.markdown("## 🗣️ %s" % course["title"])
    st.caption("Week%s · 第%s天 · 共 %d 题 · 大约 %s 分钟"
               % (course["week"], course["day"],
                  len(course["questions"]), course.get("est_minutes", 8)))
    st.markdown('<div class="bignote">小朋友：先听老师读，再点<b>红圈话筒</b>。'
                '数完 3-2-1 就大声读！读完再点一下话筒停止，听听自己的声音，'
                '满意就交给老师打星星。每题最多能录 3 次哦。</div>',
                unsafe_allow_html=True)
    st.markdown("**第一步：试试话筒**（点话筒说一句话，听到自己的声音就可以开始）")
    v = recorder.record("test", key="rec_test_%s_a%d" % (course["course_id"], s["attempt"]),
                        max_sec=8, countdown=3, label="点话筒试一试，说：Hello!")
    ready = v is not None and v.get("qid") == "test"
    if ready:
        st.success("话筒没问题！🎉")
    if st.button("开始练习", type="primary", disabled=not ready,
                 use_container_width=True):
        s["idx"] = 0
        s["t0"] = time.time()
        st.rerun()
    if not ready:
        st.caption("先试音：录一小段，点'✅就用这个'后这里就会亮起来")


def _question_page(course, s, q, student_id):
    qid = q["id"]
    qs_ = _qstate(s, qid)
    all_takes = qs_["takes"]                      # 含评分失败(error)的
    scored = [t for t in all_takes if not t.get("error")]
    takes_used = len(scored)                      # 只有评上分的才消耗 3 次机会
    st.markdown("#### 第 %d 题 · %s" % (qid, TYPE_ZH[q["type"]]))

    if q["type"] == "repeat":
        st.markdown('<div class="bigsent">%s</div>' % q["text"], unsafe_allow_html=True)
        au_label = "听老师读，还能听"
    else:
        st.markdown('<div class="hintbox">%s</div>' % q["hint"], unsafe_allow_html=True)
        st.caption("听问题，看上面的提示，用英语回答")
        au_label = "听问题，还能听"
    v = limited_audio(q["audio"], "sq%d" % qid, models.DEMO_PLAYS,
                      s.setdefault("plays", {}).get("sq%d" % qid, 0),
                      key="sau_%s_%d_a%d" % (course["course_id"], qid, s["attempt"]),
                      label=au_label)
    merge_plays(s["plays"], "sq%d" % qid, v)

    last = qs_["takes"][-1] if qs_["takes"] else None
    if last is not None:
        _show_take_feedback(last)

    can_record = takes_used < models.MAX_TAKES and not qs_["done"]
    if can_record:
        seq = len(all_takes) + 1                  # 含 error 次，保证组件 key 唯一不重放
        rv = recorder.record(qid, take=seq,
                             key="rec_%s_%d_t%d_a%d" % (course["course_id"], qid,
                                                        seq, s["attempt"]),
                             max_sec=20, countdown=3)
        if rv is not None and str(rv.get("qid")) == str(qid) and rv.get("take") == seq:
            _consume_take(course, q, qs_, rv)
            st.rerun()
    elif not qs_["done"]:
        st.info("已经录了 3 次啦，老师取最好的一次。点下一题继续！")

    if scored:
        best = engine.best_take(scored)
        n_stars = engine.stars(best.get("total"), best.get("is_rejected"))
        can_redo = takes_used < models.MAX_TAKES
        label = "下一题 ➡" if s["idx"] + 1 < len(course["questions"]) else "完成，看星星 🌟"
        cols = st.columns(2) if can_redo else [st]
        if can_redo:
            cols[0].caption("想再录一次就点上面的话筒（还剩 %d 次机会）"
                            % (models.MAX_TAKES - takes_used))
        if cols[-1].button(label, type="primary", use_container_width=True,
                           key="snext_%d_a%d" % (qid, s["attempt"]),
                           disabled=n_stars == 0 and can_redo):
            qs_["done"] = True
            s["idx"] += 1
            st.rerun()
        if n_stars == 0 and can_redo:
            st.caption("这次没录上，再试一次吧！")


def _consume_take(course, q, qs_, rv):
    """一次录音：评分（同步）+ 上传私有库（尽力而为）。"""
    wav, pcm = recorder.wav_bytes(rv)
    try:
        with st.spinner("老师在听你的录音…"):
            res = ise.evaluate_retry(_secret("XF_APPID"), _secret("XF_API_KEY"),
                                     _secret("XF_API_SECRET"),
                                     models.eval_text(q), pcm)
    except ise.IseError as e:
        res = {"total": None, "accuracy": None, "fluency": None, "integrity": None,
               "standard": None, "is_rejected": False, "words": [],
               "raw_xml": "", "seconds": 0, "error": str(e)}
    res["dur"] = rv.get("dur")
    qs_["takes"].append(res)
    try:
        path, _secs = recorder.upload_recording(
            wav, course["course_id"], q["id"], rv.get("take", 1), _secret)
        qs_["recordings"].append(path)
    except Exception:
        pass  # 上传失败不阻塞孩子做题；家长端录音箱会缺这条


def _show_take_feedback(res):
    if res.get("error"):
        st.warning("⚠️ 这次老师没听到（网络打瞌睡了），再录一次试试！")
        return
    n = engine.stars(res.get("total"), res.get("is_rejected"))
    st.markdown('<div class="starbig">%s</div>'
                % ("⭐" * n if n else "😴"), unsafe_allow_html=True)
    msg, _weak = engine.feedback(res)
    lights = engine.word_lights(res)
    if lights:
        html = "".join('<span class="wl %s">%s</span>' % (c, w) for w, c in lights)
        st.markdown('<div style="text-align:center">%s</div>' % html,
                    unsafe_allow_html=True)
    good = n >= 3
    st.markdown('<div class="fb%s">%s</div>' % ("" if good else " bad", msg),
                unsafe_allow_html=True)


def _finish(course, s, student_id):
    if s["result"]:
        return
    result = engine.build_result(course, s["q"], student_id, s["t0"])
    result["attempt"] = s["attempt"]
    if s["attempt"] > 1:
        result["result_text"] += "\n（本课第 %d 次完成·重做仅作参考）" % s["attempt"]
    s["result"] = result


def _result_page(course, s):
    result = s["result"]
    st.markdown("## 🎉 口语练习做完啦！")
    if s["attempt"] > 1:
        st.caption("本课第 %d 次完成" % s["attempt"])
    st.markdown('<div class="starbig">%s</div>'
                % ("⭐" * result["stars_total"] if result["stars_total"] <= 12
                   else "⭐ × %d" % result["stars_total"]), unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:20px'>一共得到 "
                "<b>%d</b> / %d 颗星</p>" % (result["stars_total"], result["stars_max"]),
                unsafe_allow_html=True)
    rows = []
    for qr in result["question_results"]:
        rows.append({"题": "Q%d" % qr["id"], "内容": qr["text"],
                     "星星": "⭐" * qr["stars"] if qr["stars"] else "—"})
    st.table(rows)

    if not s["submitted"]:
        if st.button("📨 提交成绩给爸爸妈妈", type="primary", use_container_width=True,
                     key="ssubmit_a%d" % s["attempt"]):
            progress.save_result(result)
            s["submitted"] = True
            st.rerun()
        st.caption("点提交后，爸爸妈妈在家长端就能看到。不提交就没有记录哦。")
    else:
        st.success("成绩已提交 ✓")
        if st.button("再做一次（重新开始本课）", use_container_width=True,
                     key="sretry_a%d" % s["attempt"]):
            _reset_for_retry(s)
            st.rerun()

    st.markdown('<div class="bignote">点下面成绩框右上角的复制图标，'
                '打开微信发给<b>文件传输助手</b>（给 AI 老师登记用）。</div>',
                unsafe_allow_html=True)
    st.code(result["result_text"], language=None)


# ---------------- 家长端 ----------------

def parent_view():
    st.markdown("## 👨‍👩‍👦 家长端 · 口语")
    expected = _secret("PARENT_PASSWORD") or "xlk2026"
    pwd = st.text_input("家长密码", type="password", key="sp_pwd")
    if pwd != expected:
        if pwd:
            st.error("密码不对")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(["成绩记录", "课程管理", "课文与答案", "录音箱"])

    with tab1:
        rs = [r for r in progress.list_results() if r.get("module") == "speaking"]
        if not rs:
            st.info("还没有口语成绩记录。")
        for r in reversed(rs):
            tag_n = "（第%d次）" % r["attempt"] if r.get("attempt", 1) > 1 else ""
            with st.expander("%s · %s · %d星/%d · 平均%d分%s"
                             % (r.get("completed_at", "?"), r["course_id"],
                                r.get("stars_total", 0), r.get("stars_max", 0),
                                r.get("score", 0), tag_n)):
                rows = []
                for qr in r.get("question_results", []):
                    rows.append({"题": "Q%d" % qr["id"], "类型": TYPE_ZH.get(qr["type"]),
                                 "内容": qr["text"], "星": qr["stars"],
                                 "最高分": qr["best_total"], "录次": qr["takes"],
                                 "弱词": ",".join(qr["weak_words"]),
                                 "考点": qr.get("tag", "")})
                st.table(rows)
                st.code(r.get("result_text", ""), language=None)

    with tab2:
        st.caption("打开=可见可做｜关闭=显示但锁定｜隐藏=不显示｜删除=永久下架")
        zh = {"open": "打开", "closed": "关闭", "hidden": "隐藏", "archived": "删除"}
        order = list(progress.COURSE_STATUSES)
        opts = [zh[k] for k in order]
        metas = models.all_courses()
        if not metas:
            st.info("还没有口语课程")
        for cid, meta in metas.items():
            c1, c2 = st.columns([3, 2])
            extra = ("　·　%s 开放" % meta["open_date"]) if meta.get("open_date") else ""
            c1.write("**%s** %s%s" % (cid, meta["title"], extra))
            picked = c2.selectbox("状态", opts, index=order.index(meta["status"]),
                                  key="sst_" + cid, label_visibility="collapsed")
            new = order[opts.index(picked)]
            if new != meta["status"]:
                progress.set_course_status(cid, new)
                st.rerun()

    with tab3:
        ids = list(models.all_courses())
        if not ids:
            st.info("没有课程")
        else:
            cid = st.selectbox("选择课程", ids, key="sp_ans_cid")
            try:
                course = models.load_course(cid, check_audio=False)
                for q in course["questions"]:
                    if q["type"] == "repeat":
                        body = "跟读：**%s**" % q["text"]
                    else:
                        body = ("问答：问题 **%s**｜屏显提示 %s｜目标答案 **%s**"
                                % (q["question"], q["hint"], q["expected"]))
                    st.markdown("- **Q%d** %s　｜考点：%s%s"
                                % (q["id"], body, q.get("tag", ""),
                                   ("　｜" + q["parent_note"]) if q.get("parent_note") else ""))
            except models.CourseValidationError as e:
                st.error(str(e))

    with tab4:
        st.caption("孩子每次确认的录音都会存到私有库（评分失败的也在），可在线试听。")
        ids = list(models.all_courses())
        if not ids:
            st.info("没有课程")
        else:
            cid = st.selectbox("选择课程", ids, key="sp_rec_cid")
            files = recorder.list_recordings(cid, _secret)
            if not files:
                st.info("该课暂无录音（或未配置私有库）")
            for f in files:
                c1, c2 = st.columns([3, 1])
                c1.write("%s（%.0f KB）" % (f["name"], f["size"] / 1024))
                if c2.button("▶ 试听", key="play_" + f["path"]):
                    try:
                        st.audio(recorder.fetch_recording(f["path"], _secret),
                                 format="audio/wav")
                    except Exception as e:
                        st.error("取回失败：%r" % e)
