# PROJECT STATUS

> 最后更新：2026-08-24  
> 当前阶段：P2 听力模块真实 iPad 验收通过；停留在 P2，不自动进入 P3

## 当前事实

- 新根目录已经接入原仓库完整 Git 对象库和工作树，是当前唯一活跃开发根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`。
- 旧源仓库仍在：`D:\project_antigravity\education_english\听力部分\sherlock-missions`，迁移前后均保持干净，当前只作只读参考。
- 当前仓库分支：`main`。
- 当前 Git 基线：`2e7370fc813531702b6388f90ceb3b19188f468f`；P1 独立提交已推送，`main` 与 `origin/main` 一致。P2 已验收并获用户授权形成独立提交推送 `main`，本记录由该 P2 提交承载。
- 当前远端：`https://github.com/summertxia0306-hue/sherlock-missions.git`。
- 原仓库 770 个跟踪文件均已迁入；根 README 同名冲突以治理 README 为主，旧 README 原样归档到 `docs/legacy-streamlit/README_streamlit_legacy.md`。
- 当前公开课程：听力和口语各 12 个 JSON，共 24 个；成品 MP3 312 个，fragments MP3 380 个。
- 当前线上正式入口仍是 Streamlit；2026-08-24 已从休眠页成功唤醒到任务首页，未执行课程提交或正式学习写入。
- CloudBase `family24` 在 P2 验收后实时核验仍为体验版，到期 `2027-02-04 23:59:59`，超额付费关闭；当前周期 `2026-08-04` 至 `2026-09-04`，3000 点中已用 1.68 点、剩余 2998.32 点。
- P1 已创建隔离资源：Event 云函数 `sherlock-api`、4 个 `ADMINONLY` 的 `sherlock_*` 集合、`sherlock-english/test/README.txt` 存储标记和前端 `publish_key`；匿名登录仅对 `sherlock-api` 放行，其他函数保留原匿名禁用规则。
- `sherlock-api` 已配置家长密码 scrypt 哈希和会话 HMAC 环境变量；P2 使用代码更新保留这些环境变量。在线健康检查返回 `stage=P2`、`formal_enabled=false` 和 `writes=test-only`。静态 test 站点已发布到 `https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/`。
- P2 已上线 W01D39–W01D50 共 12 门听力课；儿童副本 12/12 无答案、原文、考点标签或家长备注；216/216 段线上 MP3 与本地发布文件 SHA-256 一致。
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

## 下一步

P2 已验收通过，并获用户授权形成独立提交推送 `main`；推送后须确认新根目录工作区干净。是否进入 P3 仍须用户另行明确授权，当前不进入。同级临时克隆和迁移前治理快照继续保留到 P5。

当前阶段指令：`docs/阶段计划/P2_听力模块迁移.md`（验收通过）。

## 当前阻塞

无 P2 验收或提交阻塞。P2 已获提交和推送授权；P3 尚未获授权进入。

## 尚未实时确认但不阻塞

- 讯飞当前应用免费授权的精确到期日和剩余额度。
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
