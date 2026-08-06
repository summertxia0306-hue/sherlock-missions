# 口语模块对接契约与功能清单

> 版本 v1.9 · 2026-08-06（新增 S01D31–S01D35，与听力课严格同页对齐 4A M3U1 第32–36页；不进入 M3U2）。
> v1.8 · 2026-08-05：锁定 Streamlit 1.55.0 与 websocket-client 1.9.0，避免云端重建时解析到不兼容依赖；课程、口语门控和 data_kind 规则不变。
> v1.7 · 2026-07-24：新增 S01D21–S01D30，与听力课严格同页对齐 4A M2U2 第22–26页和 M2U3 第27–31页。
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
content/speaking/S01D01..35.json   课程数据（新课=新JSON+跑音频工具，零代码改动）
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
  **必须读到 3 星才出现"下一题"按钮**；不到 3 星不放行、必须重录。**重录机制即订正，无独立订正流。**
- **3 星门控 + 三次后先过（2026-06-25 家长定）**：不到 3 星时不展示"下一题"，孩子据逐词提示重读；
  **每次不到 3 星会把该题示范音可听次数重置回满**（让孩子永远有地方再听——前端计数只升不降，
  故用"换组件实例"key 带 `g{demo_gen}` 实现重置，不改共享 frontend/index.html）。
  最多计 3 次有效评分（评分失败不占次数）；第 3 次仍不到 3 星即出现"先过这题"，
  内部继续使用兼容字段 `passed_by_safety=True`，不再要求录到 6 次。
- 信息隔离：孩子端只见星级/红绿灯/中文提示，**永不见数字分数**；分数/弱词/考点仅家长端。
- 星级阈值（W1 从宽，待真实分布校准）：≥75⭐⭐⭐ ≥50⭐⭐ 其余⭐ 拒识0星。
- **评语与星级一致性硬规则**（2026-06-12 家长纠错）：不满 3 星绝不出现夸赞语；
  无明显弱词但总分低 → 点名得分最低的词（红绿灯同步标黄）或提示整句连贯度。
- **录音组件 iOS 约束**（2026-06-12 实测）：AudioContext 全实例唯一、只在用户手势内
  创建/恢复、录完 suspend 不 close；录音静音检测（峰值<0.01 直接提示重录不送评分）。
- 提交模型与听力一致：交卷只出成绩单，点"提交"才入库（attempt 递增可重做）。
- 录音：每次"就用这个"的 wav 传 sherlock-results 私有库 `recordings/{course_id}/`，
  失败不阻塞做题；家长端"录音箱"页签在线试听。上传成功后立即把入口身份写入旁路
  `recording_metadata.json`，提交结果时再由 `recording_records` 复核；历史无元数据录音按 test，
  不覆盖 wav 原文件。
- 数据隔离：新提交写 `data_kind=formal`；历史无字段成绩和录音按 test。儿童端完成状态只认 formal；
  家长端同时显示两类记录并醒目标注。
- 安全入口：普通儿童课程和普通直链固定 formal；test 只能由同一会话已通过密码的家长端启动。
  test/formal 使用不同 session_state key，录音上传和成绩提交沿用同一 data_kind。

## 4. 结果结构（progress.save_result 入参）

```json
{
  "student_id": "sherlock", "course_id": "S01D02", "module": "speaking",
  "data_kind": "formal",
  "status": "completed", "score": 78, "stars_total": 23, "stars_max": 24,
  "question_results": [{"id":1,"type":"repeat","text":"…","stars":3,
     "best_total":80.1,"first_total":62,"last_total":80,"passed_by_safety":false,
     "accuracy":..,"fluency":..,"integrity":..,"take_stars":[1,2,3],
     "is_rejected":false,"takes":3,"weak_words":["tastes"],
     "recordings":["recordings/S01D02/0617_..wav"],
     "recording_records":[{"path":"recordings/S01D02/0617_..wav","data_kind":"formal"}],
     "tag":"…"}],
  "duration_seconds": 300, "completed_at": "2026-06-17 15:02",
  "section_scores": {}, "wrong_answers": [], "play_counts": {},
  "result_text": "【夏洛恪·口语 S01D02】…"
}
```

