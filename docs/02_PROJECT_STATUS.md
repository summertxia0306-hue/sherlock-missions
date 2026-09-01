# PROJECT STATUS

> 最后更新：2026-08-31
> 当前阶段：GitHub Pages 候选入口阶段一整体验收通过。家长已在无 VPN iPad 完成听力 test、口语 8 题评分及最终 test 提交；云端复核结果、8/8 私有录音和 formal/test 隔离均正常，口语反馈约 3 秒。阶段二正式入口切换尚未获批，原 CloudBase 入口仍是唯一儿童 formal 入口；P6 第一周 12 门课程继续保持隐藏 test，尚未批准正式开放

## 当前事实

- 新根目录已经接入原仓库完整 Git 对象库和工作树，是当前唯一活跃开发根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`。
- 旧源仓库仍在：`D:\project_antigravity\education_english\听力部分\sherlock-missions`，迁移前后均保持干净，当前只作只读参考。
- 当前仓库分支：`main`。
- P2 Git 基线：`954c02400a69ad7aed22574baa742500dfc15d1a`；P3 独立提交由本记录所在的 `main` 提交承载并推送。
- 当前远端：`https://github.com/summertxia0306-hue/sherlock-missions.git`。
- 原仓库 770 个跟踪文件均已迁入；根 README 同名冲突以治理 README 为主，旧 README 原样归档到 `docs/legacy-streamlit/README_streamlit_legacy.md`。
- 当前单一活动课程源：听力和口语各 18 个 JSON，其中旧课各 12 门继续 formal 可见，新学期各 6 门为隐藏 test；成品 MP3 480 个，fragments MP3 580 个。
- 当前唯一正式入口已切换为 CloudBase；Streamlit 真实浏览器渲染确认仅保留只读迁移提示，不再接受课程、家长测试或学习记录提交。
- CloudBase `family24` 在 P5 切换前后实时核验仍为体验版，到期 `2027-02-04 23:59:59`，超额付费关闭；当前周期 `2026-08-04` 至 `2026-09-04`，切换部署前 3000 点中已用 27.13 点、剩余 2972.87 点。
- P1 已创建隔离资源：Event 云函数 `sherlock-api`、4 个 `ADMINONLY` 的 `sherlock_*` 集合、`sherlock-english/test/README.txt` 存储标记和前端 `publish_key`；匿名登录仅对 `sherlock-api` 放行，其他函数保留原匿名禁用规则。
- `sherlock-api` 已配置家长密码 scrypt 哈希、会话 HMAC 和口语内部 HMAC；P3 私有 `score-speaking` 继续使用。P5 保留全部既有密钥并仅新增 `FORMAL_ENABLED=true`；在线健康检查返回 `stage=P5`、`formal_enabled=true` 和 `writes=formal-and-test`。正式站点为 `https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/`。
- 2026-08-31 已部署并完成 GitHub Pages 阶段一候选入口验收：`https://summertxia0306-hue.github.io/sherlock-english/`。CloudBase 体验版套餐拒绝新增 Web 安全域名，因此候选前端改用同一 CloudBase 环境的 HTTP 网关 `/sherlock-api`，由云函数只向上述 GitHub Pages Origin 返回 CORS；原 Web SDK/Event 调用路径继续保留。候选入口已通过无 VPN iPad 家长 test 全流程，但阶段二尚未获批，因此仍不是儿童 formal 正式入口。
- 2026-08-31 家长 iPad 候选入口听力 test 成功；口语评分曾因 HTTP 网关约 100 KiB 请求体上限返回 413。GitHub HTTP 传输改为 65536 字符分块、最多 2 块并发、单块重试后，第 1 题评分和 8 题整课最终提交均成功。云端复核最新口语结果 `e78b76f2-9c2e-4f01-a260-0f7a02f6f8fd` 为 `S01D39/test/completed`、97 分、24/24 星、8/8 题；8 个最终私有 WAV 均存在且非空，临时分块目录为 0；`formal_completion_eligible=false`，没有新增 formal 结果。同期听力结果 `88106ae0-afe1-42cf-b352-e9a7eb861baf` 为 `W01D39/test/completed`、95 分、20/20 题。
- P2 已上线 W01D39–W01D50 共 12 门听力课；儿童副本 12/12 无答案、原文、考点标签或家长备注；216/216 段线上 MP3 与本地发布文件 SHA-256 一致。
- P3 已完成 React 口语页面、单实例 iPad PCM/WAV 录音、试录/回放/自动停止、示范音互斥、讯飞评分适配、3 星/三次门控、加密 proof、幂等评分、私有录音和家长临时回放实现，并已部署 test。
- 2026-08-27 两台 iOS 正式体验确认 PWA 跨录次复用麦克风流会导致首录间歇性静音、录完后系统麦克风指示灯跨题常亮，且显式关闭自动增益后回听偏小；Android 与旧 Streamlit 不复现。PWA 已改为每次录音获取新流并在成功、静音、异常和离页时立即停轨，恢复浏览器自动增益/降噪/回声消除；同时恢复课程卡“推荐”、完成置灰并扩大按钮触控留白。发布后真实 iOS 复验确认首录、回听音量、麦克风指示灯释放及 UI 微调均已修复。
- P5 真实正式课程与持久化验收已完成：W01D46 与 S01D46 均为 `formal`、`completed`、`formal_completion_eligible=true`；S01D46 的 9/9 个录音文件在 24 小时后仍存在且非空；家长确认推荐进度为 W01D47/S01D47。同期 24 点仍为 `family24-web-003` / `SUCCESS` / 11/11，未受切换影响。
- P3 本地验证：Web 51/51、`sherlock-api` 31/31、`score-speaking` 11/11、旧版 Python 40/40；覆盖率门、TypeScript 构建和 PWA 构建均通过。口语页面定向用例已实际点击“就用这个，开始评分”并进入评分结果态。
- 讯飞 ISE 于 2026-08-24 实时核验：当日用量 0、剩余服务量 10500、到期 `2026-09-10 12:33`；用户确认不购买、不自动付费，到期后先核验每日免费额度。
- P1 真实验收结果 `58d7621e-0fd7-4abb-aaf8-a6ab65e9a5fd` 已落入 `sherlock_results`，云端核对为 `data_kind=test`、`formal_completion_eligible=false`；未认证写入返回 `UNAUTHORIZED`，formal 动作返回 `FORMAL_DISABLED`。
- 发布后 24 点仍为 `family24-web-003` / `SUCCESS`；公开首页 HTTP 200，11/11 个当前静态文件与 `D:\project_antigravity\24\dist` 的大小和 MD5 精确匹配。
- `_runtime`、本机代理配置、`__pycache__` 和私有结果库数据均未迁入；旧位置未删除或改写。
- 原拟目录 `English-Listen-Speak` 为空，本轮未删除。
- 2026-08-28 已将 Sherlock 根目录的 8 个 P0/P4/P5 英语迁移快照、staging 和 artifacts 保持原名集中移入 `archive/migration-evidence/`；共 3,870 个文件、256,350,412 字节、4 个嵌套 Git，移动前后逐项一致。`D:\ObsidianVaults\Education\Sherlock` 根目录现只保留活跃 `English-Learning` 与 `Math`。
- 2026-08-28 家长确认新的四窗口架构：00 总控/学情/学习档案，01 教材与课程，02 系统与 CloudBase 运维，03 学校练习与考试批改归档；原 03 formal 分析职责并入 00。私密学习档案和校内错题库已迁入本地 `private/`，由 Git 排除。
- 2026-08-29 家长确认 P6 第一周采用 `L/S4A-T1-W01-D01` 至 `D06` 的六日听说配对方案；开发范围为 4A M1U1 p2–3，正式开放仍受学校实际已教范围约束。
- 2026-08-30 02 已完成 B：新旧编号同时兼容，草案按批准流程接入原有 `content/listening` 与 `content/speaking` 单一活动源；168 个新音频、两个 manifest、catalog/推荐顺序、路由、服务端 provider 和 formal 发布闸门均完成。线上 test 资源 12/12 儿童副本安全、168/168 音频哈希一致；新课仍为 `publication_status=test` / `visible=false`，儿童 formal 写入返回 `COURSE_NOT_FORMAL`。

