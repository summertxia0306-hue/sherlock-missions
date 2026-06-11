# 听力模块对接契约与功能清单（给统一架构 / Codex）

> 版本 v2 · 2026-06-11。字段或接口改动需双方确认后同步本文件。
> v2 变更：补全目录结构与功能清单；明确"跟读/口语不在听力模块范围"。

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
    W01D01.json

  static/audio/listening/     音频资产（GitHub 固定资产，网页端不可删）
    W01D01/ q01..q16.mp3 p01.mp3 hello.mp3   每题一个成品 MP3（多角色已拼接）
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

### 计划中（听力模块侧，随 W01D02 起交付）

| # | 功能 | 说明 |
|---|---|---|
| P1 | 训练课"错题再听"订正环节 | course_type=training 的课，交卷后错题逐题：重听→原文对照→同题重做1次→再错即停；订正结果入 result_text 作备注，不计掌握判定 |
| P2 | 段间休息屏 | 训练课三段结构（热身复现/主练/小测）之间的休息提示 |
| P3 | 每日完成星标（课内简单展示） | 最终以统一系统的星星规则为准，届时让位 |

### 明确不做（划给统一架构）

跟读/口语/录音（口语模块）；结果持久化存储；总首页与任务地图；账号体系；
资产删除后台。

## 3. 调用接口（python）

```python
from listening import page

# 渲染一节课（在 Streamlit 页面上下文中调用）。
# 课程完成时：结果自动写入 storage.progress，并返回结果 dict；未完成返回 None。
result = page.render_course(student_id: str, course_id: str)

# 查询某生某课最近一次结果（无则 None）
result = page.get_last_result(student_id, course_id)
```

```python
from storage import progress

progress.visible_courses()            # {course_id: meta} 仅 open 且已到 open_date
progress.all_courses()                # 同上，含全部状态与 open_date
progress.get_course_status(cid)       # open / closed / hidden / archived（默认 open）
progress.set_course_status(cid, st)
progress.list_results(course_id=None, student_id=None)
progress.beijing_today()              # "YYYY-MM-DD"（UTC+8）
```

注意：v1 的 progress 存运行目录 `_runtime/`，平台重启清空。统一架构换持久化后端时
只需重写 storage/progress.py，**函数签名不变**。

## 4. 结果结构（progress.save_result 入参 / render_course 返回）

```json
{
  "student_id": "sherlock",
  "course_id": "W01D01",
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
- play_counts 键：普通题 = 题号字符串；短文 = section id。
- wrong_answers.tag 是教学诊断标签，**只可在家长端展示**。
- 训练课（P1 交付后）会追加 `"corrections"` 字段记录订正结果，结构届时同步本文件。

## 5. URL 参数（当前临时入口；统一首页可沿用或替换）

- `?course_id=W01D01` 打开指定课程（儿童端）
- `?mode=parent` 家长端（密码 = st.secrets["PARENT_PASSWORD"]，未设则临时 xlk2026）
- `?student_id=sherlock`（默认 sherlock）

## 6. 课程数据与音频约定

- 课程 JSON：`content/listening/{course_id}.json`；新增课程 = 新 JSON + 跑
  `tools/make_audio_v2.py` + git push，无代码改动。
- 可选字段 `open_date`（"YYYY-MM-DD"）：未到期（北京时间）对儿童端不可见，
  与 status 叠加生效（visible = open 且到期）。
- 音频：每题一个成品 MP3（多角色对话已在构建期拼接，运行时单文件播放——
  这是 iPad Safari 自动播放限制下的稳妥设计，勿改回运行时多段连播）。
- 音色固定：旁白/单词/短文 = en-US-AnaNeural（童声），对话女 = AriaNeural，
  男 = GuyNeural；语速 -10%。改音色/语速会使 fragments 哈希全部失效（重新生成）。

## 7. 儿童端信息隔离（不可破坏的红线）

儿童端任何页面不得出现：听力原文、正确答案（交卷前）、考点标签、家长操作入口。
家长端独立路由 + 密码。统一首页集成时请保持此隔离。
