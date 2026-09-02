# 腾讯云国内网关唯一 formal 入口实施计划

> 日期：2026-09-02
> 对应设计：`docs/superpowers/specs/2026-09-02-cloudbase-domestic-gateway-formal-entry-design.md`
> 状态：规格已通过，待实施
> 唯一项目根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`

## 实施纪律

- 采用测试驱动：每项行为先形成失败测试，再做最小实现。
- 候选入口部署期间保持 `FORMAL_ENTRY_MODE=github-http-only`，不得提前切换儿童 formal。
- 自动验证不得创建 formal 学习结果；只允许创建会话、受控拒绝事件和家长 test。
- 不删除或覆盖用户当前未提交的 README、治理文档和教材录入文件。
- 不升级依赖、不新增域名、云函数、环境或付费资源。
- 主项目与 family24 其他应用、GitHub Pages 根站不得受影响。

## 任务 1：让 PWA 构建路径可配置

### 文件

- 修改：`web/vite.config.ts`
- 修改：`web/src/vite-env.d.ts`
- 新增或修改测试：`web/scripts/validate-cloudbase-build-env.node-test.mjs`
- 必要时修改：`web/scripts/validate-cloudbase-build-env.mjs`

### 行为

1. 增加受控构建变量，例如 `VITE_APP_BASE`。
2. 默认构建继续使用 `/sherlock-english/`，避免破坏 GitHub Pages 与历史流程。
3. 国内构建固定使用 `/sherlock-api/`。
4. `base`、PWA `start_url`、`scope`、`navigateFallback` 和音频缓存路径必须从同一规范化值生成。
5. 只允许 `/` 开头和 `/` 结尾的站内路径，拒绝完整 URL、`..`、反斜杠和空值漂移。

### 验证

- 构建配置测试覆盖默认路径、国内路径与非法路径。
- `npm run typecheck`
- 国内 profile 生产构建中，HTML、Manifest 和 Service Worker 均只引用 `/sherlock-api/`。

## 任务 2：生成最小国内函数静态包

### 文件

- 新增：`tools/prepare-domestic-gateway-release.mjs`
- 新增：`tools/prepare-domestic-gateway-release.test.mjs`
- 生成目录：`cloudfunctions/sherlock-api/public-app/`
- 修改：`.gitignore` 或发布清单规则，仅在确有需要时调整

### 行为

1. 从 `web/dist` 复制 HTML、哈希 JS/CSS、课程 JSON、图标、Manifest、Service Worker 与 Workbox 文件。
2. 明确排除 `audio/`、source map、测试文件、`private/`、环境文件和未知扩展名。
3. 生成不可由 URL 控制的静态文件 manifest，记录相对路径、MIME、字节数和内容哈希。
4. 失败时不留下半生成目录；使用同根临时目录完成后再替换目标目录。
5. 校验非音频包大小上限，当前基线约 0.51MB；异常膨胀时阻止部署。

### 验证

- 测试复制允许文件、排除音频、阻断私密文件和拒绝路径穿越。
- 产物清单与实际文件逐项哈希一致。
- 扫描产物不含密钥模式、学习档案、正式结果或私有录音。

## 任务 3：实现 GET/HEAD 国内静态处理器

### 文件

- 新增：`cloudfunctions/sherlock-api/static-app.js`
- 新增：`cloudfunctions/sherlock-api/test/static-app.test.js`
- 修改：`cloudfunctions/sherlock-api/index.js`

### 行为

1. HTTP `GET/HEAD` 在业务 API 解析前进入独立静态处理器。
2. `/sherlock-api/`、已知前端文件和课程 JSON从 manifest 读取。
3. 无扩展名的 SPA 路由返回 `index.html`；清单外带扩展名资源返回 404。
4. HTML、JS、CSS、JSON、SVG、Manifest、Service Worker 使用正确 MIME。
5. HTML/Service Worker 禁止陈旧缓存；哈希资源使用 immutable；课程 JSON 重新验证。
6. `HEAD` 返回与 GET 相同的状态和响应头，但正文为空。
7. `/sherlock-api/audio/listening|speaking/…` 仅在路径严格匹配发布规则时 302/307 到固定 CloudBase CDN 前缀。
8. 拒绝 `..`、百分号编码穿越、反斜杠、空字节、绝对路径、源码和清单外文件。

### 验证

- 测试所有 MIME、缓存头、GET/HEAD、SPA fallback、404 和音频跳转。
- 测试多种原始与编码路径穿越均无法读取函数源码或任意文件。
- HTML、JS、Service Worker 响应明确不含 `Content-Disposition: attachment`。

## 任务 4：扩展可信 Origin 与 formal 通道硬门

### 文件

- 修改：`cloudfunctions/sherlock-api/http-adapter.js`
- 修改：`cloudfunctions/sherlock-api/core.js`
- 修改：`cloudfunctions/sherlock-api/index.js`
- 修改：`cloudfunctions/sherlock-api/.env.example`
- 修改测试：
  - `cloudfunctions/sherlock-api/test/http-adapter.test.js`
  - `cloudfunctions/sherlock-api/test/core.test.js`
  - 其他受影响测试

### 行为

1. 精确允许两个 HTTP Origin：腾讯云国内网关与当前 GitHub Pages。
2. 国内 Origin 在服务端标记为 `domestic-http`；GitHub 标记为 `github-http`。
3. 新增 `domestic-http-only` 模式，同时保留已有模式用于部署与回滚。
4. `domestic-http-only` 下只有国内通道可以创建和继续 formal。
5. GitHub 家长认证 test、直传 test 和历史 test 查询继续工作。
6. 旧 Event 与 GitHub 的现有/新 formal token 均不得续写。
7. CORS 只向请求中命中的固定 Origin 返回，不反射未知 Origin。

### 验证

- 国内 formal 全动作允许；GitHub formal 和 Event formal 全动作拒绝。
- GitHub 与国内家长 test 均保持 test，不得升级 formal。
- 未知 Origin、缺失 Origin、伪造通道字段和错误客户端 ID 被拒绝。
- health 返回新的 `formal_entry_mode`。

## 任务 5：调整 GitHub 与国内入口体验

### 文件

- 修改：`web/src/core/cloudbase-api.ts`
- 修改：`web/src/core/cloudbase-api.test.ts`
- 修改：相关首页/错误提示组件及测试
- 修改：`cloud-resources/formal-cutover-shell/index.html`
- 修改：`cloud-resources/formal-cutover-shell/sw.js`

### 行为

1. 国内构建使用同源腾讯云 API URL。
2. 当 GitHub 普通儿童入口收到 `FORMAL_ENTRY_REQUIRED` 时，显示国内正式入口按钮，不进入课程。
3. GitHub 家长登录与 test 不受影响。
4. 旧 CloudBase 静态迁移页改指向国内 URL，缓存清理仍只作用于 `/sherlock-english/`。
5. formal 口语仍固定分块；本任务不得启用 formal 直传。

### 验证

- UI 测试证明 GitHub 儿童 formal 被引导、家长 test 可用。
- 国内入口不会显示错误迁移提示。
- 旧迁移 Service Worker 不删除其他 family24 缓存。

## 任务 6：构建可回滚候选部署工具

### 文件

- 新增：`tools/deploy-domestic-gateway-candidate.ps1`
- 新增或修改脚本测试：`tools/` 对应测试
- 修改：`tools/switch-formal-entry-to-pages.ps1`，重构为通用安全切换或新增独立国内切换脚本

### 行为

1. 固定项目根、环境 ID、国内 URL、GitHub URL 和 CloudBase 静态音频前缀。
2. 部署前拉取并完整保留全部云函数环境变量，绝不输出密钥值。
3. 候选部署只更新函数代码和国内静态包，保持 `github-http-only`。
4. 自动验证国内 GET 页面可达，但 formal 被阻止；GitHub 原 formal 回滚通道继续可用。
5. formal 切换脚本只改 `FORMAL_ENTRY_MODE=domestic-http-only`，验证失败自动恢复原环境。
6. 所有临时文件限定在项目根并在结束后清理。

### 验证

- PowerShell 语法解析通过。
- 脚本的路径门、环境变量保留、失败回滚和安全输出有自动测试或可审计断言。

## 任务 7：全量本地验证与候选发布

### 固定验证

1. Web 全量测试与覆盖率。
2. `sherlock-api` 全量测试与覆盖率。
3. `score-speaking` 全量测试与覆盖率。
4. Python 全仓测试。
5. tools 全量测试。
6. TypeScript 类型检查和国内 profile 生产构建。
7. 敏感信息、私密路径、结果数据和录音扫描。
8. `git diff --check` 与只提交本任务文件的状态核对。

### 候选线上验证

- 国内首页、JS、Service Worker、Manifest、课程 JSON 返回 200 且 MIME 正确。
- 顶层程序响应无附件下载头。
- 音频跳转到固定腾讯云 CDN并支持播放/Range。
- 国内候选在切换前不能写 formal。
- GitHub、原 API、家庭 24 点根站和现有结果/录音只读基线不变。

## 任务 8：唯一一次 iPad 候选验收

候选自动验证全部通过后，向家长提供国内候选 URL。只要求：

1. 无 VPN iPad Safari 打开真实 PWA 首页，不出现下载；
2. 家长 test 入口录制一条口语并收到评分。

不要求孩子完成整门听力或口语，不写 formal，不重复进行多轮真机测试。若失败，保留 GitHub formal 模式并修复候选；不得带病切换。

## 任务 9：formal 切换与线上终验

仅在家长确认任务 8 通过后执行：

1. 切换 `FORMAL_ENTRY_MODE=domestic-http-only`。
2. 验证国内新/旧会话规则、GitHub formal 拒绝、Event formal 拒绝。
3. 验证 GitHub 家长 test 仍可认证和查询。
4. 部署 GitHub 儿童入口提示与旧 CloudBase 迁移页。
5. 复核 `W01D50`、`S01D50`、撤回课程边界、音频和评分链路。
6. 确认没有自动验收产生的 formal 结果，既有结果/录音数量不减少。

## 任务 10：治理登记与提交

### 文件

- 更新：`docs/01_已确认决策.md`，新增国内唯一 formal 决策，不删除旧决策
- 更新：`docs/02_PROJECT_STATUS.md`
- 更新：对应设计与本计划状态
- 新增：`docs/部署记录/2026-09-02_腾讯云国内网关正式入口.md`
- 必要时更新：README 与 P6 阶段状态中已过时的入口说明

### 登记内容

- 正式 URL、Git 提交、CloudBase 环境与函数版本；
- iPad 无 VPN 候选验收结果；
- 响应头、课程、formal/test、录音和评分验证结果；
- 回滚模式与上一入口提交；
- 未解决的依赖审计风险；
- 明确本次 test 不进入学习档案。

## 完成定义

- 规格中的自动、在线与 iPad 验收门全部通过；
- 国内腾讯云网关是唯一可写 formal 的儿童入口；
- GitHub Pages和旧 Event 不可写 formal，但家长 test 保留；
- iPad 首页无附件下载，单条 TEST 录音评分成功；
- 现有学习数据、课程、录音和其他 family24 应用无损；
- 文档、提交、正式 URL 和回滚点全部登记。
