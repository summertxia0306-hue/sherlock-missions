# 口语模块对接契约与功能清单

> 版本 v4.1 · 2026-08-27：P5 iOS 真机缺陷修复。PWA 保留单一 `AudioContext`，但每次录音重新获取麦克风流并在成功、静音或异常后立即停轨；恢复浏览器自动增益、降噪与回声消除，避免跨题哑流、麦克风指示灯常亮和 iOS 回听音量过小。课程卡增加推荐标识与完成置灰，按钮触控留白同步扩大。

> 版本 v4.0 · 2026-08-26：P5 普通 CloudBase 儿童入口由服务端 formal 会话写正式结果和私有录音；评分函数仅接受服务端 HMAC 签署的 `data_kind=formal|test`，录音路径固定隔离为 `sherlock-english/{data_kind}/{data_kind}/{course_id}/{result_id}/`。家长验收继续独立写 test，Streamlit 仅保留只读迁移提示。

> 版本 v3.1 · 2026-08-25：P3 课程版本一致性修复。静态儿童课与 API 必须共用语义版本算法；口语 JSON 不进入 Service Worker 预缓存，客户端每次进课强制实时取目录和课件。

> 版本 v3.0 · 2026-08-24：P3 CloudBase test-only 迁移。新增 React iPad 录音状态机、`sherlock-api` 可信门控、私有 `score-speaking` 讯飞适配、私有录音临时回放；P5 前 formal 入口继续关闭。

> 版本 v2.1 · 2026-08-16（保留 S01D39–S01D40，新增 S01D41–S01D50 综合复习 M1U1–M3U2；学生端改为首个 formal 未完成课周围最多 5 课，历史 01–38 公共课件资产下线但学习记录、录音与 Git 历史保留）。
> v2.0 · 2026-08-11：新增 S01D36–S01D40，与听力课严格同页对齐 4A M3U2 第37–41页；约90% M3U2 + 约10%已学旧坑，不进入 M3U3。
> v1.9 · 2026-08-06：新增 S01D31–S01D35，与听力课严格同页对齐 4A M3U1 第32–36页；不进入 M3U2。
> v1.8 · 2026-08-05：锁定 Streamlit 1.55.0 与 websocket-client 1.9.0，避免云端重建时解析到不兼容依赖；课程、口语门控和 data_kind 规则不变。
> v1.7 · 2026-07-24：新增 S01D21–S01D30，与听力课严格同页对齐 4A M2U2 第22–26页和 M2U3 第27–31页。
> 镜像 `listening/CONTRACT.md` 的体例；改接口先改本文件再改代码。

## P3 CloudBase 迁移覆盖条款（当前生效）

- 当前公开课程仍为 S01D39–S01D50，每课 6 repeat + 2 QA；儿童副本不含 `expected`、题目原文、考点或家长备注。
- P3 仅允许经家长认证的 `test`：浏览器不能写 formal，test 不点亮儿童正式完成、不生成正式学情结论。
- 浏览器只调用 `sherlock-api`；后者校验会话、课程版本、题号和录次，再以内部 HMAC 调用 `score-speaking`。讯飞密钥只存在于评分云函数环境变量。
- 静态儿童课 `course_version` 与 API 课程版本必须统一由解析后课程对象的 `stableVersion(course)` 生成；发布测试必须逐课验证 12/12 一致。口语目录和课件请求使用 `cache: no-store` 加新鲜查询参数，且不得进入 Service Worker 预缓存，避免旧 JSON 与新 API 混用。
- 函数间 HMAC 必须签署递归字段排序后的规范化 JSON，不得直接签署依赖对象插入顺序的 `JSON.stringify(payload)`；CloudBase 传输重排字段后仍须验签通过。
- 录音为单声道 16 kHz、16 bit PCM/WAV；静音、过短和格式不符在调用讯飞前拒绝，不消耗有效录次。
- 评分成功才生成不可篡改的加密 proof。最终提交只携带 proof；服务端重建分数、首读/末读/最高分、`take_stars`、`weak_words` 和 `passed_by_safety`。
- 同一 result/question/attempt 重复请求使用服务端幂等缓存；评分服务或网络失败不产生 proof、不占三次有效评分。
- 首次评分的幂等缓存读取必须使用 `take_id` 条件查询并把空结果视为未评分，不得对尚不存在的文档执行会抛错的直读；线上验收必须从公开 SDK 经 `sherlock-api` 走完整评分链路，不能再用直接调用私有评分函数代替。
- 录音只由评分函数服务端上传到 `sherlock-english/test/test/{course_id}/{result_id}/qNN-takeN.wav`；家长认证后按题次取得 10 分钟临时 URL，儿童端只回放当前浏览器内的录音 Blob。
- 讯飞配额策略：不购买、不自动付费；当前授权到期前使用现有免费额度，到期后先验证每日免费额度是否继续；供应商不可用时保留录音和重试能力，不伪造分数。
- CloudBase 英文 ISE 适配器与已验证的 Streamlit 契约保持一致：参考文本为 BOM 加原文、`group=pupil`、10 ms 音频帧节奏，最后一个实际音频帧携带 `aus=4/status=2`；调用超时上限 20 秒并允许一次瞬时失败重试。外层 `sherlock-api` 与私有评分函数均配置 60 秒函数超时。
- 本节与下文旧 Streamlit formal 描述冲突时，以本节为准；旧规则保留作 P5 正式迁移依据，不在 P3 提前启用。

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
content/speaking/S01D39..50.json   当前公共课程数据（新课=新JSON+跑音频工具，零代码改动）
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
- **录音组件 iOS 约束**：AudioContext 全实例唯一、只在用户手势内创建/恢复、录完
  suspend 不 close；每次录音使用新麦克风流并在结束后立即停轨；录音静音检测
  （峰值<0.01 直接提示重录不送评分）。
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

