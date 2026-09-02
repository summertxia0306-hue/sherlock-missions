# GitHub Pages 正式入口切换与 W01D50 / S01D50 发布设计

> 日期：2026-09-01
> 状态：已实施并完成线上自动验收（2026-09-02）
> 唯一项目根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`

## 1. 已确认决策

- GitHub Pages `/sherlock-english/` 从候选入口切换为唯一日常 formal 前端入口。
- 本次只新增开放听力 `W01D50` 与口语 `S01D50`。
- `W01D39–49`、`S01D39–49` 仅作为既有历史课程与重做入口保留，不删除正式结果、录音或 Git 历史，也不把它们重新定义为本次新课。
- 因教材发生变更，`L4A-T1-W01-D01–D06` 与 `S4A-T1-W01-D01–D06` 不进入公开 Pages 版本，不得成为 formal 可选课或推荐课；其本地源文件和历史保留，等待 01 窗口按新教材重制。
- CloudBase 后端、数据库、正式结果、私有录音和讯飞评分服务不迁移。
- 正式口语继续使用已经验收的分块上传与回退链路；云存储直传只保留在家长 TEST 隔离路径，不用于 formal。

## 2. 目标与非目标

### 目标

1. 让孩子从 GitHub Pages 唯一入口看到并完成 `W01D50` 与 `S01D50`。
2. 从公开构建、课程目录、推荐逻辑和服务端 formal 校验四层排除教材已失效的 6 组课程。
3. 阻止旧 CloudBase 页面或旧缓存 PWA 在切换后继续创建、推进或提交 formal 会话。
4. 保持 test/formal 数据隔离，且不因入口切换修改既有正式学习记录。
5. 保留可恢复到旧入口的回滚路径。

### 非目标

- 不重写课程内容；
- 不删除 `W/S01D39–49`、失效课程源文件、已有成绩、录音或 Git 历史；
- 不把 TEST 结果写入学习档案；
- 不在本次启用 formal 云存储直传；
- 不重新上线此前已制作但教材不匹配的 6 组课程；
- 不改家庭 24 点 GitHub Pages 根站。

## 3. 入口与 formal 写入架构

仅替换旧 CloudBase 静态页面不够：已安装在 iPad 上的旧 PWA 可能继续从缓存运行。因此唯一正式入口必须由后端强制执行，而不能只依赖页面提示。

### 3.1 请求通道标识

`sherlock-api` 为每个请求建立服务端可信的通道标识：

- CloudBase Event / Web SDK：`cloudbase-event`；
- GitHub Pages HTTP 网关：`github-http`。

该标识由云函数入口生成，不采信浏览器提交的同名字段。

### 3.2 formal 会话硬门

新增可回滚部署配置 `FORMAL_ENTRY_MODE`：

- 切换前：保持当前兼容模式；
- 切换后：`github-http-only`。

在 `github-http-only` 下：

1. `startChildSession` 只接受 `github-http`，并将 `entry_channel` 写入会话；
2. formal 的进度读取、听力提交/订正、口语分块上传/评分/最终提交均校验会话的 `entry_channel`；
3. 切换前由旧入口创建但尚未完成的会话不再允许继续写入，用户必须从新入口重新开始；
4. test 会话继续按现有 test 规则处理，不能借由客户端参数变成 formal。

这样即使旧 PWA 未及时刷新，它也不能再写正式记录。

## 4. 课程发布规则

### 4.1 公开构建

Pages 构建采用明确发布清单，而不是把所有源课程无条件复制到 `web/public`：

- 包含现有历史课程 `W/S01D39–49`；
- 包含本次正式新课 `W01D50`、`S01D50`；
- 排除 `L4A-T1-W01-D01–D06`、`S4A-T1-W01-D01–D06` 的 JSON、音频、目录项与 manifest 项；
- 任何不在清单内的新课程默认不公开。

同步/构建工具应支持发布 profile 或 allowlist；不得通过移动或删除源文件实现过滤。

### 4.2 服务端课程门

- 失效的 6 组课程即使仍存在于函数侧历史副本，也必须保持非 formal 发布状态；
- 服务端创建 formal 会话时再次校验课程允许清单，避免用户通过手工 URL 或旧缓存绕过前端；
- 当前推荐的新任务上限为 `W01D50` / `S01D50`，不得自动推荐到教材未确认的后续编号。

## 5. 正式口语与 TEST 直传隔离

GitHub Pages 当前包含 TEST 云存储直传能力。切换 formal 前必须消除“所有口语评分都先尝试 TEST 直传”的可能：

- `SpeakingPage` 向客户端 API 层传递当前会话数据类型；
- 只有 `data_kind=test` 且服务端 test 会话校验通过时，客户端才可尝试云存储直传；
- `data_kind=formal` 始终走现有分块上传、评分与回退链路；
- 服务端以会话数据为权威，浏览器的 `data_kind` 只用于选择客户端传输方式，不能改变记录身份；
- direct 失败不得让 formal 转入 test，也不得生成重复评分记录。

## 6. 旧 CloudBase 前端处理

只替换 `/sherlock-english/` 子应用，不影响 CloudBase 根站及其他应用：

1. 部署最小迁移页，明确显示新的唯一入口并提供打开按钮；
2. 部署接管型 Service Worker，立即激活、接管页面并清理 Sherlock 旧缓存；
3. 不在迁移页保留课程、录音、评分或提交功能；
4. 后端 formal 会话硬门是最终安全保证，迁移页和缓存清理只负责用户体验。

## 7. 实施顺序

为缩短不可用窗口，按以下固定顺序执行：

1. 记录两套入口、CloudBase 配置、Pages 根站、课程目录和正式数据只读基线；
2. 实现并验证发布清单、formal/TEST 口语分流、服务端通道校验及旧入口迁移页；
3. 运行 Web、云函数、评分函数、Python 和针对性安全测试；
4. 先发布 formal-ready 的 GitHub Pages 构建，并验证但暂不宣布切换；
5. 部署 `sherlock-api` 通道硬门并把 `FORMAL_ENTRY_MODE` 切为 `github-http-only`；
6. 部署旧 CloudBase 迁移页与缓存清理 Service Worker；
7. 复核 Pages 为唯一可创建 formal 会话的前端，并登记状态与回滚版本。

本次部署验证不得代替孩子完成课程，也不得为了验收生成虚假的 formal 成绩。

## 8. 验证门

### 自动验证

- 现有 Web、`sherlock-api`、`score-speaking`、Python 测试全部通过；
- 新增测试覆盖：旧 Event 通道 formal 被拒、GitHub HTTP formal 被接受、旧会话不能续写、test/formal 不串写；
- formal 口语调用分块链路，TEST 才可进入 direct 链路；
- Pages 课程目录只出现允许课程，失效 6 组课程的公开 JSON/音频返回不存在；
- 服务端拒绝对失效 6 组课程创建 formal 会话；
- `W01D50`、`S01D50` 的 JSON、音频、题数、答案、录次与 manifest 完整；
- Pages `/sherlock-english/`、路由回退、主脚本、Manifest、Service Worker 和代表音频均正常；
- family24 Pages 根站文件与在线行为不变；
- 构建产物不含 `private/`、学习档案、密钥、正式结果或私有录音。

### 无正式作答的线上复核

- 新入口可登录儿童端并读取正式进度；
- `W01D50`、`S01D50` 是当前可进入的新任务；
- 那 6 组失效课程不可见、不可由 URL 创建 formal 会话；
- 旧 CloudBase 地址只显示迁移页；
- 旧 Event 通道的 formal 开始请求被服务端拒绝；
- test 探针不改变正式完成状态；
- 临时口语对象目录为空，既有正式结果和录音数量不减少。

孩子以后首次完成 `W01D50` / `S01D50` 才属于真实 formal 学习验收；本次上线不要求家长重复进行开发测试。

## 9. 回滚

若新入口、课程过滤或 formal 写入出现异常：

1. 先把 `FORMAL_ENTRY_MODE` 恢复到切换前模式，恢复旧入口创建 formal 的能力；
2. 恢复上一版 `sherlock-api` 与旧 CloudBase 静态构建；
3. Pages 新版本可回退到上一提交，但不得改动家庭 24 点根目录；
4. 对切换窗口内产生的会话和记录只做对账，不删除、不改写；
5. 不启用 Streamlit formal 作为临时替代。

## 10. 完成定义

同时满足以下条件才宣布方案 A 完成：

- GitHub Pages 是服务端认可的唯一 formal 前端通道；
- 旧 CloudBase 前端只提供迁移提示，旧缓存无法继续 formal 写入；
- 公开新课只有 `W01D50`、`S01D50`，失效 6 组课程已从公开版本和 formal 门中排除；
- 正式口语仍走分块上传，TEST 直传仍被隔离；
- 全套自动验证与线上只读/边界验证通过；
- 既有成绩、录音、学习档案、源课程和 Git 历史无删除；
- 项目状态、正式入口、发布提交和回滚点已登记。

这个判断最可能错在哪：旧 PWA 的历史请求形态可能不止当前识别出的 Event 通道；因此上线前必须用服务端测试证明所有 formal 写动作都经过统一通道门，而不能只测试 `startChildSession`。
