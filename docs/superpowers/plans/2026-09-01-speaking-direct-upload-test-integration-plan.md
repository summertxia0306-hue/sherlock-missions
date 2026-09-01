# 口语评分直传 TEST 集成实施计划

> 依据：`docs/superpowers/specs/2026-09-01-speaking-direct-upload-test-integration-design.md`
>
> 状态：待实施
>
> 唯一项目根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`

## 实施原则

- 仅接入 GitHub Pages 家长 TEST 口语入口；腾讯云正式入口、formal 会话和听力链路不动；
- 严格测试先行，先写失败测试，再写满足测试的最小实现；
- 现有 `uploadSpeakingChunk` / `scoreUploadedSpeakingTake` 全程保留；
- 所有直传、重试与分块兜底共用现有确定性 take ID；
- 任何状态不明确的超时都先走同一 take 的幂等恢复，不直接创建新 take；
- 不修改课程内容、学习档案、错题库或正式能力分析；
- 不触碰无关的未跟踪教材录入文件；
- 部署前后核对 CloudBase 环境、超额付费状态、函数环境变量和其他应用健康状态。

## 任务 1：锁定当前基线

### 只读检查

- 确认 Git 根目录和当前分支；
- 确认只有本任务文件与已知教材录入文件存在工作区差异；
- 记录当前 Web、`sherlock-api`、`score-speaking`、Python 测试与构建结果；
- 记录当前 GitHub Pages 候选入口、CloudBase 正式入口、活动 bundle 和云函数版本；
- 查询直传探针前缀、现有口语分块临时前缀均无遗留对象；
- 导出并哈希 `sherlock-api` 与 `score-speaking` 当前环境变量，只用于部署前后比对，不写入仓库。

### 验证命令

```powershell
git status --short
git log -1 --oneline
npm test
npm run typecheck
npm run build
```

Web 命令在 `web` 目录运行；函数测试分别在对应云函数目录运行。若基线失败，先判断是否与本任务相关，不带病进入部署。

## 任务 2：服务端直传存储适配器——测试先行

### 新增测试

文件：

- `cloudfunctions/sherlock-api/test/speaking-direct-upload-store.test.js`

覆盖：

- 只能为服务端给定的单一对象路径签发 PUT；
- 返回浏览器所需的最小 URL 与请求头，不返回长期密钥；
- 能下载私有对象为 `Buffer`；
- 能删除单一对象；
- SDK 返回缺字段、下载失败和删除失败时给出稳定的内部错误；
- 日志和抛出信息不包含签名 URL、临时 token 或录音正文。

先运行定向测试并确认因模块不存在而失败。

### 最小实现

文件：

- 新增 `cloudfunctions/sherlock-api/speaking-direct-upload-store.js`
- 修改 `cloudfunctions/sherlock-api/index.js`

实现 `issue(objectKey)`、`download(fileId)`、`remove(fileId)` 三个最小职责。可以复用现有探针已经验证的 COS 签名原语，但不得把真实评分动作接到 probe 前缀或 probe 白名单大小规则上。

### 本步验证

```powershell
node --test test/speaking-direct-upload-store.test.js
```

## 任务 3：服务端真实口语直传动作——测试先行

### 新增测试

文件：

- 新增 `cloudfunctions/sherlock-api/test/core-speaking-direct-upload.test.js`
- 必要时补充 `cloudfunctions/sherlock-api/test/core-speaking.test.js`

先覆盖以下失败与成功路径：

1. 未认证、儿童会话、formal 会话、隐藏课程及服务端开关关闭均拒绝签发；
2. 只有家长 TEST 会话能够为当前课程、题目、尝试和 result 申请票据；
3. 服务端生成确定性 take ID 与唯一临时路径，浏览器不能指定对象路径；
4. 票据绑定 caller、owner、会话、TEST、课程版本、题号、attempt、take ID、大小、SHA-256、MIME、file ID 和 120 秒有效期；
5. 小于有效 WAV、超过 `700000` 字节、非法哈希、非法类型、过期票据、篡改票据和跨用户票据均拒绝；
6. 评分动作在下载对象前先检查同一 take 是否已有评分；已有评分直接幂等返回，不再次下载或调用评分服务；
7. 新 take 下载对象后核对实际字节数、SHA-256 与 WAV 结构，再调用现有公共评分流程；
8. 成功后保存正常 TEST take、TEST 结果所需数据和最终私有录音，并删除临时对象；
9. 下载失败、大小不符、哈希不符、无效 WAV、评分失败和取消均按规则清理；
10. 清理失败不覆盖已经成功的评分，但返回可诊断的 cleanup 状态并写安全审计；
11. 重复评分请求、评分响应丢失后的重试和会话续期后的重试都返回同一 take；
12. 原有完整 Base64 与分块评分路径继续通过。

先运行定向测试并确认新动作不存在导致失败。

### 最小实现

文件：

- 修改 `cloudfunctions/sherlock-api/core.js`
- 修改 `cloudfunctions/sherlock-api/index.js`

新增职责清晰的动作：

- `createSpeakingDirectUpload`
- `scoreDirectUploadedSpeakingTake`
- `cancelSpeakingDirectUpload`

实现要求：

- 使用现有 HMAC 密钥签名独立版本的真实口语票据；
- 使用 `sherlock-english/tmp-speaking-direct/test/{owner}/{takeId}.wav` 一类服务端固定前缀；
- 服务端开关默认关闭，例如 `SPEAKING_DIRECT_UPLOAD_TEST_ENABLED=false`；
- `scoreDirectUploadedSpeakingTake` 复用现有 `scorePreparedSpeakingTake()`，不得复制评分和次数规则；
- 对同一 take 的缓存检查必须早于临时对象下载，以支持评分响应丢失后的幂等恢复；
- 返回 TEST 诊断所需的服务端校验、评分与清理耗时，但不返回内部对象路径。

### 本步验证

```powershell
node --test test/core-speaking-direct-upload.test.js
node --test test/core-speaking.test.js
npm run test:coverage
```

## 任务 4：前端直传状态机——测试先行

### 新增测试

文件：

- 新增 `web/src/core/speaking-direct-upload.test.ts`
- 修改 `web/src/core/cloudbase-api.test.ts`

测试矩阵：

- 将现有 WAV Base64 准确还原为原始字节并计算 SHA-256；
- 申请票据后使用原始二进制单次 PUT，不经过 `sherlock-api` 大请求体；
- PUT 成功后提交同一 result/题号/attempt 对应的直传评分；
- 返回直传模式与客户端哈希、票据、PUT、服务端校验、评分、总耗时；
- 票据申请或 PUT 明确失败时，用同一份 WAV 和同一 take 进入现有分块路径；
- 评分请求超时或响应不明确时，先重试同一直传评分动作；
- 重试得到幂等评分时不得触发分块；
- 服务端明确确认未评分且对象不可用时才允许分块兜底；
- 两条路径均失败时保留原始录音数据并返回可重试错误；
- feature flag 关闭、非 HTTP 客户端或非 TEST 会话继续使用原路径；
- 不在错误信息和日志暴露票据、签名 URL 或内部路径。

先运行定向测试并确认失败。

### 最小实现

文件：

- 新增 `web/src/core/speaking-direct-upload.ts`
- 修改 `web/src/core/cloudbase-api.ts`

实现单一入口的 direct-first 状态机。现有 `scoreSpeakingTake()` 对页面保持兼容；仅 GitHub Pages 候选构建且 TEST 功能开关开启时启用直传，其他场景继续走当前实现。

前端公开构建变量只允许是布尔开关，例如 `VITE_SPEAKING_DIRECT_UPLOAD_TEST=true`，不得包含 Secret。

### 本步验证

```powershell
npx vitest run src/core/speaking-direct-upload.test.ts src/core/cloudbase-api.test.ts
```

## 任务 5：口语页面 TEST 诊断——测试先行

### 修改测试

文件：

- 修改 `web/src/pages/SpeakingPage.test.tsx`
- 必要时修改 `web/src/App.test.tsx`

覆盖：

- 家长 TEST 评分成功后显示 `直传` 或 `分块兜底`；
- 显示哈希、票据、上传、校验、评分和总反馈耗时；
- 显示临时对象清理状态；
- 诊断不阻塞分数和反馈展示；
- formal 页面、儿童页面和开关关闭时不显示诊断；
- 失败后原录音仍可重试，不强制重新录制；
- 连续 8 题的诊断互不串题，最终课程提交逻辑不变。

### 最小实现

文件：

- 修改 `web/src/pages/SpeakingPage.tsx`
- 如现有样式不足，仅在现有样式文件中加入最小诊断样式

诊断采用家长可读的短文本，不显示 ticket、签名 URL、对象路径或堆栈。正式 UI 不增加任何调试元素。

### 本步验证

```powershell
npx vitest run src/pages/SpeakingPage.test.tsx src/App.test.tsx
```

## 任务 6：完整本地验证与安全审查

使用 `tdd-workflow` 完成红—绿—重构闭环，并在部署前使用 `security-review` 逐项检查身份、签名、输入、日志、临时对象和正式数据边界。

至少运行：

```powershell
# web
npm run test:coverage
npm run typecheck
npm run build

