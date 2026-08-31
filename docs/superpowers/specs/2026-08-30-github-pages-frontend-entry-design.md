# GitHub Pages 前端入口切换设计

> 日期：2026-08-30  
> 状态：家长已批准方案 A；阶段一候选部署及无 VPN iPad 家长 test 全流程验收通过；阶段二尚未批准
> 唯一项目根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`

## 1. 背景与已确认根因

现有 React/Vite PWA、CloudBase 云函数、数据库、正式结果和私有录音均正常保留。当前阻塞发生在 CloudBase 默认域名接收 Safari 顶层导航时：平台在业务代码运行前返回访问提示页，并可能把 `index.html` 作为附件处理。

已分别验证以下两类入口均受影响：

- 静态托管默认域名：`*.tcloudbaseapp.com`；
- CloudBase Web 应用域名：`*.webapps.tcloudbase.com`。

因此，继续修改 React、Service Worker、会话代码或创建新的 CloudBase Web 应用不能消除根因。

## 2. 目标与非目标

### 目标

- 为 iPad 提供不经过 CloudBase 默认域名提示页的稳定 HTTPS PWA 入口；
- 保留现有 CloudBase 云函数、数据库、正式成绩和私有录音；
- 不购买域名、不申请 ICP 备案、不新增付费资源；
- 不影响现有家庭 24 点 GitHub Pages 根站；
- 保持 formal/test、课程、推荐、录音和家长端现有业务规则不变；
- 保留可执行的 CloudBase 回滚路径。

### 非目标

- 不重写前端或后端；
- 不迁移、复制或重建正式学习数据；
- 不改变课程内容、编号、可见性或推荐顺序；
- 不修改科大讯飞评分链；
- 不把 `private/`、家长密码、管理密钥或私有录音发布到 GitHub Pages；
- 不在本阶段购买域名、升级 CloudBase 套餐或恢复 Streamlit formal。

## 3. 选定架构

正式候选入口为：

`https://summertxia0306-hue.github.io/sherlock-english/`

该账号现有 GitHub Pages 根站已经托管家庭 24 点。本项目只占用 `/sherlock-english/` 子路径，不改变根目录现有文件。

```text
iPad Safari / 主屏幕 PWA
        |
        | HTTPS 静态内容
        v
summertxia0306-hue.github.io/sherlock-english/
├─ React/Vite 应用壳
├─ Service Worker 与 Manifest
├─ 儿童安全课程 JSON
└─ 公开示范音频
        |
        | HTTPS JSON / CloudBase HTTP 网关
        v
现有 family24 CloudBase 环境
├─ sherlock-api
├─ score-speaking
├─ sherlock_* 数据集合
├─ 私有录音存储
└─ 科大讯飞 ISE
```

当前 Vite `base`、Manifest `start_url`、PWA `scope` 和导航回退均已使用 `/sherlock-english/`，与候选地址路径一致。实施时只允许为可重复发布做最小配置调整，不改变应用页面或业务行为。

## 4. 发布边界

### GitHub Pages 发布内容

只发布 `web` 的生产构建产物，包括：

- HTML、JavaScript、CSS、Manifest、Service Worker 和图标；
- `web/public` 中已经过儿童安全同步的课程副本；
- 公开听力和示范音频及对应 manifest。

发布前必须执行敏感信息扫描，并证明构建产物不包含：

- `private/` 下任何文件；
- 家长密码或密码哈希；
- CloudBase 管理密钥；
- 科大讯飞 APISecret/APIKey；
- 正式结果、错题、学习档案或私有录音。

GitHub Pages 候选构建不注入 CloudBase Publishable Key；客户端只包含公开的 HTTPS 网关地址。原 CloudBase 前端继续沿用现有 Web SDK 配置，任何 Publishable Key 仍不得输出到日志、Markdown 或新增提交历史。

### CloudBase 保留内容

以下资源不迁移：

- 两支现有云函数；
- `sherlock_*` 数据集合；
- formal/test 结果；
- 私有录音和临时访问地址；
- 讯飞配置与函数环境变量。

实施时 CloudBase 体验版拒绝新增 GitHub Pages Web 安全域名，因此阶段一改为创建同一环境的 HTTP 网关路由，由 `sherlock-api` 对唯一 GitHub Pages Origin 执行精确 CORS。不得扩大数据库、存储或其他云函数权限。

## 5. 两阶段切换

### 阶段一：候选入口部署与家长 test 验收

1. 记录家庭 24 点 Pages 根站的文件清单、哈希和在线基线。
2. 构建 Sherlock PWA，并只写入 Pages 仓库的 `sherlock-english/` 子目录。
3. 通过同一 CloudBase 环境的 `/sherlock-api` HTTP 网关连接现有云函数，并只允许 `https://summertxia0306-hue.github.io` Origin。
4. 验证候选入口、路由、静态资源、音频和只读 API。
5. 由家长在 iPad Safari 使用家长 test 入口完成播放、录音、回放、评分和提交验收。

阶段一期间，孩子不得从候选入口进行普通 formal 学习。现有 CloudBase 地址继续是唯一 formal 入口。

### 阶段二：正式入口切换

只有阶段一真机 test 验收通过并得到家长明确确认后，才执行：

1. 将 GitHub Pages 地址宣布为唯一 formal 入口；
2. 将 CloudBase 原 `/sherlock-english/` 页面更新为只读迁移提示，指向新入口；
3. 更新旧 Service Worker，使已安装旧 PWA 获取迁移提示，避免继续从旧入口开始课程；
4. 不关闭 CloudBase 后端 formal 写入，因为新入口仍使用同一服务端；
5. 完成一对真实 formal 听力/口语课程并立即对账，随后执行 24 小时复核。

