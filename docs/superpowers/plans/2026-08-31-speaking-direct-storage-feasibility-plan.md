# 口语录音云存储直传隔离验证实施计划

> 依据：`docs/superpowers/specs/2026-08-31-speaking-direct-storage-feasibility-design.md`  
> 状态：书面规格已获家长批准

## 事实基线

- 唯一项目根为 `D:\ObsidianVaults\Education\Sherlock\English-Learning`；
- 当前 `main` 工作区在设计提交后保持干净；
- CloudBase 环境 `family24-d7gqb6r6m2d722f7a` 为上海体验版，存储桶为 PRIVATE；
- 项目固定的 `@cloudbase/node-sdk@3.18.3` 已提供 `app.getUploadMetadata({ cloudPath })`，返回上传 URL、临时 token、authorization、fileId 与 cosFileId；
- 当前 GitHub HTTP 分块方案已经通过无 VPN iPad 真机验收，必须继续保留。

## 实施步骤

### 1. 服务端测试先行

在 `cloudfunctions/sherlock-api/test/` 增加直传 probe 用例，先证明以下行为：

- 未认证、formal 会话和无效输入均被拒绝；
- 只有家长 test 会话能申请固定大小范围内的 probe；
- 对象路径只能由服务端生成，位于 `sherlock-english/test/direct-upload-probe/`；
- 返回的上传信息不包含管理密钥，日志不输出上传 token；
- finalize 会验证 HMAC 票据、caller、到期时间、对象路径、字节数和 SHA-256；
- 成功与校验失败都会尽力删除临时对象；
- cancel 只能删除当前票据对应的对象；
- probe 不调用讯飞、不保存 speaking take 或学习结果。

### 2. 服务端最小实现

新增独立 `direct-upload-probe-store.js`，只封装：

- `issue(path)`：调用 `getUploadMetadata()`，整理浏览器 PUT 所需的最小字段；
- `download(fileId)`：下载对象用于字节数和 SHA-256 核验；
- `remove(fileId)`：删除对象。

在 `core.js` 增加三个仅 test 会话动作：

- `createDirectUploadProbe`
- `verifyDirectUploadProbe`
- `cancelDirectUploadProbe`

票据使用现有 `PARENT_SESSION_HMAC_KEY` 签名，包含版本、caller 绑定、对象路径、fileId、声明大小、SHA-256、签发和到期时间。有效期固定 120 秒，不新增数据库集合。

### 3. 前端测试先行

在 `web/src/core/cloudbase-api.test.ts` 与父页面定向测试中覆盖：

- HTTP 客户端能调用三个 probe 动作；
- 浏览器生成固定 16 kHz、单声道、16 bit、约 150 KiB 的非儿童测试 WAV；
- 使用服务端返回的 URL/headers 执行单次二进制 PUT；
- 客户端展示 PUT、服务端核验和总耗时；
- PUT 或核验失败时调用 cancel；
- probe 只在 GitHub Pages 候选构建且家长认证后显示。

### 4. 前端最小实现

- 在 API 类型与实现中增加 probe 合同；
- 新增纯函数测试 WAV 生成器和 SHA-256 计算；
- 在家长端增加隐藏于 feature flag 后的“云存储直传探针”；
- 不接入口语课程页，不替换 `scoreSpeakingTake()`，不影响 formal 儿童入口；
- 构建变量仅为公开布尔开关，不包含 Secret。

### 5. 本地验证

依次运行：

- `sherlock-api` 定向及完整覆盖率测试；
- Web 定向及完整覆盖率测试；
- `score-speaking` 既有测试；
- Python 既有测试；
- TypeScript typecheck 与 production build；
- 敏感信息和公开包边界扫描；
- Git diff 与工作区检查。

### 6. 云端隔离部署与自动验证

- 部署前重新核对体验版、超额付费关闭及 24 点状态；
- 只更新既有 `sherlock-api` 和 GitHub Pages 候选子目录，不修改 CloudBase 正式静态入口；
- 使用家长 test 会话从 GitHub Pages Origin 执行一次 150 KiB PUT、verify 和 delete；
- 检查 probe 前缀为空，学习结果、speaking take 和正式录音计数未增加；
- 再次核对 24 点与 CloudBase 正式英语入口。

### 7. iPad 验收与结论

向家长提供一个按钮和最短操作步骤。iPad 无 VPN 验收只执行一次确定性测试 WAV，不启用麦克风。成功后记录 PUT、verify 和总耗时；失败时保留明确错误码和 CORS 证据。

只有 iPad 成功、对象清零、数据零污染和现有链路无回归同时满足，才能登记“直传传输层可行”。是否替换正式分块方案另立设计，不在本计划内。

## 回滚

- 停用候选构建中的 probe feature flag；
- 恢复 `sherlock-api` 到 probe 实现前版本；
- 删除 probe 前缀残留对象；
- 当前分块上传、正式录音、讯飞评分和 formal/test 数据无需迁移或回滚。
