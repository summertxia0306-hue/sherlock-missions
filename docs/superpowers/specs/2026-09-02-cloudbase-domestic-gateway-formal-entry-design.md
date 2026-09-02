# 腾讯云国内网关唯一 formal 入口设计

> 日期：2026-09-02
> 状态：家长已批准完整设计，待书面规格复核后实施
> 唯一项目根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`

## 1. 背景与结论

GitHub Pages 入口已在安卓关闭 VPN 后完成页面、录音提交和评分验证，但一台从未安装 VPN 的主用 iPad 在微信与 Safari 中无法打开 GitHub Pages。该 iPad 随后直接访问腾讯云上海 HTTP 网关，能够收到预期的“请求不被允许”JSON，证明设备、Wi-Fi 与 Safari 可以直连现有腾讯云网关。

因此此前“GitHub Pages 作为唯一儿童 formal 入口”的真机验收结论失效。家长已批准方案 A：复用现有 `sherlock-api` HTTP 网关提供国内 PWA，腾讯云国内入口成为唯一儿童 formal 入口；GitHub Pages降级为备用和家长 test，不再允许 formal。

国内正式地址规划为：

`https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api/`

## 2. 目标与非目标

### 目标

1. 让从未安装 VPN 的主用 iPad 通过腾讯云国内线路稳定打开、安装和使用 PWA。
2. 彻底绕过 CloudBase 静态托管首页的 `Content-Disposition: attachment` 行为。
3. 保持现有数据库、正式结果、私有录音、讯飞评分和课程内容不迁移。
4. 让后端只接受国内 HTTP 网关创建和继续儿童 formal 会话。
5. 保留 GitHub Pages 作为家长 test 与紧急回滚候选，但禁止其产生 formal。
6. 不新增域名、ICP 备案、付费环境或云函数。

### 非目标

- 不修改 `W01D50`、`S01D50` 的课程内容；
- 不重新开放教材已失效的 `L/S4A-T1-W01-D01–D06`；
- 不切换 formal 口语到云存储直传；
- 不迁移或删除成绩、录音、错题、订正、学习档案、源课程或 Git 历史；
- 不借本次入口修复升级 CloudBase SDK 或进行无关重构；
- 不购买自定义域名、套餐或其他资源。

## 3. 入口架构

### 3.1 同一网关分离 GET 与 POST

复用现有 `sherlock-api` HTTP 路由：

- `GET/HEAD /sherlock-api/…`：只提供国内版 PWA 静态程序；
- `POST /sherlock-api`：继续处理现有业务 API；
- `OPTIONS /sherlock-api`：继续处理受控 CORS 预检。

静态响应和业务请求在代码中使用独立处理器。GET 处理器不得调用数据库、评分函数、云存储写入或学习结果逻辑；POST 处理器不得从浏览器参数读取静态文件路径。

### 3.2 绕过附件下载层

CloudBase 静态托管默认域名继续返回 `Content-Disposition: attachment`，所以不得再承担顶层 HTML 导航。国内首页、JS、CSS、课程 JSON、图标、Manifest 和 Service Worker 全部由云函数网关返回：

- HTML：`Content-Type: text/html; charset=utf-8`；
- JavaScript/Service Worker：正确的 JavaScript MIME；
- CSS、JSON、SVG、Web Manifest：按扩展名返回正确 MIME；
- 所有顶层页面响应不得包含 `Content-Disposition: attachment`。

网关已经实测不会自行附加附件下载响应头。正式切换前仍必须在线复核最终 HTML、Service Worker 和 JS 的真实响应头；任何一项出现附件标记即判失败，不切换 formal。

### 3.3 轻量函数包与音频 CDN

当前生产构建约 12.18MB、351 个文件；排除音频后只剩约 0.51MB、39 个文件。因此：

- 云函数包只携带非音频 PWA 产物；
- 课程音频继续放在现有 CloudBase 静态 CDN `/sherlock-english/audio/…`；
- 网关收到 `/sherlock-api/audio/…` 时，只允许匹配发布清单内的规范音频路径，并重定向到腾讯云静态 CDN；
- 音频仍由浏览器播放器作为子资源加载，保留 Range、播放与 PWA 运行时缓存；静态托管不再承担顶层导航。

这样不会让约 11.7MB 音频流量经过云函数，也不会把评分 API 与大文件下载绑定。

### 3.4 PWA 路径与缓存

国内构建的 `base`、`start_url`、`scope` 和导航回退统一为 `/sherlock-api/`。Service Worker 只能控制该路径：

- HTML 与 Service Worker：`no-store` 或强制重新验证；
- 带内容哈希的 JS/CSS：长期不可变缓存；
- 课程 JSON：重新验证，避免发布后继续读取陈旧课程；
- 音频：沿用现有 CacheFirst 与容量/有效期限制；
- 离线时已缓存页面可打开，但提交必须明确提示恢复网络。

## 4. formal、test 与可信通道

### 4.1 服务端通道

后端生成、且不采信浏览器同名参数的通道标识扩展为：

- 腾讯云国内页面：`domestic-http`；
- GitHub Pages：`github-http`；
- 旧 Web SDK/Event：`cloudbase-event`。

HTTP Origin 必须与固定允许清单精确匹配。腾讯云国内 Origin 只允许当前 `ap-shanghai.app.tcloudbase.com` 主机；GitHub 只允许当前 Pages Origin。不得使用任意后缀、反射 Origin 或客户端自报通道。

### 4.2 唯一 formal 门

新增并切换到 `FORMAL_ENTRY_MODE=domestic-http-only`：

1. 只有 `domestic-http` 可以创建 formal 儿童会话；
2. formal 的进度、听力提交/订正、口语分块上传/评分/最终提交继续校验会话的 `entry_channel`；
3. 切换前由 GitHub 创建但未完成的 formal 会话不能继续写入，必须从国内入口重新进入；
4. `github-http` 只保留家长认证后的 test；
5. `cloudbase-event` 继续禁止 formal；
6. test 会话不能通过 Origin、客户端字段或旧 token 转成 formal。

GitHub Pages 普通儿童入口应显示国内正式入口提示，但服务端硬门才是最终保证。

### 4.3 现有数据和口语链路

- 正式成绩、历史完成进度、录音和家长数据继续使用现有集合与云存储；
- formal 口语继续使用已验收的 HTTP 分块上传与回退链路；
- 云存储直传继续只允许家长 test；
- 切换和自动验收不得生成虚假 formal 学习结果；
- `W01D50`、`S01D50` 及撤回课程的公开与服务端课程门保持不变。

## 5. 静态文件安全与错误处理

GET 处理器采用构建时生成的发布清单，只允许返回清单内文件：

- URL 必须规范化并限制在 `/sherlock-api/`；
- 拒绝 `..`、编码后路径穿越、反斜杠、空字节和清单外文件；
- 不允许读取函数源码、`.env`、依赖、`private/`、学习档案或任意绝对路径；
- 未知的无扩展名前端路由回退到 `index.html`；
- 未知的带扩展名资源返回 404，不得回退 HTML；
- `HEAD` 与 `GET` 使用相同状态和响应头，但不返回正文；
- POST/OPTIONS 的现有大小、Origin、Content-Type 和客户端 ID 校验保持有效。

前端无法加载关键程序时显示可重试错误；API、音频或评分短暂失败时沿用现有重试与“网络恢复后提交”提示，不生成重复结果。

## 6. 发布顺序

1. 记录 GitHub、国内网关、CloudBase 静态站、API 健康、课程目录和正式数据只读基线。
2. 实现国内构建、GET/HEAD 静态处理、音频重定向、通道识别和 `domestic-http-only` 模式测试。
3. 在 `FORMAL_ENTRY_MODE=github-http-only` 不变的情况下部署新代码和国内候选页面。
4. 自动验证响应头、路由、PWA、课程、音频、API、formal/test 隔离和全部现有测试。
5. 只进行一次必要的 iPad 真机候选验收：打开国内首页、完成一条家长 TEST 口语并收到评分；不要求完成整课。
6. 真机通过后，将 `FORMAL_ENTRY_MODE` 切为 `domestic-http-only`。
7. GitHub 普通入口改为国内入口提示并保留家长 test；旧 CloudBase 静态迁移页改指向国内入口。
8. 完成线上 formal 通道、旧通道拒绝、课程边界和数据无损复核，登记提交、URL 与回滚点。

## 7. 验证门

### 自动验证

- GET/HEAD 正确返回首页、哈希资源、课程 JSON、Manifest、Service Worker 和 SPA 路由；
- HTML、JS 和 Service Worker 无 `Content-Disposition: attachment`，MIME 正确；
- 路径穿越、编码穿越、清单外扩展资源和源码访问均被拒绝；
- 音频只重定向到固定腾讯云 CDN 前缀，目标路径经过清单或严格规范校验；
- 国内 HTTP formal 被允许，GitHub HTTP formal 与旧 Event formal 被拒绝；
- GitHub 家长 test 仍可用，test/formal 不串写；
- formal 口语仍走分块链路，TEST 直传边界不变；
- Web、`sherlock-api`、`score-speaking`、Python、tools、类型检查和生产构建全部通过；
- 构建产物与函数包不含私密文件、密钥、正式结果或私有录音；
- 自动验收不新增 formal 成绩。

### 在线与真机验证

- 无 VPN iPad 可以直接打开国内候选首页，不出现附件下载；
- iPad 家长 TEST 单条录音可以提交并收到评分；
- 切换后国内入口可以创建 formal 会话；
- GitHub 和旧 Event 创建/继续 formal 均返回入口拒绝；
- `W01D50`、`S01D50` 可见，撤回的 6 组课程不可见且不可写 formal；
- 旧迁移页指向国内入口，家庭 24 点应用及其他 family24 路径不变。

## 8. 回滚

切换前任何失败只停止发布，不改变 formal 模式。切换后若复核失败：

1. 保留全部现有环境变量，仅将 `FORMAL_ENTRY_MODE` 恢复为 `github-http-only`；
2. GitHub Pages 恢复为临时 formal 回滚入口；
3. 恢复上一版 `sherlock-api`，但不删除新函数包、会话、审计或任何学习数据；
4. 对切换窗口内记录只做对账，不删除、不改写；
5. CloudBase 静态首页仍不得作为正式 PWA 回滚入口，因为附件下载问题已被实测确认。

## 9. 完成定义

同时满足以下条件才宣布国内入口完成：

- 无 VPN iPad 真机能够打开国内 PWA 并完成单条 TEST 录音评分；
- 国内网关是服务端唯一认可的 formal 前端通道；
- GitHub Pages仅保留家长 test/备用，不可写 formal；
- 顶层 HTML、JS 和 PWA 文件不经过带附件响应头的静态托管导航；
- 音频继续走腾讯云 CDN，评分和正式数据链路保持原状；
- 全套自动验证和线上边界验证通过；
- 既有成绩、录音、课程、档案和 Git 历史没有删除或改写；
- 项目状态、已确认决策、正式 URL、部署提交和回滚点完成登记。

这个判断最可能错在哪：虽然 iPad 已证明能直连腾讯云网关，但最终 HTML、Service Worker、麦克风权限和跨路径音频重定向尚未在真实国内构建上联合验证，因此必须坚持“候选先上线、单条 TEST 真机通过后才切 formal”的顺序。