# sherlock-api
npm run test:coverage

# score-speaking
npm test

# 项目 Python
python -m pytest
```

同时执行：

- `git diff --check`；
- 搜索构建产物中的 Secret、CloudBase 管理凭据、签名 URL 和本地绝对路径；
- 检查 public bundle 只包含公开环境 ID 与布尔开关；
- 检查正式入口构建未启用直传开关；
- 检查 TEST 数据不会触发学习档案更新；
- 检查已知教材录入文件仍未纳入本任务提交。

只有相关测试、完整回归、覆盖率阈值、typecheck、build 和安全审查全部通过，才能部署。

## 任务 7：CloudBase 代码级灰度部署

### 部署前

- 确认目标环境仍为 `family24-d7gqb6r6m2d722f7a`；
- 确认体验版和超额付费关闭；
- 保存函数配置与环境变量哈希；
- 确认 24 点应用和英语正式健康检查正常；
- 确认临时对象前缀为空。

### 部署

- 只部署 `sherlock-api` 所需代码；
- 保留并核对全部现有环境变量；
- 仅为 TEST 灰度开启服务端直传开关；
- 不部署 CloudBase 正式静态站点，不修改 `score-speaking`，除非实现过程中证明其是设计内必需改动并重新获得批准。

### 部署后

- 比对环境变量哈希；
- 验证 formal、儿童、隐藏课程和未认证请求均不能申请直传；
- 验证 TEST 签发、上传、评分幂等和清理；
- 查询 `tmp-speaking-direct/test/` 最终为空；
- 再次验证英语正式入口和 24 点应用健康状态。

任一环境变量漂移、数据串写或其他应用异常都立即停止并回滚。

## 任务 8：GitHub Pages 候选部署

- 仅在 GitHub Pages 候选构建启用 `VITE_SPEAKING_DIRECT_UPLOAD_TEST=true`；
- CloudBase 正式构建保持关闭；
- 构建后扫描 bundle，确认无 Secret 和内部签名；
- 部署候选子路径，不覆盖其他 GitHub Pages 内容；
- 桌面浏览器完成一题真实 TEST 冒烟，确认直传、评分、诊断、最终录音与清理；
- 模拟直传失败，确认分块兜底仍能完成评分；
- 模拟评分响应丢失，确认同一 take 幂等恢复且不触发重复评分。

桌面冒烟产生的 TEST 数据必须明确标记，不更新学习档案。

## 任务 9：无 VPN iPad 整节验收

家长在无 VPN iPad Safari 上，从 GitHub Pages 家长 TEST 入口完成整节 8 题口语并最终提交。每题只需正常作答，不需要刻意录制到 700KB 上限。

验收后由系统核对：

- 8/8 题均取得评分；
- 8 条 TEST take 与课程提交状态正确；
- 8 份 TEST 私有最终录音存在且可由家长受控播放；
- 无重复评分、重复扣次数、丢题或正式数据写入；
- 每题传输方式和分阶段耗时完整；
- `tmp-speaking-direct/test/` 对象数为 0；
- 单题总反馈耗时中位数不超过 5 秒；
- 任意一题总反馈耗时不超过 8 秒；
- 8 题均走直传，未发生自动兜底。

若发生兜底，课程完成可判定连续性通过，但直传验收不通过；记录题号和错误域，修复后重新验收。

## 任务 10：结论、文档与回滚点

验收后更新：

- `docs/02_PROJECT_STATUS.md`
- 本实施计划的状态与客观结果
- 对应的已确认决策记录（只有验收结论明确后更新）

不得更新夏洛恪学习档案或错题库。

形成以下三种结论之一：

1. **稳定且达标**：登记 TEST 直传可用；正式入口切换仍需另立设计；
2. **稳定但未达性能门槛**：TEST 保留或关闭由家长决定；若继续优化，另立“评分直接读取对象/复用最终对象”设计；
3. **不稳定或有数据风险**：关闭服务端与候选前端开关，全部恢复现有分块链路。

回滚不删除历史 TEST 评分或私有录音，只执行：

- 关闭服务端 TEST 直传开关；
- 关闭 GitHub Pages 候选构建开关；
- 清理确认无业务引用的直传临时对象；
- 验证现有分块上传重新成为唯一传输方式；
- 复核 formal、test、正式录音与其他应用状态。

## 完成定义

只有以下全部满足，本计划才算完成：

- 代码、测试、安全审查、本地回归和构建通过；
- 云端部署未改变既有环境变量和正式入口；
- 无 VPN iPad 完成 8 题真实 TEST；
- 评分、最终录音、幂等、清理和性能门槛全部通过；
- 未发生正式数据污染；
- 文档记录真实结果并保留明确回滚点。

本计划完成也不等于批准正式入口切换。
