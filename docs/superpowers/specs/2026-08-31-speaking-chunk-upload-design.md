# GitHub Pages 口语录音分块上传设计

> 日期：2026-08-31  
> 状态：家长已批准并通过书面规格；本地实现与自动验证通过，待候选入口部署和 iPad test 复验
> 唯一项目根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`

## 1. 故障事实与根因

GitHub Pages 候选入口的家长 test 听力流程已经成功，口语第 1 题在点击“就用这个，开始评分”后失败。失败发生在题目评分请求，不是整课最终提交。

线上边界探测确认：

- 同一个 GitHub Origin、同一个 CloudBase HTTP 网关和同一个 `health` 动作，在请求体约 102400 字节以内返回 200；
- 请求体增大到约 102432 字节后，网关在 `sherlock-api` 运行前返回 HTTP 413 / `EXCEED_MAX_PAYLOAD_SIZE`；
- 413 响应没有业务层 CORS 响应头，Safari 将其表现为 `fetch` 的 `TypeError`，前端因此显示“当前网络不可用”；
- 12 秒、16 kHz、单声道、16 bit PCM/WAV 约为 384 KB，Base64 后约为 512 KB，必然超过该入口的实际限制；
- 听力提交只包含小型 JSON，所以不受影响；
- 本次失败没有形成口语评分 take、test 结果或云端录音。

因此根因不是 iPad 录音、PWA 缓存、会话续期、讯飞 ISE 或整课提交，而是 GitHub Pages 前端到 CloudBase HTTP 网关之间的单请求体上限。

## 2. 目标与边界

### 目标

- 让 GitHub Pages 候选入口可以可靠上传现有质量的 PCM/WAV 并完成评分；
- 不降低录音采样率、位深或讯飞评分输入质量；
- 单个外部 HTTP 请求明显低于实测约 100 KiB 上限；
- 某一块失败时只重传该块，录音仍保留在浏览器内；
- 复用现有评分、proof、三星门控、幂等和最终私有录音路径；
- 保持 test/formal、旧 CloudBase Event 入口和历史数据兼容。

### 非目标

- 不改变课程、教材、评分阈值、三次门控或儿童反馈规则；
- 不改讯飞 ISE 请求契约；
- 不购买域名、升级套餐、开启按量付费或创建新环境；
- 不改写、删除或迁移历史成绩、录音和 Git 历史；
- 不把临时分块或最终录音公开；
- 不把本轮家长 test 结果用于正式学情。

## 3. 选定架构

只改 GitHub Pages 使用的 HTTP 传输层。原 CloudBase Web SDK/Event 调用继续保留原来的整段内部请求，作为现有正式入口兼容与回滚路径。

```text
iPad 录制 16 kHz PCM/WAV
        |
        | 浏览器内生成 Base64、字节数和 SHA-256
        v
HTTP 传输层按 65536 个 Base64 字符分块
        |
        | 每块请求约 65-70 KiB，最多 2 块并发
        v
sherlock-api: uploadSpeakingChunk
        |
        | 私有临时对象，确定性路径，可重复覆盖
        v
sherlock-api: scoreUploadedSpeakingTake
        |
        | 下载全部分块、校验顺序/大小/SHA-256、合并 WAV
        v
现有 score-speaking 内部调用
        |
        ├─ 讯飞 ISE
        ├─ 原正式/测试私有录音路径
        └─ 原 proof、星级、弱词、幂等缓存