## 已完成

- 开学后教学方向确认；
- CloudBase 方案 C 确认；
- 费用和免费额度初步评估；
- 项目迁移和归档策略确认；
- Codex 窗口架构确认；
- 历史上曾确认单词模块接口预留；2026-08-28 起由 D26 取消预设，未来立项时重新讨论；
- 项目治理文档包建立并校验：总控文件 8 份、P0-P6 阶段执行书 7 份、窗口说明与指令 6 份，加根目录入口文件共 23 份 Markdown；
- 已完成 P0 迁移前后的 Git、测试、课程 JSON、音频和逐文件 SHA-256 对账；
- 已迁入 6 份教材依赖、4 份家长版历史参考和 2 份私有结果清单文档；
- 已建立 `docs/迁移清单_2026-08-24.md`、`docs/硬编码路径适配清单_2026-08-24.md` 和 `docs/P0_资产SHA256清单_2026-08-24.tsv`；
- 迁移前后单元测试均为 40/40 通过，目标根 32 个项目 Python 文件编译通过，312/312 成品 MP3 可解码；
- P0 验证门达到；初次 P0 窗口按当时边界没有提交、推送、部署或提前进入 P1；2026-08-24 验收后，用户已明确授权形成独立 P0 提交并推送 `main`。
- P0 独立提交 `eb00a38298e2e76b8c2b5c6c62b5319a11303d38` 已推送 `main`，推送后工作区曾确认干净；临时克隆和迁移前快照继续保留到 P5。
- P1 React + TypeScript + Vite PWA、路由、离线/更新提示、错误边界、课程目录/推荐接口、通用结果 schema 与 test-only 云函数已完成本地实现。
- P1 本地验证：前端 19/19、服务端 9/9、旧版 Python 40/40；前端 statements 90.43% / lines 91.66%，服务端 lines 91.20%；类型检查和生产构建通过。
- P1 云端与桌面验证：12/12 静态文件上传；首页、`listening`、`speaking`、`parent`、manifest 和 Service Worker 均 HTTP 200；桌面浏览器实际加载首页、三个模块入口且无控制台错误。
- P1 独立提交 `2e7370fc813531702b6388f90ceb3b19188f468f` 已推送 `main`，推送后工作区确认干净。
- P2 听力目录、试音、五类题型、限次播放、服务端计分、幂等提交、两遍订正与家长完整 test 明细已完成；正式入口继续关闭。
- P2 本地验证：Web 34/34、云函数 16/16、旧版 Python 40/40；类型检查、生产构建和覆盖率门通过；216/216 本地 MP3 完整解码。
- P2 云端验证：242/242 静态文件上传；12/12 儿童课件信息隔离及 216/216 线上音频字节哈希通过；未认证写入和 formal 动作均被拒绝。
- P2 音频首轮真机反馈已修复并发布：试音完整播放后才允许开始；任一音频播放期间锁定其他播放/提交/订正确认；未缓存音频离线失败会立即显示加载状态并给出可重试提示。
- 修复发布后结果库只读计数：formal 为 0；listening test 为 4（含 1 条既有 P1 smoke 和本轮真机验收新增 test）。
- 用户完成针对性复验并于 2026-08-24 明确确认 P2 验收通过；锁屏、断网恢复、状态保持、布局、试音完整播放和单音频互斥均纳入真机结论。
- P3 已部署 `score-speaking` 和新版 `sherlock-api`；352/352 个静态文件上传成功，线上 12 门口语目录、S01D39 儿童课件和样例音频均为 HTTP 200，儿童副本无 `expected`、`tag` 或 `parent_note`。
- P3 部署后独立复核：API 健康状态为 `stage=P3` / `formal_enabled=false` / `writes=test-only`；family24 仍为 `family24-web-003` / `SUCCESS`，11/11 文件一致，超额付费关闭。
- P3 首次 iPad 实测表现为点击评分后立即失败。外层 `sherlock-api` 超时已由 10 秒修正为与私有评分函数一致的 60 秒并保留，但根据“立即失败”证据确认它不是本次根因。逐层对照旧 Streamlit 后，讯飞适配器已恢复其已验证的英文 ISE 请求契约（BOM 原文、`group=pupil`、10 ms 发帧、最后实际音频帧 `status=2`），同时保留安全诊断码。
- 真正根因为 CloudBase 函数间传递 JSON 时会重排 payload 字段，而旧内部 HMAC 直接签署 `JSON.stringify(payload)`，导致内容相同但字段顺序变化后立即验签失败。签名方与验签方现均使用递归字段排序的规范化 JSON；新增“CloudBase 重排字段仍可验签”回归测试，并移除临时事件形状诊断入口。
- 2026-08-25 自动真实线上评分探针通过：使用 S01D39 第 1 题现有示范音频，经 16 kHz 单声道 PCM/WAV、内部 HMAC、`score-speaking`、讯飞 ISE 和私有 test 录音上传完整链路返回 `97` 分、`3` 星、`Rejected=False`、`RecordingSaved=True`。探针脚本不输出密钥，临时明文载荷执行后删除；只保留 test 录音证据。
- 2026-08-25 评分修复后的首次静态重建遗漏 `VITE_CLOUDBASE_*` 公共构建变量，导致家长登录页显示“站点尚未完成 CloudBase 公开配置”；用户反馈后已从线上保留的上一版有效 P3 bundle 恢复 PublishableKey，带完整配置重新构建并上传 352/352 文件。最终线上活动 bundle `index-BvUctEPZ.js` 已核验环境 ID 与 PublishableKey 有效；新增生产构建硬门，缺少任一 CloudBase 公共变量时构建直接失败，防止同类错误再次部署。
- 随后的 iPad 实测进入评分主链路后返回“课程刚刚更新”。根因不是浏览器操作，而是静态课件生成器按原始文件字节计算 `course_version`，API 按解析后的课程对象计算语义版本，同一课因此永久不一致。两端现统一调用 `stableVersion(course)`；新增覆盖全部 12 门口语课的跨产物版本回归测试，前端课程请求加入 cache-busting 与 `cache: no-store`，Service Worker 不再预缓存口语 JSON。
- 最终修复已重新发布：352/352 文件上传成功；线上目录、12 个儿童课程 JSON 与 API 健康响应逐课对账为 12/12 一致，S01D39 统一为 `d16bf656e92b3078`；儿童副本仍无私有字段，API 仍为 `stage=P3` / `writes=test-only` / `formal_enabled=false`。修复后真实讯飞探针再次得到 97 分、3 星并保存到 test 私有路径。
- 用户随后在真实按钮上得到 `INTERNAL_ERROR`。复盘确认旧“真实讯飞探针”直接调用了私有 `score-speaking`，没有覆盖浏览器实际经过的 `sherlock-api` 首次录次幂等读取，因此不能作为按钮主链路验收。生产根因为 `getSpeakingTake()` 对尚不存在的首次录次使用文档直读，CloudBase 在该空文档条件下抛出异常；现改为按 `take_id` 的 `where(...).limit(1)` 空结果安全查询，并增加首录次回归测试。
- 修复发布后，2026-08-25 使用真实 CloudBase 匿名身份和隔离的合成 TEST 会话完成公开 SDK → `sherlock-api` → `score-speaking` → 讯飞 ISE → 私有录音存储的完整线上主链路：返回 `ok=true`、3 星和逐词反馈；相同请求再次调用返回 `idempotent=true`；录音 `q01-take1.wav` 在线存在，大小 132942 字节。该验证没有使用或写入 formal。