当前公共课程为 W01D39–D50、S01D39–D50，均按编号排序。儿童端围绕首个 formal 未完成课程显示最多 5 课；全部完成时显示最后 5 课。家长端仍列出全部现存公共课件。
S01D39–D40 保持原 M3U2 课程不变。S01D41–D48 依次综合复习 M1U1 Meeting new people、M1U2 Abilities、M1U3 How do you feel、M2U1 Jill's family、M2U2 Jobs、M2U3 Friends、M3U1 In our school、M3U2 Around my home。
S01D49 为 M1–M2 综合复习，S01D50 为 M1–M3U2 全范围综合复习；均不进入 M3U3。
S01D01–D38 的公共 JSON、示范音和构建片段已下线；正式成绩、逐题星级、weak_words、passed_by_safety、录音、私有结果库数据与 Git 历史保留。
3 星正常通关、未到 3 星可重试、第 3 次仍未到 3 星出现“先过这题”的口语门控规则保持不变。

## 6. 依赖与 Secrets

requirements：`streamlit==1.55.0`、`websocket-client==1.9.0`。这两个版本已通过本地完整页面验证；不得改回无上限的 `>=`，否则云端休眠重建可能自动升级并破坏启动。
Secrets：XF_APPID / XF_API_KEY / XF_API_SECRET（讯飞）+ RESULTS_REPO / RESULTS_TOKEN（录音与成绩）。
讯飞免费包 1 万次/90 天（约 2026-09-10 到期）；每次评分（含孩子每一录次）消耗 1 次。

## 6b. PWA 录音生命周期（2026-08-27 iOS 正式入口实测后定）

整节课共用一个 React 录音服务和一个 `AudioContext`；`AudioContext` 必须在点击录音的
用户手势内创建/恢复，录完只 suspend、不 close。

**麦克风流不跨录次复用**：每次点击录音重新 `getUserMedia`，请求单声道并启用浏览器
`echoCancellation/noiseSuppression/autoGainControl`；成功、静音、异常或页面离开都立即停止
全部音轨。PWA 始终是同一页面，不会像旧 Streamlit 的多 iframe 实例那样因重新获取流而
反复创建权限主体；已授权情况下由浏览器复用权限。

原因：2026-08-26 两台 iOS 真机确认，跨题复用的流即使仍报告 live/unmuted，也可能在播放
示范音切换音频会话后只产出近零采样；同时停轨不及时会让系统橙色麦克风图标跨题常亮。
旧实现还关闭自动增益，导致 iOS 回听持续偏小。静音阈值峰值 `<0.01`、失败不消耗评分录次
继续保留。

## 7. 已知风险与降级路

- iOS PWA 仍需家长复验 v4.1：首录成功率、录完后橙色麦克风图标熄灭、回听音量和评分全流程；
  自动化只能证明音轨生命周期和 16k WAV 输出，不能代替真实 iOS 音频会话。
- 评分耗时：发帧间隔已降至 10ms（冒烟 6.5–8.9s → 预期 <5s）；若讯飞报限流/10163 → 回调 0.04。
- 童声评分偏差：W1 阈值从宽；持续偏低 → 调阈值或降级为"完整度+弱词提示、不打星"。
