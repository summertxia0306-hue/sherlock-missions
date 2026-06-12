# 口语模块对接契约与功能清单

> 版本 v1 · 2026-06-12 · Owner = 口语开发（Claude）。
> 镜像 `listening/CONTRACT.md` 的体例；改接口先改本文件再改代码。

## 0. 范围

口语模块只做：口语课程渲染、录音、讯飞 ISE 评分、星级反馈、录音入私有库、家长查看。
不做：总首页布局之外的系统功能、听力内部、账号体系。
**app.py 三入口首页**（2026-06-12 家长裁决归口语开发改造）：🎧听力 / 🗣️口语 / 🤖AI互动（占位）。

## 1. 目录

```text
speaking/
  page.py        speaking_home() / render_course() / parent_view() / get_last_result()
  engine.py      星级/规则化评语/最佳成绩/结果组装（纯逻辑，可单测）
  models.py      课程 JSON 加载+校验（加载即校验）；MAX_TAKES=3 DEMO_PLAYS=2
  ise.py         讯飞 ISE WebSocket 客户端（evaluate / evaluate_retry / parse_result）
  wavtools.py    wav→16k 单声道 PCM（纯标准库；smoke 页用，正式录音组件 JS 端已产 16k wav）
  recorder.py    自研录音组件封装 + 录音上传/列出/取回私有库
  smoke.py       冒烟/运维自检页（?mode=smoke，家长密码）
  frontend/index.html  录音组件前端（大按钮/3-2-1倒计时/自动停止20s/回放/组件内重录/JS端wav编码）
content/speaking/S01D01..05.json   课程数据（新课=新JSON+跑音频工具，零代码改动）
static/audio/speaking/             示范音（Ana，tools/make_audio_speaking.py 生成）
tools/make_audio_speaking.py       示范音生成（镜像 make_audio_v2：哈希复用/增量/代理）
```

## 2. 课程 JSON 模式

course_id 形如 `S01D01`；`questions` 题号 1..n 连续；题型：
- `repeat`：必填 `text`（跟读句，孩子可见）
- `qa`：必填 `question`（仅家长/音频）、`expected`（目标答案=评测文本）、`hint`（屏显**中文答案提示**，
  即中译英式："用英语说：它是黄色的。"。2026-06-12 家长定：**禁用 emoji/图片做答案线索**——
  各设备渲染不一致会误导内容，沿用纸质卷"配图改中译英"的既有决策；评测是跟读式比对，
  答案必须被提示唯一锁定）
- 每题必填 `audio`（static/audio/speaking/ 下）、`tag`（考点，仅家长端）；可选 `parent_note`
- 课程可选 `open_date`（与听力同语义）；course_type: training / weekly_review

## 3. 行为契约

- 每题流程：听示范（限 2 遍，复用 listening 限次组件）→ 录音（3-2-1 倒计时）→
  讯飞评分（失败自动重试 1 次，仍失败不消耗录次）→ 星级+逐词红绿灯+具体到词中文提示 →
  可重录（最多 3 次取最高）→ 下一题。**重录机制即订正，无独立订正流。**
- 信息隔离：孩子端只见星级/红绿灯/中文提示，**永不见数字分数**；分数/弱词/考点仅家长端。
- 星级阈值（W1 从宽，待真实分布校准）：≥75⭐⭐⭐ ≥50⭐⭐ 其余⭐ 拒识0星。
- 提交模型与听力一致：交卷只出成绩单，点"提交"才入库（attempt 递增可重做）。
- 录音：每次"就用这个"的 wav 传 sherlock-results 私有库 `recordings/{course_id}/`，
  失败不阻塞做题；家长端"录音箱"页签在线试听。

## 4. 结果结构（progress.save_result 入参）

```json
{
  "student_id": "sherlock", "course_id": "S01D02", "module": "speaking",
  "status": "completed", "score": 78, "stars_total": 23, "stars_max": 24,
  "question_results": [{"id":1,"type":"repeat","text":"…","stars":3,
     "best_total":80.1,"accuracy":..,"fluency":..,"integrity":..,
     "is_rejected":false,"takes":2,"weak_words":["tastes"],
     "recordings":["recordings/S01D02/0617_..wav"],"tag":"…"}],
  "duration_seconds": 300, "completed_at": "2026-06-17 15:02",
  "section_scores": {}, "wrong_answers": [], "play_counts": {},
  "result_text": "【夏洛恪·口语 S01D02】…"
}
```

`section_scores/wrong_answers/play_counts` 为 listening 家长端成绩列表的兼容空键，勿删。

## 5. 路由（app.py，2026-06-12 起）

`/` 三入口首页｜`?module=listening|speaking` 列表｜`?course_id=…` 前缀路由（W→听力 S→口语，
直链不受 open_date 限制）｜`?mode=parent` 家长端（模块单选→各自密码页）｜`?mode=smoke` 自检页。

## 6. 依赖与 Secrets

requirements：`streamlit>=1.40`（audio_input 已不用，但保留新版本）、`websocket-client>=1.6`。
Secrets：XF_APPID / XF_API_KEY / XF_API_SECRET（讯飞）+ RESULTS_REPO / RESULTS_TOKEN（录音与成绩）。
讯飞免费包 1 万次/90 天（约 2026-09-10 到期）；每次评分（含孩子每一录次）消耗 1 次。

## 7. 已知风险与降级路

- iPad Safari 未实测（家长 2026-06-12 决定不等）：录音组件用 ScriptProcessor（兼容旧 Safari），
  若 iPad 实测失败 → 排查 AudioContext 采样率/权限，备选 MediaRecorder+服务端转码。
- 评分耗时：发帧间隔已降至 10ms（冒烟 6.5–8.9s → 预期 <5s）；若讯飞报限流/10163 → 回调 0.04。
- 童声评分偏差：W1 阈值从宽；持续偏低 → 调阈值或降级为"完整度+弱词提示、不打星"。
