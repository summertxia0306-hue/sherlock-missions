# 听力模块对接契约与功能清单（给统一架构 / Codex）

> 版本 v3.5 · 2026-07-02。新增 W01D06–W01D10（4A M1U1/M1U2 同步段 + 旧坑复现），当前推荐 W01D06；字段或接口改动需同步本文件。
> v2 变更：补全目录结构与功能清单；明确"跟读/口语不在听力模块范围"。
> **v3 变更（两位 Codex 必读）**：
> ① 新增儿童端听力主界面 `listening_home()`——**架构师**的统一首页"听力练习"
>   入口请调用它，不要自行实现课程列表或完成状态（完成=有提交记录，自动推导）；
> ② 提交模型——记录只在孩子点"提交"后产生，可重做多次提交多条（attempt 字段）；
> ③ **错题订正环节已实现**（v3.1 按家长实测修订）——非诊断课成绩单页有
>   "✏️ 错题订正"按钮。订正流：第一遍**盲订正**（只重听2遍+重做，不显示原文
>   和任何答案信息）→ 再错才显示【仅原文】并重听重做第二遍 → 无论对错结束该题；
>   **正确答案任何阶段都不展示**；无提交按钮；结果（✓/✓²/✗）写入
>   result["corrections"] 与 result_text 备注；
> ④ course_type 取值：diagnostic（无订正）/ training / weekly_test（后两者有订正）；
> ⑤ 信息隔离红线增加唯一例外：订正环节展示错题原文（交卷后、仅错题）；
> ⑥ 课程总数已 10 节（W01D01–05 为 3B 听说基线与旧坑复习周；W01D06–10 转入 4A M1U1/M1U2 同步段，当前推荐 W01D06）；
> ⑦ **发布员**注意：W01D06–D10 发布含新增听力成品音频 90 个 MP3，发布七步的"音频抽查"必须执行。

## 0. 范围声明（先读）

听力模块**只做**：听力课程的渲染、答题、限次播放、计分、结果产出、家长查看。
听力模块**不做**（统一架构 / Codex 负责）：总首页、任务地图、账号体系、星星规则、
**口语与跟读训练**（2026-06-11 家长决定：原听力规划中的"热身跟读"已整体移除，
口语模块全权接管发音/跟读/录音类功能）、口语录音箱（storage/recordings.py 仅接口占位）。

## 1. 仓库目录结构（职责注释版）

```text
sherlock-missions/
  app.py                      临时入口路由（统一首页接管后整体替换，无业务逻辑）
  requirements.txt            线上运行依赖（仅 streamlit）
  .streamlit/config.toml      enableStaticServing=true（音频静态服务，勿删）
  本地体验.bat                 家长本地预览（streamlit run app.py）

  listening/                  ★ 听力模块本体（Codex 以包形式调用，勿改内部）
    page.py                   Streamlit 渲染层：render_course() / parent_view() / get_last_result()
    engine.py                 流程状态机（纯逻辑，无 streamlit 依赖，可单测）
    models.py                 课程 JSON 加载 + 校验器（加载即校验，坏数据拒载并列明细）
    results.py                计分/错题/结果契约组装 + result_text 生成（纯逻辑）
    audio.py                  受限播放组件 Python 封装（服务端持有播放计数）
    frontend/index.html       组件前端（免构建，手写 Streamlit postMessage 协议）
    CONTRACT.md               本文件

  content/listening/          课程数据（每课一个 JSON；新课=加文件，零代码改动）
    W01D01.json ... W01D10.json

  static/audio/listening/     音频资产（GitHub 固定资产，网页端不可删）
    W01D01/ ... W01D10/ q01..q16.mp3 p01.mp3 hello.mp3   每题一个成品 MP3（多角色已拼接）
    fragments/                分角色原始片段（sha1(role|text|rate) 命名，跨课复用）
    manifest.json             片段与成品的对应清单（归档课程的音频可据此人工清理）

  storage/
    progress.py               进度/结果/课程状态接口（v1 = _runtime/ JSON 文件，易失）
    recordings.py             口语录音箱接口占位（NotImplemented，Codex 实现）

  tools/                      开发期工具（不部署逻辑，线上不运行）
    make_audio_v2.py          课程 JSON → edge-tts 片段 → ffmpeg 拼接成品 + manifest
                              支持代理（tools/proxy.txt 或环境变量）；增量生成、同文本复用
    生成音频_v2.bat            上面脚本的双击入口
    proxy.txt                 家长本机代理配置（已 gitignore，不入库）

  _runtime/                   运行期数据（已 gitignore；平台重启清空）
```

## 2. 功能清单

### 已实现（W01D01 等价迁移，2026-06-11）

