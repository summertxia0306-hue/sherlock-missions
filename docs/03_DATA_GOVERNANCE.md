# 数据治理与正式学习记录规则

## 1. 数据分类

### formal

孩子通过普通学生入口完成的正式学习记录。

可以用于：

- 完成状态；
- 推荐课程；
- 错题、弱词和订正分析；
- A 主线 + C 微调中的 C 线选择；
- 家长端正式报告。

### test

家长、开发者或验收流程产生的测试记录。

只能用于：

- 功能验收；
- 播放、提交、评分和持久化检查；
- 故障复现。

不得用于：

- 儿童完成状态；
- 推荐课推进；
- 学情结论；
- 错词或薄弱项判断。

## 2. 写入规则

- 儿童普通入口由服务端强制写 `formal`。
- `test` 只能来自已认证的家长会话。
- 前端传入的 `data_kind` 不可作为最终事实，云函数必须重新判定。
- 同一课程的 formal/test 页面状态、提交记录和录音路径必须隔离。
- 历史无 `data_kind` 记录按 test 处理，除非存在可验证的正式来源证据。

## 3. 完成状态

- 完成课程集合只查询 formal。
- test 即使满分或满星也不得标记完成。
- 推荐课是第一个可见且 formal 未完成的课程。
- 所有可见课完成后显示阶段完成状态，不自动越过教材进度。

## 4. 数据对象

### 通用结果头

```text
result_id
student_id
module_type
course_id
pair_id
data_kind
course_version
started_at
submitted_at
duration_seconds
device_info
```

### 听力结果

```text
score
section_scores
wrong_answers
corrections
play_counts
question_results
```

### 口语结果

```text
score
stars_total
stars_max
question_results
weak_words
take_stars
first_score
last_score
best_score
passed_by_safety
recording_refs
```

## 5. 录音规则

- 录音存入私有 CloudBase 云存储路径。
- 路径必须包含环境、data_kind、课程和随机记录 ID，不含真实姓名。
- 数据库只存私有引用和元数据，不在公共 JSON 暴露下载地址。
- 家长端通过受控云函数获取临时访问地址。
- 历史 GitHub 私有库录音在迁移对账完成前不得删除。

## 6. 历史迁移

迁移顺序：

1. 导出原始结果、状态、录音清单和旁路元数据；
2. 生成文件数量、字节数和 SHA-256；
3. 保留原始只读快照；
4. 导入 CloudBase；
5. 对账课程 ID、记录数、data_kind、时间、录音数量和哈希；
6. 家长端抽查；
7. 原私有结果库转为只读备份。

任何一步失败都不得以删除原数据作为修复方式。

P4 实施补充：

- 历史导入采用 `legacy_source_id`、`legacy_source_record_sha256` 和 `migration_batch_id` 保证可追溯与幂等；
- 旧课只标记为 `current-equivalent` 或 `legacy-only`，不得凭 ID 重叠推断为新学期新完成；
- 缺失 `data_kind` 的结果和无可验证分类的录音默认 test；
- 原始 Streamlit 展示文本可留在受控原始快照，不需要复制进业务数据库；
- 管理迁移历史 formal 不改变在线儿童入口 `formal_enabled=false / writes=test-only` 的阶段边界。

## 7. 学情边界

- 开发、测试和线上可用性不等于掌握。
- 口语星级只表示评分模型下的朗读表现，不等于理解词义。
- 教材已上完只表示接触过，不表示掌握。
- 正式结论必须说明证据范围、反例和不确定性。

## 8. 密钥与权限

- 家长密码只保存不可逆哈希。
- 讯飞 AppID/APIKey/APISecret 只在云函数环境变量中使用。
- CloudBase 管理密钥不得进入浏览器包、课程 JSON、Git 或 Markdown。
- 公共课程和示范音频可公开读取；结果、录音和家长查询默认私有。
- 未经家长确认不得开启付费能力或扩大权限。