`section_scores/wrong_answers/play_counts` 为 listening 家长端成绩列表的兼容空键，勿删。

## 5. 路由（app.py，2026-06-12 起）

`/` 三入口首页｜`?module=listening|speaking` 列表｜`?course_id=…` 儿童正式入口
（W→听力 S→口语，默认 formal）｜`?mode=parent` 家长端（模块单选→各自密码页）｜
`?mode=test&course_id=…` 已认证家长测试入口（默认拒绝直接访问）｜`?mode=smoke` 自检页。

W01D01–D35、S01D01–D35 当前均保持可见，列表按编号排序；当前推荐自动选择首个已可见且 formal 未完成课程。
S01D06 人物介绍与数字，S01D07 Jill 阅读，S01D08 What can you do，S01D09 Can he/she/动物能力，S01D10 综合介绍朋友/家人。
S01D11–D15 覆盖 M1U3 feelings / Have some ... / story / weekly review；S01D16 为已完成的 M2U1 family words，保持原课不改。
S01D17–D20 依次对齐 4A M2U1 教材第17–18页 family questions、第19页 Photos of Jill's family、第20页 Mid-autumn Day、第21页 rhyme 与 `-sh` 语音复习。
S01D21–D25 与听力同页对齐 M2U2 第22–26页：fire rhyme、jobs、job guessing、fire station、survey/`dr`/`pr`。
S01D26–D30 与听力同页对齐 M2U3 第27–31页：friend descriptions、clothes、lion and mouse、clothes rhyme、friend profile/`br`/`cr`。
S01D31–D35 与听力同页对齐 M3U1 第32–36页：school places、`There is/are`、school visit、Animal School、school/classroom/schoolbag review 与 `fr`/`gr`/`tr`；不进入 M3U2。
3 星正常通关、未到 3 星可重试、第 3 次仍未到 3 星出现“先过这题”的口语门控规则保持不变。

## 6. 依赖与 Secrets

requirements：`streamlit==1.55.0`、`websocket-client==1.9.0`。这两个版本已通过本地完整页面验证；不得改回无上限的 `>=`，否则云端休眠重建可能自动升级并破坏启动。
Secrets：XF_APPID / XF_API_KEY / XF_API_SECRET（讯飞）+ RESULTS_REPO / RESULTS_TOKEN（录音与成绩）。
讯飞免费包 1 万次/90 天（约 2026-09-10 到期）；每次评分（含孩子每一录次）消耗 1 次。

## 6b. 录音组件实例策略（2026-06-12 iOS 实测后定，勿改回）

整节课（含试音）**共用一个组件实例**：key 只含 course_id+attempt，题号/录次走
args(qid/take)，前端检测 qid|take 变化做软复位。
原因：iOS WebKit 对每个新 iframe 实例重弹麦克风权限——按题新建实例 = 每题弹一次
（家长 iOS 实测）；单实例 = 每节课只授权一次。防重放靠 Python 端 (qid, take) 匹配。

**麦克风流策略 v3（2026-06-12 iOS 四轮实测迭代，勿简化）**：
点话筒时（手势内）：流存在且 live 且未 muted → 直接复用；否则停轨释放并重新
getUserMedia。录后峰值<0.01（哑流）→ 释放流+提示重试（下一次点击自动换新流）。
演进记录：v1 复用流→播放示范音把 iOS 音频会话切"纯播放"，旧流静音变哑；
v2 每次新申请→能录但 iOS 随机重弹权限 4-5 次/课；v3 健康才复用+哑流自愈。
AudioContext 全程唯一（手势内创建/恢复、录完 suspend 不 close）。
代价说明：复用期间话筒指示灯（小绿点）整课常亮，属预期。

## 7. 已知风险与降级路

- iPad Safari 未实测（家长 2026-06-12 决定不等）：录音组件用 ScriptProcessor（兼容旧 Safari），
  若 iPad 实测失败 → 排查 AudioContext 采样率/权限，备选 MediaRecorder+服务端转码。
- 评分耗时：发帧间隔已降至 10ms（冒烟 6.5–8.9s → 预期 <5s）；若讯飞报限流/10163 → 回调 0.04。
- 童声评分偏差：W1 阈值从宽；持续偏低 → 调阈值或降级为"完整度+弱词提示、不打星"。