## 下一步

P6/B 工程兼容、音频生成和 CloudBase 隐藏 test 部署已经完成。下一步不是继续改代码，而是由 00/家长按学校当天实际已教范围决定 D01–D06 中哪些课程可以从 test 改为 formal 可见；未获批准前全部新课继续隐藏且服务端拒绝 formal 写入。线上 formal 由 00 直接分析；学校练习/考试交给 03 批改入库。

P0、P4 与 P5 的临时克隆、迁移前备份、原始快照和失败网络克隆目录继续保留，清理属于破坏性操作，须经家长另行明确授权。

当前治理入口：`docs/窗口指令/00_总控与路线图窗口.md`。P6 获准后执行 `docs/阶段计划/P6_开学后课程运营.md`。

## 当前阻塞

P5 无阻塞且退出条件全部满足。P6 第一周工程阻塞 `BLOCKED_BY_ID_COMPAT` 已解除；当前唯一发布闸门是 00/家长确认学校当天实际已教范围并明确批准 formal 开放。浏览器自动化已打开线上页面但 DOM 读取连续超时；不影响 HTTP、逐文件哈希、云函数边界和全套回归结论，也不要求孩子为隐藏 test 课程执行额外验收流程。

## 尚未实时确认但不阻塞

- 讯飞授权于 2026-09-10 到期后，每日免费 500 次是否继续可用。
- `score-speaking` 沿用项目固定的 `@cloudbase/node-sdk@3.18.3`，其传递依赖审计仍报 4 high / 1 moderate；未执行会导致 SDK 破坏性变更的 `npm audit fix --force`。
- 开学后第一批课程的学校实际页段。

## 状态更新格式

每次阶段结束追加：

```text
日期：
阶段：
完成：
验证：
提交/版本：
线上地址：
遗留问题：
下一步：
```

## 2026-08-24 P0 状态登记

```text
日期：2026-08-24
阶段：P0 项目迁移与归档
完成：完整 Git 历史迁入新根；治理文档、教材依赖和历史参考受控合并；迁移与硬编码清单已生成
验证：迁移前后测试 40/40；24 份课程 JSON；312/312 成品 MP3 解码；Git HEAD、远端、可达与不可达对象清单一致；Streamlit 首页可唤醒
提交/版本：P0 迁移前基线 HEAD 14d4d659ebc71832cc1a388f79f9bb80c9a974e1；验收后的独立迁移提交由本记录所在 main 提交承载
线上地址：https://sherlock-missions-pesuyw9p75offrqtdadiag.streamlit.app
遗留问题：P4 前须凭受控凭证实时导出并对账私有结果库；线上课程提交、录音和评分链路本轮未验证
下一步：推送 P0 独立提交并确认工作区干净；随后读取并执行 P1，在任何 CloudBase 写入前完成只读资源核验
```

验收后决定：用户已授权把 P0 迁移结果形成一个独立 Git 提交并推送 `main`；推送后确认新根工作区干净，再进入 `docs/阶段计划/P1_CloudBase基础架构.md`。临时克隆和迁移前快照保留到 P5 正式切换验收完成。

## 2026-08-24 P1 进行中状态登记

```text
日期：2026-08-24
阶段：P1 CloudBase 基础架构（验收通过）
完成：PWA 和 test-only 云函数实现；4 个私有集合、存储前缀、publish key、匿名身份和 sherlock-api；密码哈希配置；真实 test 写入；/sherlock-english/ 静态发布
验证：前端 19/19、服务端 9/9、旧版 Python 40/40；类型检查和构建通过；云函数 health 正常；真实结果固定为 test 且不具备 formal 完成资格；未认证写入和 formal 动作均被拒绝；12 个静态文件及深链接在线；24 点 11/11 文件未变化；超额付费仍关闭
提交/版本：P1 独立提交由本记录所在 main 提交承载；P0 main 基线 eb00a38298e2e76b8c2b5c6c62b5319a11303d38
线上地址：https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/；24 点原 URL 正常
遗留问题：真实 iPad 断网重启未单独留存截图；CloudBase SDK 传递依赖的 npm audit 高危公告需单独评估，不能直接强制降级
下一步：P1 独立提交推送并确认工作区干净后，停留在 P1 完成态；不得进入 P2
```

## 2026-08-24 P1 iPad 验收登记

```text
日期：2026-08-24
阶段：P1 CloudBase 基础架构
完成：真实 iPad 启动 PWA，进入听力和跟读口语基础入口；两个入口均显示 P1 预期占位状态和 formal 入口关闭
验证：听力页面明确课程将在 P2 迁移；跟读口语页面明确课程将在 P3 迁移；页面可返回本周任务；用户确认 P1 验收通过
提交/版本：P1 独立提交由本记录所在 main 提交承载；P0 main 基线 eb00a38298e2e76b8c2b5c6c62b5319a11303d38
线上地址：https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/
遗留问题：SDK 传递依赖安全公告待单独评估；真实 iPad 断网重启未单独留存证据
下一步：P1 独立提交推送并确认工作区干净后，停留在 P1 完成态；不进入 P2
```