阶段二不会产生两套数据库或两套 formal 规则；只有静态前端承载位置发生变化。

## 6. 24 点保护

家庭 24 点 Pages 根站属于受保护资源。实施必须满足：

- 发布前后根目录现有文件逐项哈希一致；
- 根地址标题、主要静态文件和 HTTP 状态保持不变；
- 不修改根站 Manifest、Service Worker、入口 HTML 或缓存策略；
- Pages 提交只允许新增或更新 `sherlock-english/` 子目录；
- 若发现发布工具会清空或替换整个 Pages 站点，立即停止，不执行发布。

## 7. 验证门

### 自动验证

- Python、Web、两支云函数现有测试全部通过；
- TypeScript 和生产构建通过；
- 构建产物敏感信息扫描通过；
- 新入口及路由回退返回 `200 text/html`；
- 不存在 `Content-Disposition: attachment`；
- 不出现 CloudBase 风险提示页；
- 构建清单中的 JS、CSS、课程 JSON、Manifest 和公开音频均可访问；
- CloudBase health、课程目录和 formal 进度只读调用成功；
- family24 根站文件及在线行为不变。

### iPad 真机验证

- Safari 首次打开无需点击腾讯云“确定访问”；
- 可添加到主屏幕并以 standalone 方式启动；
- 听力音频正常播放；
- 口语麦克风授权、录音、停止、回放和评分正常；
- 家长 test 写入仍为 test，不推进完成状态；
- 后台恢复和重新打开后仍能进入应用；
- 阶段二切换后，一对真实 formal 结果、推荐进度和私有录音即时及 24 小时对账通过。

## 8. 错误处理与停止条件

出现以下任一情况立即停止切换：

- GitHub Pages 在家中网络或 iPad 上不可稳定打开；
- CloudBase Web SDK 被 CORS 或安全域名拒绝；
- Pages 发布可能覆盖家庭 24 点根站；
- 发现敏感信息进入构建产物；
- test 被写入 formal，或 formal/test 边界发生变化；
- 音频、麦克风、讯飞评分或私有录音访问失败；
- 正式结果、录音或推荐状态出现差异。

失败时不删除任何 CloudBase 数据，不恢复 Streamlit formal，也不继续尝试新的免费平台。先回滚本次前端入口，再由 00 决定是否进入自定义域名与 ICP 备案方案。

## 9. 回滚

阶段一回滚：

- 删除 Pages 仓库中的 `sherlock-english/` 候选目录；
- 删除新增的 `/sherlock-api` HTTP 网关路由；
- CloudBase 原入口和全部数据保持不变。

阶段二回滚：

- 恢复 CloudBase 原 `/sherlock-english/` 完整静态版本和 Service Worker；
- 恢复原入口说明；
- Pages 候选目录可保留为不可使用的 test 证据或删除；
- 对切换窗口内产生的记录只做对账，不删除、不改写。

## 10. 完成定义

只有同时满足以下条件，才能宣布入口迁移完成：

- GitHub Pages iPad test 全流程通过；
- 家庭 24 点根站无变化；
- 家长明确批准正式切换；
- 一对真实 formal 听力/口语完成并即时对账；
- 24 小时后结果、推荐和录音仍一致；
- CloudBase 原前端已经只读提示，新入口成为唯一日常入口；
- 项目状态、URL、提交、验证证据和回滚版本已经登记。

## 11. 2026-08-31 实施修订与阶段一证据

原设计假设可将 GitHub Pages 域名加入 CloudBase Web 安全域名。实施时平台明确返回 `[CreateAuthDomain] 当前套餐无法执行此操作`，该假设在现有体验版套餐下不成立。为保持方案 A 的产品边界且不升级付费，连接层作以下技术修订：

- 前端静态承载仍为批准的 GitHub Pages `/sherlock-english/` 子路径；
- 后端、数据库、正式结果、私有录音和讯飞链路仍在原 CloudBase 环境；
- GitHub Pages 前端通过同环境 HTTP 网关调用 `sherlock-api`，不再依赖 Web SDK 安全域名；
- `sherlock-api` 同时保留既有 Event 调用与新增 HTTP 调用，旧正式入口没有被切断；
- HTTP 入口只接受 JSON `POST/OPTIONS`，校验客户端标识、请求大小和唯一 GitHub Origin；错误 Origin 返回 403 且不返回 `Access-Control-Allow-Origin`；
- 候选构建不包含 CloudBase Publishable Key、管理密钥、JWT、`private/`、正式结果或私有录音。

阶段一已完成的自动证据：Pages 提交 `3eb0d9b` 部署成功；候选四个入口、主脚本、Manifest、Service Worker、两类课程 JSON 和代表音频均为 HTTP 200；HTML 不含附件响应头；家庭 24 点根站保持 HTTP 200 且 Pages 提交在 `sherlock-english/` 以外零变更；HTTP 网关的许可 Origin health 为 200、预检为 204、非许可 Origin 为 403。

2026-08-31 家长已在无 VPN iPad Safari 完成听力 test、口语录音/回放、8 题评分和最终 test 提交，并明确确认整体验收通过。云端复核最新口语结果为 `S01D39/test/completed`、97 分、24/24 星、8/8 题；8 个最终私有 WAV 均存在且非空，临时分块目录为空，且没有新增 formal 结果。

该修订和阶段一验收通过均不等于阶段二获批。家长再次明确批准正式切换前，原 CloudBase 地址继续是唯一儿童 formal 入口。