```

Base64 分块长度固定为 65536 字符，对应最多 49152 字节二进制数据。它可被 4 整除，允许每块独立解码；加上会话、课程和校验元数据后，单次 JSON 仍与实测上限保留约 30 KiB 安全余量。

前端最多同时上传 2 块。以 12 秒录音估算约 8 块、4 轮请求；不会影响录音和回放，只会在点击评分后增加短暂上传阶段。

## 4. 外部动作合同

### `uploadSpeakingChunk`

请求包含：

```text
session_token
result_id
course_id
course_version
question_id
attempt
chunk_index
chunk_count
chunk_base64
chunk_sha256
wav_byte_length
wav_sha256
```

服务端必须：

- 重新认证 session，并由服务端决定 `data_kind`；
- 校验课程存在、版本一致、题号和 attempt 合法；
- 限制 `chunk_count`、索引、单块大小、总 WAV 大小和 SHA-256 格式；
- 严格校验 Base64 并核对该块解码后的 SHA-256；
- 把分块写入 `sherlock-english/tmp-speaking/{data_kind}/{owner_hash}/{take_id}/part-NN.bin`；
- 返回实际 `file_id`、块序号和块哈希；重复上传同一块覆盖同一确定性对象并返回成功；
- 不创建 speaking take、proof、结果、完成状态或评分审计。

`owner_hash` 由服务端 caller 身份派生，`take_id` 继续采用现有 data_kind/result/course/question/attempt 的确定性规则。路径不含学生姓名。

### `scoreUploadedSpeakingTake`

请求包含原评分元数据以及：

```text
chunk_count
part_file_ids
wav_byte_length
wav_sha256
```

服务端必须：

1. 再次认证 session、课程、版本、题号、attempt 和 caller 所有权；
2. 先查询现有 speaking take 幂等缓存；若已评分，直接返回原响应，并尽力清理本次重复上传的临时块；
3. 校验每个 `file_id` 都精确对应当前 caller、data_kind 和 take 的预期私有临时路径；
4. 按序下载所有块，限制合并总大小，核对 `wav_byte_length` 和整段 SHA-256；
5. 把合并后的 Base64 通过现有内部 HMAC 调用传给 `score-speaking`；
6. 沿用现有 WAV 头、PCM、静音、讯飞、最终录音上传、proof、星级和幂等逻辑；
7. 成功或幂等返回后尽力删除本次临时块；删除失败不得删除最终录音，也不得把评分改成失败。

任何缺块、乱序、替换文件、跨 caller、跨 test/formal、哈希不符或超限都必须在调用讯飞前拒绝。

## 5. 前端行为

`SherlockApi.scoreSpeakingTake()` 的页面合同保持不变。只有 `createHttpGatewayApp` 在检测到该动作时内部执行分块上传和合并评分；CloudBase Event transport 继续发送原请求。

前端 HTTP 传输层：

- 从现有 `wav_base64` 计算整段二进制 SHA-256；
- 拆成固定块并计算每块 SHA-256；
- 最多 2 块并发；
- 单块网络或 5xx 失败自动重试最多 2 次；认证、课程版本、格式和权限错误不盲目重试；
- 所有块成功后才调用 `scoreUploadedSpeakingTake`；
- 合并评分响应转换回现有 `SpeakingScoreResponse`，页面、proof 和门控代码不需要分叉；
- 整体失败时保留当前浏览器录音，不增加有效 attempt。

页面评分文案改为“正在上传录音并评分，请稍等…”。错误提示至少区分：

- `SPEAKING_UPLOAD_FAILED`：录音上传未完成，可直接再次评分；
- `SPEAKING_UPLOAD_INCOMPLETE`：分块缺失或校验失败，可直接再次评分；
- `SPEAKING_SCORE_UNAVAILABLE`：录音已到服务端但评分暂不可用；
- `UNAUTHORIZED`：沿用现有 formal 自动续期/test 重新认证规则；
- `SILENT_AUDIO`、`INVALID_AUDIO`、`COURSE_VERSION_MISMATCH`：沿用现有专用提示。

## 6. 幂等、失败和清理

- 分块对象使用确定性路径，重复上传是覆盖，不产生无界副本；
- 评分仍以现有 `take_id` 为幂等键；响应丢失后重传不会重复消耗有效录次，也应优先返回缓存结果；
- 某块失败只重试该块；超过重试次数后整次评分失败，但浏览器录音保留；
- 在全部校验完成前不调用讯飞、不写 speaking take、不生成 proof；
- 成功评分后最终 WAV 仍由 `score-speaking` 写入原 `sherlock-english/{data_kind}/{data_kind}/...` 路径；临时块不进入结果引用；
- 成功或命中幂等缓存后尽力清理临时块；中途放弃的少量私有块会在相同 take 重试时被覆盖，不得用扩大公开权限来解决清理问题。

## 7. 安全与数据边界

- 两个新动作都必须通过现有 session 验证，客户端声明的 `data_kind` 不作为事实；
- 临时路径绑定服务端 caller 所有权、课程、result、题号和 attempt；
- 最终动作不接受任意云存储路径，只接受本次 take 的精确预期路径；
- 临时块与最终录音均保持私有，不生成公共下载 URL；
- 前端包不增加 CloudBase 管理密钥、讯飞密钥或存储写凭证；
- GitHub Origin CORS 白名单不扩大；
- 家长 test 继续不推进儿童完成状态，不进入学习档案；
- 原 CloudBase formal 入口、旧结果、旧录音和 24 点资源不变。

## 8. 测试与验收

### 先失败的回归测试

实施前先增加能在当前代码失败的测试：

- 约 512 KB Base64 的 HTTP 评分不会再形成单个超限请求；
- 分块长度、块数、顺序和二进制重组正确；
- 最大并发不超过 2，单块最多重试 2 次；
- 上传中断后再次评分可覆盖并继续；
- 缺块、乱序、块哈希错、整段哈希错、超限和跨 caller 被拒绝；
- test/formal 临时路径隔离；
- 命中已有 take 时不重复调用讯飞；
- 评分成功后沿用原 proof、星级、最终录音引用和提交逻辑；
- HTTP 网关现有 Origin、客户端 ID、内容类型和小请求行为不回归。

### 自动验证

- Web 全套测试与覆盖率门；
- `sherlock-api` 全套测试与覆盖率门；
- `score-speaking` 全套测试；
- Python 既有测试；
- TypeScript、production build、敏感信息扫描；
- 本地验证每个外部分块 JSON 小于 75 KiB；
- 线上只读 health、Origin/CORS 和 24 点隔离复核。

### iPad 家长 test 验收

部署到候选入口后：

1. 在无 VPN 的 iPad Safari 重新录制口语第 1 题；
2. 点击评分，确认上传与评分成功、星级和反馈正常；
3. 如需完整阶段一验收，再完成 8 题并提交 test；
4. 云端核对结果为 `data_kind=test`，不推进 formal 推荐；
5. 核对最终私有录音存在，家长端可受控回放；
6. 核对没有学习档案更新、没有 formal 结果、没有 24 点资源变化。

本次失败的第 1 题录音不可能跨部署保留；家长已接受修复后重新录制。

## 9. 发布与回滚

发布只允许更新：

- `sherlock-api` 现有函数代码；
- GitHub Pages `sherlock-english/` 子目录构建产物。

不重新部署或修改 `score-speaking` 的业务合同，不创建新集合、云函数、环境、域名或付费能力。发布前后必须核对 family24 体验版/超额付费状态以及 24 点根站。

回滚时恢复本次修复前的 `sherlock-api` 和 GitHub Pages 子目录构建。原 CloudBase Event 正式入口从未切断；临时块没有结果引用，回滚不得删除任何历史最终录音或学习结果。

## 10. 完成定义

- 自动测试、覆盖率、类型检查和生产构建全部通过；
- 线上每个分块请求低于 75 KiB，HTTP 网关不再返回 413；
- 无 VPN iPad 家长 test 的口语第 1 题真实评分成功；
- test 录音私有保存且家长可受控读取；
- 无 formal/test 串写，无正式推荐推进，无历史数据变化；
- 24 点根站和资源不变；
- 提交、部署版本、URL、验证证据和回滚点登记到项目状态。

这个判断最可能错在哪：CloudBase HTTP 网关除请求体外还可能存在未公开的连续请求频率限制。方案把并发限制为 2，并要求单块重试和真实 iPad 验收；若线上仍出现平台级限流，应先把并发降为 1，而不是降低录音质量或扩大权限。