## 2026-08-24 P2 验收登记

```text
日期：2026-08-24
阶段：P2 听力模块迁移（验收通过）
完成：W01D39–W01D50 目录、试音、五类题型、限次播放、答题暂存、服务端计分、幂等提交、两遍订正、家长 test 明细；242 个静态文件发布
验证：Web 34/34；云函数 16/16；旧版 Python 40/40；类型检查与构建通过；本地 MP3 216/216 解码；线上儿童课件 12/12 信息隔离；线上 MP3 216/216 SHA-256 一致；UNAUTHORIZED 与 FORMAL_DISABLED 生效；结果库 formal=0；首轮 iPad 发现的试音提前放行和跨题叠音已修复，用户复验后确认通过
提交/版本：P1 基线 2e7370fc813531702b6388f90ceb3b19188f468f；P2 独立提交由本记录所在的 main 提交承载
线上地址：https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/
遗留问题：CloudBase SDK 传递依赖仍有 4 high / 1 moderate 公告，未执行破坏性降级
下一步：完成 P2 独立提交和推送并确认工作区干净后停止；不自动进入 P3
```

## 2026-08-25 P3 验收登记

```text
日期：2026-08-25
阶段：P3 跟读口语与讯飞迁移（验收通过）
完成：S01D39–S01D50、iPad 录音/回放、讯飞 ISE、三星与三次门控、加密 proof、幂等评分、私有 test 录音和家长受控回放；formal 继续关闭
验证：Web 51/51；sherlock-api 31/31；score-speaking 11/11；旧版 Python 40/40；线上 12/12 课程版本一致；公开 SDK 经 sherlock-api 到讯飞及私有录音的真实主链路返回 3 星且重复请求 idempotent=true；用户真机复验后明确确认验收通过
提交/版本：P2 基线 954c02400a69ad7aed22574baa742500dfc15d1a；P3 独立提交由本记录所在的 main 提交承载并推送
线上地址：https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/
遗留问题：讯飞当前授权到期后每日免费额度是否延续仍待到期前实时核验；CloudBase SDK 传递依赖公告未执行破坏性强制升级
下一步：P3 提交推送并确认工作区干净后停止；等待用户明确授权进入 P4
```

## 2026-08-25 P4 自动迁移与部署登记

```text
日期：2026-08-25
阶段：P4 数据迁移与家长端（验收通过）
完成：固定原私有库提交并生成外部原始快照、逐文件 SHA-256 和课程映射；143 条历史结果及 422 个 WAV 以只追加幂等方式迁入 CloudBase；家长端默认 formal 并提供独立 test、模块/课程/日期筛选、听力/口语明细及 600 秒录音临时回放；旧库、外部快照和导入前 CloudBase 备份均保留
验证：历史结果 143/143 全字段匹配、formal=142/test=1、listening=63/speaking=80；验收后线上总数 150、formal 仍为 142、test 为 8；录音 422/422 路径与大小一致，formal=382/test=40，6/6 云端下载样本 SHA-256 一致；再次干跑结果跳过 143、录音跳过 422、异常 0；迁移测试 8/8、sherlock-api 33/33、Web 52/52，类型检查/覆盖率/生产构建通过；线上 API stage=P4、formal_enabled=false、writes=test-only，未认证家长查询被拒绝；24 点仍为 family24-web-003 / SUCCESS / 11/11，超额付费关闭
提交/版本：P3 main 基线 9f18f37；P4 独立提交由本记录所在的 main 提交承载并推送
线上地址：https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/
遗留问题：无 P4 验收阻塞；PWA 若出现“新版本已就绪”仍应点“立即更新”；讯飞到期后免费额度与 SDK 传递依赖公告继续按原边界处理
下一步：完成 P4 独立提交、推送并确认工作区干净；停留在 P4，等待用户另行授权进入 P5
```

## 2026-08-26 P5 切换前登记

```text
日期：2026-08-26
阶段：P5 上线切换与验收（切换窗口进行中）
完成：formal 儿童会话、正式完成进度、听力/口语服务端 data_kind 判定、正式录音路径隔离、五课窗口、家长 test 路由隔离、Streamlit 只读迁移页和自动关闭 formal 的部署保护已实现
验证：sherlock-api 37/37 且覆盖率门通过；score-speaking 12/12 且覆盖率门通过；Web 57/57 且覆盖率门通过；旧 Python 40/40；Streamlit 只读定向测试 3/3；TypeScript 与 PWA 生产构建通过
提交/版本：P4 main 基线 355b35b；P5 切换提交待形成并推送
线上地址：https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/
遗留问题：线上 formal 尚未开启；一对真实 formal 课程、即时对账和 24 小时复核尚未执行
下一步：推送 Streamlit 只读版本并在线确认；在不影响 24 点且不启用付费的前提下执行 CloudBase 原子切换
```

## 2026-08-26 P5 正式切换登记

```text
日期：2026-08-26
阶段：P5 上线切换与验收（线上切换完成，真机持久化验收待完成）
完成：基于结果仓库 cb9bc864 创建独立 P5 最终快照；追加迁移 W01D44、W01D45、S01D44、S01D45 的 8 条正式结果及 17 个录音；Streamlit 只读上线并关闭旧写入口；CloudBase 两支云函数、PWA 和 FORMAL_ENABLED=true 已发布
迁移验证：151/151 源结果完成对账（新增 8、跳过 143、冲突 0），151/151 字段匹配；439/439 录音路径与大小匹配，6 个 formal/test 云端下载样本 SHA-256 一致；旧仓库在只读上线后仍为 cb9bc864，无切换窗口漏项
应用验证：sherlock-api 37/37、score-speaking 12/12、Web 57/57、旧 Python 40/40、迁移单测 9/9；覆盖率门、类型检查和生产构建通过；真实浏览器确认首页、听力、口语均为 FORMAL，W44/W45 与 S44/S45 已完成，当前推荐 W46/S46，窗口显示 44–48
安全验证：线上 health 为 stage=P5 / formal_enabled=true / writes=formal-and-test；未认证写入仍被拒绝；family24 仍为 family24-web-003 / SUCCESS / 11/11；体验版、2027-02-04 到期、超额付费关闭均未改变
提交/版本：P5 主切换提交 e2bc8fa 已推送 main；部署传播等待修复与本登记由后续状态提交承载
保留项：P0、P4、P5 最终快照、迁移产物及失败网络克隆目录均保留，不删除
遗留问题：需在真实 iPad 完成新的正式 W01D46 与 S01D46，随后即时对账；24 小时后复核结果和私有录音仍存在，方可宣布 P5 完整验收通过并清理保留项
下一步：家长打开 CloudBase 新地址完成 W01D46 和 S01D46；不要回旧 Streamlit 做课
```

