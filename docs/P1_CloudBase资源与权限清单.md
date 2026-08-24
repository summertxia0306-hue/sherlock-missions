# P1 CloudBase 资源与权限清单

环境：`family24-d7gqb6r6m2d722f7a`（与 24 点共用环境，资源严格隔离）

## P1 资源

| 类型 | 名称或路径 | P1 权限与用途 |
|---|---|---|
| 静态托管 | `/sherlock-english/` | 公开读取的家长 test 验收 PWA；已发布 12 个文件；不得写托管根目录 |
| 云函数 | `sherlock-api` | Event 函数；匿名 CloudBase 身份可调用；服务端再验证家长会话 |
| 数据库 | `sherlock_parent_sessions` | `ADMINONLY`；只存会话 token 的 HMAC，不存明文 token 或密码 |
| 数据库 | `sherlock_results` | `ADMINONLY`；P1 只允许 `data_kind=test`，不得产生 formal 完成状态 |
| 数据库 | `sherlock_audit_logs` | `ADMINONLY`；只存最小审计字段，不记录密码或完整个人数据 |
| 数据库 | `sherlock_auth_attempts` | `ADMINONLY`；认证失败限流，禁止浏览器直接读写 |
| 云存储 | `sherlock-english/test/*` | 继承环境“仅创建者及管理员可读写”；P1 仅放命名空间标记 |
| 身份认证 | 匿名登录 | 只用于获得稳定的 CloudBase 调用者身份；家长身份仍由 `sherlock-api` 验证 |
| API Key | `publish_key` | CloudBase 明确定义的前端公开密钥；构建时注入，不写入 Git |

## 服务端强制边界

- `formal_enabled=false`；任何包含 formal 的动作均拒绝。
- `submitResult` 必须携带有效、未过期且属于同一 CloudBase 调用者的家长会话。
- 浏览器传入的 `data_kind` 被忽略，落库固定为 `test`。
- 每条 P1 结果固定 `formal_completion_eligible=false`。
- 家长密码只以 scrypt 哈希存在于云函数环境变量；会话 token 只以 HMAC 存库。
- 认证失败按 CloudBase 调用者限流；对外只返回稳定错误码。

## 明确未修改

- 24 点静态托管根目录及 11 个当前发布文件；
- `family24-web` 应用及 `family24-web-003` 版本；
- 24 点本地部署包与回滚 ZIP；
- 套餐、自动续费、超额付费、云托管、HTTP 路由和已有系统集合。

## 发布后核验（2026-08-24）

- test URL：`https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/`
- 真实验收结果 ID：`58d7621e-0fd7-4abb-aaf8-a6ab65e9a5fd`
- 结果字段：`data_kind=test`、`formal_completion_eligible=false`
- 未认证写入：`UNAUTHORIZED`
- formal 动作：`FORMAL_DISABLED`
- `sherlock-api` 健康状态：`formal_enabled=false`、`writes=test-only`
- 套餐：体验版；到期 `2027-02-04 23:59:59`；`EnableOverrun=false`
- 发布后用量：已用 0.82 / 3000 点，剩余 2999.18 点
- 24 点：`family24-web-003` 仍为 `SUCCESS`；公开首页 HTTP 200；当前 11/11 文件大小和 MD5 未变化