| # | 功能 | 位置 |
|---|---|---|
| 1 | 五种题型：听音选词 / 听句判断 / 听问句选答语 / 听对话选答案（双音色）/ 听短文判断 | engine + page |
| 2 | 限次播放，服务端计数，任意 rerun/选答案不重置，普通操作不可绕过 | audio.py + frontend |
| 3 | 短文 4 小题共享播放次数 | page._passage_page |
| 4 | 试音解锁（首屏必须先试音才能开始；试音不限次） | page._start_page |
| 5 | 分部分 intro 页 + 全程进度条；交卷前不显示对错 | page |
| 6 | 自动计分、五维分项、错题列表（含考点标签）、听满次数记录、用时 | results.py |
| 7 | result_text 人读成绩单（"复制成绩→微信→AI入档"兜底通道，格式与旧HTML版一致） | results.py |
| 8 | 儿童端信息隔离：看不到原文/答案/考点标签/管理操作 | page |
| 9 | 家长端（?mode=parent + 密码）：成绩记录 / 课程管理 / 原文与答案 三页签 | page.parent_view |
| 10 | 课程状态 open/closed/hidden/archived（家长端可设；不可删 GitHub 固定资产） | storage/progress |
| 11 | `open_date` 到期自动解锁（北京时间），支持一周 5 课批量预发 | progress.visible_courses |
| 12 | 课程 JSON 校验器（ID/题号唯一、答案合法、音频存在、计分一致、open_date 格式） | models.py |
| 13 | 音频生产线：JSON→片段(哈希复用)→拼接成品(0.6s停顿)→manifest；代理支持；增量生成 | tools/make_audio_v2 |
| 14 | 引擎层单元测试通过（满分/混合错题/校验器负样例） | 开发期验证 |

### 已实现（v3 追加，2026-06-12）

| # | 功能 | 位置 |
|---|---|---|
| 15 | 听力主界面 listening_home（课程卡片/正式完成标记/再做一遍/锁定态；test 不产生完成） | page.listening_home |
| 16 | 提交模型（提交才有记录、可重做多次提交、attempt 标记） | page._result_page |
| 17 | **错题订正环节 v2**：第一遍盲订正（重听2遍+重做，零提示）→再错才显示仅原文+第二遍重做→结束；答案全程不展示；无提交按钮；结果（✓/✓²/✗）入 corrections+result_text 备注，不计判定 | page._correction_page |
| 18 | 课程 W01D01–10（D01–05：3B 听说基线与旧坑复习周；D06–10：4A M1U1/M1U2 同步段，D10 为综合周测） | content/listening |
| 19 | GitHub 私有结果库持久化（成绩+课程状态，未配置自动退本地） | storage/progress |
| 20 | `data_kind=test/formal` 隔离：旧无字段记录按 test，新提交默认 formal，家长端醒目标注 | storage/progress + page |
| 21 | 安全家长测试入口：同一会话先过家长密码才能打开 test 课程；普通儿童入口固定 formal；test/formal 页面状态隔离 | app.py + page + storage/progress |
| 22 | 课程按编号排序并标明当前推荐课；W1 听说课程继续全部可见，不在 2B 调整状态或开放日期 | page |
| 23 | 当前推荐课为 W01D06；D06 人物介绍与数字，D07 Jill 阅读，D08 What can you do，D09 Can he/she/动物能力，D10 M1U1+M1U2 综合周测 | page + content/listening |

### 计划中（听力模块侧）

| # | 功能 | 说明 |
|---|---|---|
| P2 | 每日完成星标（课内简单展示） | 最终以统一系统的星星规则为准，届时让位 |
| P3 | 周中补丁机制工具化 | 重出未解锁课程的便捷流程（当前手工可行） |

### 明确不做（划给统一架构）

跟读/口语/录音（口语模块）；结果持久化存储；总首页与任务地图；账号体系；
资产删除后台。

## 3. 调用接口（python）

```python
from listening import page

# 听力主界面（2026-06-12 新增）：统一首页的"听力练习"入口应调用它。
# 列出全部已开发课程卡片：完成状态（✅/⬜）由孩子的提交记录自动推导（非家长设置）；
# 已完成可"再做一遍"；hidden/archived 或未到 open_date 的不显示；closed 显示但锁定。
page.listening_home(student_id: str)

# 渲染一节课（在 Streamlit 页面上下文中调用）。
# 提交模型（2026-06-12 家长定）：交卷只显示成绩单；孩子点"提交"按钮后
# 才写入 storage.progress 并返回结果 dict（未提交一律返回 None，无任何记录）。
# 提交后可"再做一次"并再次提交，每次一条独立记录（result["attempt"] 递增）。
result = page.render_course(student_id: str, course_id: str, data_kind: str = "formal")

# 查询某生某课最近一次结果（无则 None）
result = page.get_last_result(student_id, course_id)
```

```python
from storage import progress

progress.visible_courses()            # {course_id: meta} 仅 open 且已到 open_date
progress.all_courses()                # 同上，含全部状态与 open_date
progress.get_course_status(cid)       # open / closed / hidden / archived（默认 open）
# 状态语义（家长端 UI 标签）：open=打开（可见可做）/ closed=关闭（列表显示但锁定）/
# hidden=隐藏（列表不显示）/ archived=删除（永久下架；网页端不真删 GitHub 文件）
progress.set_course_status(cid, st)
progress.list_results(course_id=None, student_id=None, data_kind=None)
progress.completed_course_ids(results) # 只返回 formal 完成课程
progress.submission_data_kind(requested=None, parent_authenticated=False)
progress.course_session_key(prefix, course_id, data_kind)
progress.beijing_today()              # "YYYY-MM-DD"（UTC+8）
```