## 2026-08-27 P5 iOS 录音热修复登记

```text
日期：2026-08-27
阶段：P5 正式入口 iOS 录音可靠性热修复（验收通过）
完成：逐行对照旧 Streamlit 与 PWA 录音实现；PWA 改为每录次新建麦克风流、结束即停轨，AudioContext 在点击手势内恢复，并启用浏览器自动增益/降噪/回声消除；课程推荐标签、完成置灰和按钮留白同步微调
验证：前端 59/59；函数覆盖率 80.34%、行覆盖率 89.95%；Python 40/40（另 41 个 subtests）；TypeScript 与生产构建通过；本地浏览器 1024×768 和 390×844 均无横向溢出，课程按钮 56px、口语题内按钮 62px、返回入口 52px；CloudBase 静态文件 352/352 上传成功，线上新 JS/CSS 已核对包含自动增益和推荐/完成样式；用户在真实 iOS 上复验并确认首录、麦克风释放、回听音量及 UI 微调均已修复
CloudBase 安全：发布前 family24 为体验版、2027-02-04 到期、超额关闭、剩余 2954.14；发布后复核剩余 2953.99，24 点仍为 family24-web-003 / SUCCESS / 11/11；本轮仅更新 sherlock-english 静态托管，未重部署云函数或改正式数据
提交/版本：设计记录提交 dfae391；实现修复由本记录所在的后续独立提交承载并推送
遗留问题：本热修复无验收遗留；P5 一对正式课程的即时对账与 24 小时持久化复核仍待完成
下一步：继续 P5 一对正式课程与即时/24小时持久化对账
```

## 2026-08-28 P5 完整验收登记

```text
日期：2026-08-28
阶段：P5 上线切换与验收（完整验收通过）
正式课程：W01D46 结果 e3a08a08-59ff-4503-94cc-201efa73d090，formal/completed/eligible=true，80 分；S01D46 结果 abc139f7-599a-46e7-a050-315420f3c0d3，formal/completed/eligible=true，99 分、24/24 星
即时与持久化验证：两门课程完成后即时对账通过；满 24 小时后再次查询，W01D46、S01D46 正式记录仍各 1 条，S01D46 的 9/9 个录音文件仍存在且非空；家长确认跨设备/重登后的推荐进度为 W01D47、S01D47
资源隔离：family24 仍为体验版，2027-02-04 23:59:59 到期，超额付费关闭；当前周期总额度 3000、已用 52.4、剩余 2947.6；24 点仍为 family24-web-003 / SUCCESS / 11/11
入口结论：CloudBase PWA 是唯一正式入口；Streamlit 保持只读且不再接收 formal
提交/版本：P5 主切换 e2bc8fa、iOS 录音修复 419e669 均已推送 main；本登记由后续状态提交承载
保留项：P0、P4、P5 快照、迁移产物及失败网络克隆目录仍保留；本轮不删除
遗留问题：无 P5 验收遗留；讯飞到期后的免费额度与既有 SDK 依赖公告按原边界继续观察
下一步：停留在 P5 完成态；等待家长明确授权后再进入 P6_开学后课程运营
```

## 2026-08-28 治理文档与窗口入口对齐

```text
日期：2026-08-28
阶段：P5 完成态 / P6 总控讨论准备
完成：当前对话正式承担 00 英语系统总控与路线图职责；清除总计划、路线图、窗口架构、开工索引和窗口指令中的过期 P0 开工导向；重写 02 窗口为迁移后的长期开发运维指令；给根目录旧 Streamlit 文档增加历史警示
验证：当前入口文件不再要求执行 P0 或把旧仓库当作活跃源；P6 路由统一为 00 决策、03 formal 分析、01 内容开发、02 测试部署与运维
代码/生产影响：无代码、课程、部署、CloudBase 或正式学习数据变更
教材核查：当前活跃项目和旧教育归档中仅发现 4A 四年级上教材资产，未发现四年级下/4B 教材原件、索引或词库
下一步：在 00 窗口讨论 P6 启动条件；开始首批课程前由家长提供并确认学校实际教材页段
```

## 2026-08-28 英语迁移证据集中归档

```text
日期：2026-08-28
阶段：P5 完成后的本地目录治理
完成：将 Sherlock 根目录 8 个英语迁移快照、staging、P4/P5 备份与迁移产物整体移入 English-Learning/archive/migration-evidence，原文件夹名称保持不变；Math 未移动
验证：移动前后均为 3,870 个文件、256,350,412 字节、4 个嵌套 Git；8/8 源路径消失且目标存在；Sherlock 根目录只剩 English-Learning 与 Math；归档目录被主仓库 .gitignore 排除
数据边界：未删除、去重、压缩或改写归档内容；未触碰课程、CloudBase、正式结果或录音
文档：新增 archive/README.md，并更新 P0/P4 路径说明和当前状态
下一步：归档继续本地只读保留；删除或清理必须另行获得家长明确授权
```

## 2026-08-28 四窗口架构与私密学习档案迁移

```text
日期：2026-08-28
阶段：P5 完成态 / P6 治理准备
家长决策：正式采用四个长期窗口；原 03 正式学情与数据分析并入 00，新 03 为学校练习与考试批改归档；背单词、自动出纸面卷及其他新增功能未来重新讨论
职责：00 是学习档案唯一维护者；03 是校内错题库唯一维护者；01 只接收 00 确认的内容目标；02 不处理 private 学生材料
隐私：新增 private/student-records 与 private/school-evidence，本地保存并由 .gitignore 排除，不进入公开 Git
档案迁移：旧学习档案以 SHA-256 A6A4880CEF0DD452FCAE46B2B928553A10BA3375E5372663C2A14C5805C65D29 完整复制后续写；旧源不删除、不双写；历史 E1–E37 保留，E32 作废、E36 并入 E21，新编号从 E38 开始
最新学情：吸收 W01D46 formal 80 分、S01D46 formal 99 分/24 星及 9/9 录音 24 小时持久化摘要；因缺逐题错题/订正/weak_words 明细，不新增 E 编号、不改变旧 E 状态
代码/生产影响：无应用代码、课程、部署、CloudBase 或正式学习数据变更
下一步：家长可用 01 提示词启动教材与课程窗口，用 03 提示词启动学校材料批改窗口；P6 课程仍须先确认学校实际教材页段
```

## 2026-08-29 P6 第一周课程设计确认

