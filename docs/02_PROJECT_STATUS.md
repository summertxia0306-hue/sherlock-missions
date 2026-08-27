# PROJECT STATUS

> 最后更新：2026-08-27
> 当前阶段：P5 正式切换已上线；iOS 录音热修复已通过真机验收，等待一对正式课程即时对账和 24 小时复核

## 当前事实

- 新根目录已经接入原仓库完整 Git 对象库和工作树，是当前唯一活跃开发根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`。
- 旧源仓库仍在：`D:\project_antigravity\education_english\听力部分\sherlock-missions`，迁移前后均保持干净，当前只作只读参考。
- 当前仓库分支：`main`。
- P2 Git 基线：`954c02400a69ad7aed22574baa742500dfc15d1a`；P3 独立提交由本记录所在的 `main` 提交承载并推送。
- 当前远端：`https://github.com/summertxia0306-hue/sherlock-missions.git`。
- 原仓库 770 个跟踪文件均已迁入；根 README 同名冲突以治理 README 为主，旧 README 原样归档到 `docs/legacy-streamlit/README_streamlit_legacy.md`。
- 当前公开课程：听力和口语各 12 个 JSON，共 24 个；成品 MP3 312 个，fragments MP3 380 个。
- 当前唯一正式入口已切换为 CloudBase；Streamlit 真实浏览器渲染确认仅保留只读迁移提示，不再接受课程、家长测试或学习记录提交。
- CloudBase `family24` 在 P5 切换前后实时核验仍为体验版，到期 `2027-02-04 23:59:59`，超额付费关闭；当前周期 `2026-08-04` 至 `2026-09-04`，切换部署前 3000 点中已用 27.13 点、剩余 2972.87 点。
- P1 已创建隔离资源：Event 云函数 `sherlock-api`、4 个 `ADMINONLY` 的 `sherlock_*` 集合、`sherlock-english/test/README.txt` 存储标记和前端 `publish_key`；匿名登录仅对 `sherlock-api` 放行，其他函数保留原匿名禁用规则。
- `sherlock-api` 已配置家长密码 scrypt 哈希、会话 HMAC 和口语内部 HMAC；P3 私有 `score-speaking` 继续使用。P5 保留全部既有密钥并仅新增 `FORMAL_ENABLED=true`；在线健康检查返回 `stage=P5`、`formal_enabled=true` 和 `writes=formal-and-test`。正式站点为 `https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/`。
- P2 已上线 W01D39–W01D50 共 12 门听力课；儿童副本 12/12 无答案、原文、考点标签或家长备注；216/216 段线上 MP3 与本地发布文件 SHA-256 一致。
- P3 已完成 React 口语页面、单实例 iPad PCM/WAV 录音、试录/回放/自动停止、示范音互斥、讯飞评分适配、3 星/三次门控、加密 proof、幂等评分、私有录音和家长临时回放实现，并已部署 test。
- 2026-08-27 两台 iOS 正式体验确认 PWA 跨录次复用麦克风流会导致首录间歇性静音、录完后系统麦克风指示灯跨题常亮，且显式关闭自动增益后回听偏小；Android 与旧 Streamlit 不复现。PWA 已改为每次录音获取新流并在成功、静音、异常和离页时立即停轨，恢复浏览器自动增益/降噪/回声消除；同时恢复课程卡“推荐”、完成置灰并扩大按钮触控留白。发布后真实 iOS 复验确认首录、回听音量、麦克风指示灯释放及 UI 微调均已修复。
- P3 本地验证：Web 51/51、`sherlock-api` 31/31、`score-speaking` 11/11、旧版 Python 40/40；覆盖率门、TypeScript 构建和 PWA 构建均通过。口语页面定向用例已实际点击“就用这个，开始评分”并进入评分结果态。
- 讯飞 ISE 于 2026-08-24 实时核验：当日用量 0、剩余服务量 10500、到期 `2026-09-10 12:33`；用户确认不购买、不自动付费，到期后先核验每日免费额度。
- P1 真实验收结果 `58d7621e-0fd7-4abb-aaf8-a6ab65e9a5fd` 已落入 `sherlock_results`，云端核对为 `data_kind=test`、`formal_completion_eligible=false`；未认证写入返回 `UNAUTHORIZED`，formal 动作返回 `FORMAL_DISABLED`。
- 发布后 24 点仍为 `family24-web-003` / `SUCCESS`；公开首页 HTTP 200，11/11 个当前静态文件与 `D:\project_antigravity\24\dist` 的大小和 MD5 精确匹配。
- `_runtime`、本机代理配置、`__pycache__` 和私有结果库数据均未迁入；旧位置未删除或改写。
- 原拟目录 `English-Listen-Speak` 为空，本轮未删除。

## 已完成

- 开学后教学方向确认；
- CloudBase 方案 C 确认；
- 费用和免费额度初步评估；
- 项目迁移和归档策略确认；
- Codex 窗口架构确认；
- 未来单词模块衔接原则确认；
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

完成 W01D46 与 S01D46 两门新的正式课程；完成后立即核对 formal 结果、录音与推荐进度，24 小时后再次复核持久化。P0、P4 与 P5 的临时克隆、迁移前备份和原始快照继续保留到 P5 完整验收通过。

当前阶段指令：`docs/阶段计划/P5_上线切换与验收.md`。

## 当前阻塞

无开发阻塞；线上切换和 iOS 录音热修复已完成并通过真实 iOS 复验，formal 即时对账与 24 小时复核尚未完成。

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