注意：progress v1.1（2026-06-12）起支持双层存储：运行目录（快路径/兜底）+
GitHub 私有结果库（Secrets 配 RESULTS_REPO / RESULTS_TOKEN 后启用，重启不丢）。
v1.2（2026-06-25）起：
- 新提交若未显式指定，`save_result` 自动写入 `"data_kind":"formal"`；
- 历史无字段结果在读取时补为 `"data_kind":"test"`，不覆盖原始 JSON；
- 儿童端完成状态和 `get_last_result` 只认 formal；
- 家长端可同时看 test/formal，并显示“开发/家长测试”或“正式学习”。
- 普通课程列表和普通 `?course_id=...` 直链固定使用 formal；query 参数不能改写身份；
- test 只能由已通过密码的家长端按钮在同一 Streamlit 会话中启动；直接拼接 test URL 会被拒绝；
- test/formal 使用不同 session_state key，避免同一课程跨入口串写。

## 4. 结果结构（progress.save_result 入参 / render_course 返回）

```json
{
  "student_id": "sherlock",
  "course_id": "W01D01",
  "data_kind": "formal",
  "status": "completed",
  "score": 85,
  "duration_seconds": 1120,
  "section_scores": {
    "word_discrimination": 15,
    "sentence_meaning": 20,
    "question_response": 15,
    "dialogue": 15,
    "passage": 20
  },
  "wrong_answers": [
    {"id": 2, "picked": "A", "correct": "B",
     "tag": "听辨·音近词(E26词复现)", "section": "word_discrimination"}
  ],
  "play_counts": {"2": 2, "passage": 3},
  "completed_at": "2026-06-16 15:02",
  "result_text": "【夏洛恪·听力诊断卷 W01D01】…（人读成绩单，复制回传通道用）"
}
```

- section_scores 键 = 课程 JSON 中 section 的 id（五个固定值如上）。
- data_kind 仅允许 `test` / `formal`。历史无字段记录按 test。
- play_counts 键：普通题 = 题号字符串；短文 = section id。
- wrong_answers.tag 是教学诊断标签，**只可在家长端展示**。
- 训练课（P1 交付后）会追加 `"corrections"` 字段记录订正结果，结构届时同步本文件。

## 5. URL 参数（当前临时入口；统一首页可沿用或替换）

- `?course_id=W01D01` 打开指定课程（儿童正式入口），提交默认 `data_kind=formal`
- `?mode=parent` 家长端（密码 = st.secrets["PARENT_PASSWORD"]，未设则临时 xlk2026）
- `?mode=test&course_id=W01D01` 仅由已认证家长端按钮生成；同一会话未认证时拒绝访问，
  成绩和录音写 `data_kind=test`，不产生儿童端完成状态
- `?student_id=sherlock`（默认 sherlock）

## 6. 课程数据与音频约定

- 课程 JSON：`content/listening/{course_id}.json`；新增课程 = 新 JSON + 跑
  `tools/make_audio_v2.py` + git push，无代码改动。
- 可选字段 `open_date`（"YYYY-MM-DD"）：未到期（北京时间）对儿童端不可见，
  与 status 叠加生效（visible = open 且到期）。
- 音频：每题一个成品 MP3（多角色对话已在构建期拼接，运行时单文件播放——
  这是 iPad Safari 自动播放限制下的稳妥设计，勿改回运行时多段连播）。
- 音频 URL（2026-06-29 生产修正）：`audio.py` 生成多个公开直链，前端失败时自动切换。
  当前顺序为 jsDelivr CDN 优先、GitHub Raw 兜底；**前提 = 仓库 Public**。
  前端同时兼容历史后端只传 Raw `src` 的场景，会自动派生 jsDelivr 优先源。
  不要改回 `/app/static/` 内部路径（Community Cloud 禁止组件访问）。
- 音色固定：旁白/单词/短文 = en-US-AnaNeural（童声），对话女 = AriaNeural，
  男 = GuyNeural；语速 -10%。改音色/语速会使 fragments 哈希全部失效（重新生成）。

## 7. 儿童端信息隔离（不可破坏的红线）

儿童端任何页面不得出现：听力原文、正确答案（交卷前）、考点标签、家长操作入口。
家长端独立路由 + 密码。统一首页集成时请保持此隔离。
**唯一例外（2026-06-12，v3.1 收窄）**：错题订正的**第二遍尝试**展示该错题的原文
（仅原文；正确答案与"他选了什么"任何阶段都不展示）——仅限交卷后、仅限错题、
仅限非诊断课。第一遍订正什么都不显示（盲订正）。