```text
日期：2026-08-29
阶段：P6 开学后课程运营 / 第一周设计
家长决策：采用方案 1，新学期编号为 L4A-T1-W01-D01 / S4A-T1-W01-D01；周二至周日每天一组，共 6 组、12 门课程
教材边界：第一周开发范围锁定 4A M1U1 p2–3；正式开放不得越过学校当天已经教授的范围
梯度：听力 20/20/20/25/25/25 题；口语每天 8 题并保持 6 repeat + 2 QA；难度 L1 至 L3 综合逐日上升；每日总时长约 25/25/30/30/35/35–40 分钟
工程影响：现有听力、口语、音频路径和目录 schema 仍限制旧 W01Dxx/S01Dxx 编号；须由 02 完成兼容改造，01 不得越界修改核心程序
生产影响：本次只确认并登记设计，尚未创建课程、音频、test/formal 记录或执行部署
下一步：向 01 派发第一周内容开发提示词；向 02 派发新编号兼容任务；完成校验和家长 test 验收后再按学校进度开放
```

## 2026-08-29 P6 第一周 01 内容交付登记

```text
日期：2026-08-29
阶段：P6 开学后课程运营 / 第一周内容开发
完成：6 个 study pack、L4A-T1-W01-D01 至 D06、S4A-T1-W01-D01 至 D06 的隔离内容草案；家长版答案原文；12 份儿童安全草案副本；168 项音频文本与生成清单；教材映射和校验报告
教材验证：实际渲染并视觉核对教材 PDF p2-p3；与 Lesson 索引、TSV/JSON 词库和 M1U1 词句包交叉核对；未进入 p4-p6
验证：内容定向 12/12；全仓 Python 52/52；Web 59/59；sherlock-api 37/37；score-speaking 12/12；TypeScript typecheck 与 Python 编译通过；儿童草案 12/12 无答案/原文/考点/数字评分且 visible=false
提交/版本：基线 4e74e94；01 独立本地内容提交由本登记所在后续提交承载；不 push
生产影响：无部署、无 CloudBase 修改、无 test/formal 学习记录、无完成状态或学习档案变更
阻塞：BLOCKED_BY_ID_COMPAT；正式 schema、MP3、manifest、test 部署和 iPad 验收须等待 02 完成新 ID、音频路径、catalog 与推荐顺序兼容
下一步：02 完成兼容后接入单一活动课程源，生成并校验 168 个 MP3，重新运行全套正式校验；每日 formal 开放仍由 00 按学校当天已教范围决定
```

## 2026-08-29 A：formal 会话无损续期本地实现

```text
日期：2026-08-29
阶段：P5 生产事故热修复 A / 已部署、待 iPad 真实 formal 验收
事故根因：PWA 只在首次加载时创建约 7200 秒 formal 会话，后台恢复和临近过期不续期；服务端又把 listening result 与 speaking take/result 的幂等所有权绑定到会变化的 token，换 token 后可能误报 RESULT_ID_CONFLICT；听力还把业务错误统一显示成网络错误
本地修复：新增仅供儿童 formal 使用的会话管理器，在临近过期、pageshow/visibilitychange 恢复和 UNAUTHORIZED 时单飞续期，原请求最多重试一次；家长 test 不接入自动续期；服务端的新 formal 结果/take 使用稳定 CloudBase caller 的 HMAC 所有权，同时保留旧 token 标识和历史行旧规则
状态保留：自动重试沿用同一请求对象和 result_id；听力答案、播放次数、订正状态不重建；口语 take/attempt/proof/星数及录音引用不重建；响应丢失后的重复请求由服务端幂等返回
错误呈现：formal 区分正在恢复与恢复失败；test 过期要求重新认证；只有离线或明确传输异常显示网络错误；其他服务端错误显示安全诊断码
验证：Web 68/68，覆盖率 statements 84.63%、branches 78.94%、functions 80.45%、lines 89.98%；sherlock-api 40/40，覆盖率 lines 93.26%、branches 77.83%、functions 85.94%；score-speaking 12/12；Python 52/52；迁移/构建环境 Node 测试 10/10；TypeScript 与 production-mode build 通过
生产发布：家长明确批准后于 2026-08-30 仅更新 sherlock-api 与 sherlock-english 静态托管；函数部署完成，PWA 352/352 文件上传成功，线上活动 bundle 由 index-C1VOY_sS.js 切换为 index-_vmlXHVO.js，并核验包含 formal 自动恢复与恢复失败提示
部署后验证：health 仍为 stage=P5 / formal_enabled=true / writes=formal-and-test；无效 formal token 返回 UNAUTHORIZED；family24 仍为 family24-web-003 / SUCCESS / 11/11；体验版有效至 2027-02-04，超额付费关闭；发布前后剩余额度 2941.94 → 2939.16；Git 工作区无未提交改动（登记修订除外）
数据边界：未调用生产学习写接口，未创建用于验收的 test/formal 学习记录；未修改 W01D49、S01D49 或任何历史结果/录音；家长 test 仍须密码登录且不接入自动续期
回滚：函数代码与静态站点均可由 A 提交的父提交重新构建发布；若 iPad 出现无法进入、数据隔离异常、重复结果或正式流程回归，立即停止 W01D50/S01D50 并执行回滚
后续决定：家长认为专门等待两小时并按步骤制造过期过于繁琐，批准保留 A 线上热修复并转为真实使用中的自然观察，直接进入 B；W01D50/S01D50 不再作为进入 B 的前置人工流程
```

## 2026-08-30 B：P6 新学期编号兼容与隐藏 test 部署

```text
日期：2026-08-30
阶段：P6/B 新编号兼容 / test 已部署、formal 未开放
完成：旧 W01Dxx/S01Dxx 与新 L/S4A-T1-W01-D01 至 D06 同时兼容；12 门新课接入原有单一活动源；catalog、推荐顺序、路由、音频路径、Python/Web/云函数 schema 与 provider 均支持新旧编号
发布闸门：12 门新课统一 publication_status=test、visible=false；儿童 formal 无法从目录看到，直接写入也由服务端返回 COURSE_NOT_FORMAL；家长 test 仍必须密码认证
音频：新生成 168 项，ffmpeg 解码 168/168；发布后 168/168 逐文件 SHA-256 与本地一致；manifest 与儿童安全副本同步完成
验证：Python 53/53；Web 73/73；sherlock-api 43/43；score-speaking 13/13；TypeScript、Python 编译和生产构建通过；线上 12 门隐藏儿童课件安全字段校验通过；CloudBase formal 拦截听力/口语均通过
CloudBase：只更新既有 score-speaking、sherlock-api 和 sherlock-english 静态托管，没有创建新资源、没有开启付费、没有写 test/formal 学习结果或录音；health 保持 P5/formal-and-test
24 点：family24-web-003 / SUCCESS / 11/11，HTTP 200，未受影响；体验版有效至 2027-02-04 23:59:59，超额付费关闭，当前剩余 2939.12 点
浏览器验收：自动浏览器已打开正式列表页，但 DOM 读取连续超时；HTTP、静态哈希、构建和云函数边界均已完成自动验收，不要求孩子执行隐藏 test 专项流程
正式发布状态：未发布；D01-D06 均不可用于儿童 formal。正式开放必须由 00/家长按学校当天实际已教范围另行明确批准
回滚：以 B 提交的父提交重新构建并部署两支函数和静态站点；不迁改任何旧课程 ID、成绩、录音路径或历史记录
```

