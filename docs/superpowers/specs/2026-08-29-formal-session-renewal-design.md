# Formal 会话无损续期设计

## 背景与根因

2026-08-29 的 W01D49、S01D49 正式提交事故由两个问题叠加造成：

1. PWA 只在首次加载时创建约两小时有效的 formal 会话，没有在后台恢复、临近过期或 `UNAUTHORIZED` 后续期。
2. 服务端使用会变化的 session token 标识结果和 speaking take 的所有权。即使 CloudBase caller、`data_kind` 和 `result_id` 未变，换 token 后的幂等重试也可能被误判为 `RESULT_ID_CONFLICT`。

听力页面还会把所有提交错误显示成网络错误；口语页面虽然识别 `UNAUTHORIZED`，但要求刷新，会威胁尚未提交的过程状态。

## 边界

- 自动续期仅用于儿童 `formal` 会话。
- 家长 `test` 会话继续由密码创建；过期后必须重新认证。
- `data_kind` 始终由服务端已认证会话决定，浏览器声明无效。
- 不迁移、不删除、不重写任何历史正式结果或录音。
- 不生成验收用伪 formal 记录。

## 前端设计

新增一个单例式 formal 会话管理器：

- 保存当前 token 和服务端返回的 `expires_at`。
- 距离过期不足五分钟时，在下一次正式请求前续期。
- 页面通过 `visibilitychange` 或 `pageshow` 从后台恢复时检查是否需要续期。
- 正式请求收到 `UNAUTHORIZED` 后，丢弃旧 token、创建新 formal 会话，并把同一个请求最多重试一次。
- 多个并发恢复动作共用一个续期 Promise，避免生成续期风暴。
- 续期失败后返回明确的恢复失败错误，不进入无限重试。

页面在调用会话管理器前先构造固定请求对象。听力提交继续沿用同一 `result_id`、答案和播放次数；口语评分继续沿用同一 `result_id`、题号、attempt 和音频，最终提交继续沿用既有 proofs、星数及录音引用。

家长 test 页面不使用 formal 会话管理器，因而不会获得无密码续期。

## 服务端设计

为新写入的 formal 结果和 speaking take 增加由 HMAC 生成的稳定 caller 所有权标识：

- formal 幂等重放要求 `data_kind`、模块/课程和 caller 所有权全部一致。
- test 仍要求原 session token 标识一致。
- 不同 caller 即使猜中 `result_id`，仍得到 `RESULT_ID_CONFLICT`。
- 历史行没有新字段时继续使用旧 token 规则；查询和展示不受影响，也不对历史数据做迁移。
- 现有 `created_by_session` 保留用于审计和旧数据兼容。

speaking take 的确定性 `take_id` 不变，因此评分已在服务端完成但响应丢失时，续期后的同 caller 请求会读取同一 cached take，不会重复评分或重复上传录音。

## 错误呈现

- formal 续期过程中显示“正在自动恢复”，并说明答案或录音仍保留。
- formal 恢复失败显示专用提示。
- 只有离线或明确的传输异常显示网络错误。
- 其余服务端错误显示安全诊断码，不再伪装成网络错误。
- test 的 `UNAUTHORIZED` 明确要求返回家长入口重新认证。

## 验证

自动测试覆盖：临近过期、后台恢复、`UNAUTHORIZED` 单次重试、并发单飞、听力/口语相同 `result_id` 幂等、响应丢失、两题之间换 token、最终提交前换 token、不同 caller 冲突、test 不自动续期，以及旧 W01Dxx/S01Dxx 兼容。

完成单元测试、集成测试、类型检查和生产构建后形成 A 的单独 commit。生产部署必须再次取得家长明确批准。