## 2026-08-31 GitHub Pages 候选入口阶段一部署

```text
日期：2026-08-31
阶段：P5 后续入口故障治理 / 方案 A 阶段一候选部署与 iPad 真机验收完成
家长决策：采用 GitHub Pages /sherlock-english/ 作为候选前端，CloudBase 后端与数据保留；先仅家长 test，不切换儿童 formal；不购买域名、不申请 ICP 备案、不新增付费资源
套餐约束与修订：CloudBase 返回 [CreateAuthDomain] 当前套餐无法执行此操作，不能新增 GitHub Web 安全域名；改用同一环境 HTTP 网关转发 sherlock-api，函数只允许 https://summertxia0306-hue.github.io Origin，原 Event/Web SDK 调用兼容保留
源码提交：5c0512e（隔离发布工具）、c044a6a（HTTP 网关传输与双入口云函数）；设计文档 c6fe54d
Pages 发布：独立 Pages 仓库提交 3eb0d9b，GitHub Actions run 33348996066 成功；候选 URL https://summertxia0306-hue.github.io/sherlock-english/
CloudBase：已更新 sherlock-api 函数代码并创建 /sherlock-api HTTP 路由；OPTIONS 为 204，GitHub Origin health 为 200，错误客户端为 400，非许可 Origin 为 403 且无 ACAO；原 Event health 仍返回 P5/formal-and-test
自动验证：Python 53/53；Web 74/74，覆盖率 statements 84.79%、branches 79.34%、functions 80.98%、lines 90.27%；sherlock-api 47/47，覆盖率 lines 92.94%、branches 77.61%、functions 86.03%；score-speaking 13/13；发布隔离 5/5；TypeScript、production build、敏感信息扫描通过
线上静态验收：根、listening、speaking、parent、主 JS、Manifest、Service Worker、听力/口语 JSON 与代表音频均 HTTP 200；HTML 无 Content-Disposition；候选树 531 个文件。Pages 提交在 sherlock-english/ 之外零变更，家庭 24 点根站仍为 HTTP 200 / 标题“家庭 24 点”
数据边界：自动验证只调用 health 和错误输入边界，不登录家长端、不提交课程、不创建 test/formal 学习结果或录音；private 未发布，候选包不含 CloudBase Publishable Key、JWT 或管理密钥
浏览器限制：候选地址可导航，但自动化 DOM/控制台读取超时，因此不登记为真实浏览器全流程通过；HTTP、构建、提交和云函数证据已通过，iPad Safari 仍是最终门槛
真机验收：家长在无 VPN iPad 完成听力 test、口语录音/回放/8 题评分与最终 test 提交；云端复核 test 结果、私有录音和隔离边界均通过
正式状态：原 CloudBase 地址继续是唯一儿童 formal 入口；GitHub Pages 已通过阶段一，但家长尚未明确批准阶段二，因此不执行正式入口切换
回滚：删除 Pages 仓库 sherlock-english/ 子目录并删除 HTTP 网关路由；CloudBase 原静态入口、Event 调用、正式数据和录音不变
```

## 2026-08-31 GitHub Pages 口语分块上传修复

```text
日期：2026-08-31
阶段：GitHub Pages 候选入口阶段一 / 口语评分上传故障修复及整课 test 验收通过
根因：同一 GitHub Origin 和 CloudBase HTTP 网关实测约 102400 字节以内返回 200，约 102432 字节起返回 413/EXCEED_MAX_PAYLOAD_SIZE；12 秒 16 kHz 单声道 PCM/WAV Base64 约 512 KiB，因此请求在 sherlock-api 和讯飞运行前被平台拒绝
修复：只在 GitHub HTTP transport 内把 wav_base64 按 65536 字符分块，最多 2 块并发、单块最多重试 2 次；sherlock-api 将分块写入 caller/session 绑定的私有 tmp-speaking 路径，校验块与整段 SHA-256、大小、顺序和精确 file_id 后，再调用原 score-speaking；成功或幂等返回后尽力清理临时块
兼容边界：原 CloudBase Web SDK/Event 整段内部调用保持不变；score-speaking 未重部署，讯飞契约、proof、星级、三次门控、最终 formal/test 私有录音路径和历史数据均未改变
自动验证：Web 77/77；sherlock-api 52/52，lines 93.30%/branches 76.68%/functions 87.82%；score-speaking 13/13；Python 53/53；迁移与 Pages 发布隔离 14/14；TypeScript、production build、敏感信息扫描通过；12 秒样例拆为 8 块，最大单请求小于 75 KiB
线上验证：CloudBase HTTP 65,624 字节分块形状请求已穿过网关并由新版业务层返回 UNAUTHORIZED，不再是 413；候选入口 HTTP 200，活动 bundle index-CumPV6Dc.js 同时包含 uploadSpeakingChunk/scoreUploadedSpeakingTake；CORS 仍只允许 GitHub Origin；Pages 工作流 33361066952 success
资源与隔离：Pages 只更新 sherlock-english/ 7 个构建条目，Pages 提交 ac6bd8e；家庭 24 点根站 HTTP 200/标题“家庭 24 点”，CloudBase 仍为 family24-web-003/SUCCESS/11-11；体验版有效至 2027-02-04，超额付费关闭，发布前后剩余 2936.52 点
提交/版本：设计 2fd4a3a；实现 e1cf455；Pages ac6bd8e；候选 URL https://summertxia0306-hue.github.io/sherlock-english/
数据边界：自动验证只使用无效 session 的边界请求，未创建 test/formal 结果、speaking take、临时分块、最终录音或完成状态；未修改学习档案；家长此前成功的听力 test 继续只作功能验收
回滚：sherlock-api 恢复到实现提交 e1cf455 的父提交 2fd4a3a 对应代码；Pages 恢复 3eb0d9b；不删除任何历史结果或最终录音
真实 iPad 复验：家长在无 VPN iPad Safari 重新录制口语第 1 题并点击评分，确认评分成功；提交后的反馈约 3 秒，符合分块上传、云端合并校验和讯飞评分的预期链路
整课验收：家长已在无 VPN iPad 完成 8 题及最终 test 提交，并明确确认整体验收通过；云端结果 e78b76f2-9c2e-4f01-a260-0f7a02f6f8fd 为 S01D39/test/completed、97 分、24/24 星、8/8 题且每题 1 次有效评分；8 个最终 WAV 均存在且非空，临时分块为 0，formal_completion_eligible=false
剩余边界：阶段一无遗留；家长未明确批准阶段二前，GitHub Pages 仍不是儿童 formal 入口
```

## 2026-08-31 私有 COS 直传隔离探针候选部署

```text
日期：2026-08-31
阶段：GitHub Pages 口语性能优化可行性验证 / 候选已部署、待无 VPN iPad 真机验收
家长决策：批准设计与规格；只验证一份确定性 150KiB WAV 直传私有 COS，不使用麦克风、不调用讯飞、不写 test/formal 结果或学习档案；现行分块上传仍为生产回滚链路
服务端边界：仅家长 test session 可申请；对象固定写入 sherlock-english/test/direct-upload-probe/；PUT 签名 120 秒有效；ticket 绑定 session、caller、精确 file_id、字节数、SHA-256 和 content-type；验证或取消后删除对象
CORS：保留 COS 既有规则，只新增 ID=sherlock-direct-upload-probe-github；Origin 精确限定 https://summertxia0306-hue.github.io，方法仅 PUT，请求头仅 Content-Type，预检实测 200；未开放匿名读取或通配 GitHub Origin
入口隔离：VITE_DIRECT_UPLOAD_PROBE 只在 GitHub Pages 候选构建设为 true；CloudBase 正式静态构建默认 false；按钮仅在家长密码认证成功后出现
自动验证：sherlock-api 60/60，覆盖率 lines 92.22%/branches 76.63%/functions 87.72%；Web 82/82，statements 85.07%/branches 78.60%/functions 81.49%/lines 90.54%；score-speaking 13/13；Python 53/53；TypeScript 与 production build 通过
安全复核：无效 session 的线上 createDirectUploadProbe 返回 UNAUTHORIZED；函数部署前后环境变量内容完全一致；新增 cos-nodejs-sdk-v5 固定为 3.0.0；npm audit 的 5 项告警均来自既有 @cloudbase/node-sdk 依赖链，未执行破坏性强制升级
资源复核：family24 仍为 family24-web-003/SUCCESS/11-11；体验版有效至 2027-02-04，超额付费关闭，预检时剩余 2933.61 点；未新建环境、数据库、函数、网关或付费资源
发布证据：设计 472a5d6；实施计划 866f2c2；实现 afdfbbc；Pages 968fd0b；GitHub Actions run 33384616270 success；线上活动 bundle index-BBGwsV5w.js
数据边界：自动验证只执行 health、CORS OPTIONS 和无效 session 边界；未创建探针对象、课程结果、speaking take、录音或完成状态；未修改夏洛恪英语学习档案
回滚：Pages 恢复 ac6bd8e；sherlock-api 恢复 afdfbbc 的父提交对应代码；删除 COS CORS 规则 sherlock-direct-upload-probe-github；历史结果、录音和现行分块链路不动
安卓预验收：家长在关闭 VPN 的安卓手机上运行成功；153600 字节完整通过，PUT 501ms、服务端核验与删除 1671ms、总计 3744ms，页面显示“对象已清理”；随后云端查询 sherlock-english/test/direct-upload-probe/ 为 0 个对象
安卓界面观察：截图顶部仍显示“当前离线”，但签票、跨域 PUT、服务端下载核验和删除均完成，判定为页面网络状态提示误报；该现象不否定本次传输结果，也暂不扩展为本轮直传功能改造
当前结论：存储直传在安卓无 VPN 网络上技术可行，单次原始二进制 PUT 约 0.5 秒；3744ms 不是完整口语评分耗时，不能据此承诺讯飞反馈时间；现行分块链路继续不变
待验收：补做一次无 VPN iPad Safari 同样探针；通过后才可形成“进入正式直传替换设计”的最终可行性结论，仍不得直接切换正式口语链路
```

## 2026-09-01 私有 COS 直传三档探针扩展部署

```text
日期：2026-09-01
阶段：GitHub Pages 口语性能优化可行性验证 / 三档候选已部署、待真机补测
家长决策：三档规格通过；固定允许 153600、409600、700000 字节，分别对应 150KiB、400KiB、700KB；每次只运行一档，不提供批量执行
实现边界：前后端均采用精确白名单，不接受范围内任意其他大小；沿用 120 秒签名、caller/session/ticket/path/hash/type 绑定及验证后删除；正式口语仍使用既有分块链路，讯飞评分、formal/test 数据和课程逻辑均未改变
自动验证：Web 82/82，coverage statements 85.15%/branches 78.71%/functions 81.67%/lines 90.57%；sherlock-api 60/60，coverage lines 92.21%/branches 76.63%/functions 87.72%；score-speaking 13/13；Python 53/53；TypeScript typecheck 与 GitHub Pages production build 通过
安全复核：sherlock-api 采用 code-only 更新；部署前后 7 个环境变量文件 SHA-256 均为 EC66FCD6AB317825108A8D15BE2137A1E6793C60542924ED7B48ED28094EC5E9，临时快照已删除；HTTP 网关 health 为 200，CORS 仍精确允许 https://summertxia0306-hue.github.io；P5/formal-and-test 与隐藏课程 formal 拦截均正常
资源复核：family24 为 family24-web-003/SUCCESS/11-11；体验版有效至 2027-02-04，超额付费关闭，部署前剩余 2927.83 点；原 CloudBase 英语正式入口与家庭 24 点均 HTTP 200
发布证据：设计扩展 85834de；实施计划 26a7e65；实现 39a96a6；Pages 7280052；GitHub Actions run 33465649825 success；线上活动 bundle index-aq5Lbf_5.js，包含 400KiB/700KB 档位标记
数据边界：发布验证未登录家长端、未运行探针、未创建 test/formal 结果、speaking take、录音或完成状态；云端 sherlock-english/test/direct-upload-probe/ 当前为 0 个对象；未修改夏洛恪英语学习档案
Android 无 VPN 真机补测：400KiB 返回 409600 字节，PUT 555ms、服务端核验与删除 1365ms、总计 2501ms；700KB 返回 700000 字节，PUT 472ms、服务端核验与删除 1139ms、总计 2351ms；两档页面均显示“对象已清理”
云端复核：两档测试完成后 sherlock-english/test/direct-upload-probe/ 再次查询为 0 个对象；连同此前 150KiB 结果，Android 无 VPN 三档均通过，且本轮未进入学习档案
当前结论：Android 侧已证明当前口语 WAV 上限 700000 字节可绕过 HTTP 网关直接上传私有 COS；该结论只覆盖传输、核验与清理，不代表完整讯飞评分反馈能达到 2.4 至 2.5 秒
iOS 真机验收：家长确认 700KB 档通过；返回 700000 字节，PUT 2337ms、服务端核验与删除 1348ms、总计 4229ms，页面显示“对象已清理”
最终云端复核：iOS 测试完成后 sherlock-english/test/direct-upload-probe/ 为 0 个对象；未生成学习结果、口语 take 或学习档案记录
最终结论：Android 无 VPN 三档与 iOS 700KB 上限档均通过，跨 Android/iOS 的私有 COS 直传传输层可行性验收完成；是否替换正式分块方案仍须另立设计并保留回滚链路
```
