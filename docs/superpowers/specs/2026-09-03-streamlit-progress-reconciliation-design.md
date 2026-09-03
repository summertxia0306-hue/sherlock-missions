# Streamlit 第 46–49 课进度对账设计

日期：2026-09-03

## 目标

Streamlit 回切后，应准确显示听力与口语均只剩第 50 课未完成。

## 已确认事实

- GitHub 私有结果库的正式完成记录目前只到 `W01D45` / `S01D45`。
- CloudBase `sherlock_results` 存在 `W01D46–49`、`S01D46–49` 的 `formal/completed` 记录。
- 家长确认 `W01D50`、`S01D50` 尚未完成。CloudBase 中与此冲突的两条第 50 课 formal 标记不进入本次完成进度。

## 方案

在 GitHub 私有结果库新增 `completion_reconciliations.json`，只记录跨平台确认过的完成事实及来源结果 ID。Streamlit 将原 `results.json` 的 formal 完成集合与该文件合并后计算推荐课。

不向 `results.json` 伪造成绩，不迁移录音，不覆盖或删除 CloudBase/GitHub 原始数据。对账文件不进入公开代码仓库。

## 验收

- 自动测试证明：仅同一学生的 `formal/completed` 对账项计入完成；test、其他学生及第 50 课不计入。
- 线上听力推荐为 `W01D50`，口语推荐为 `S01D50`。
- 第 50 课按钮显示未完成且可开始。

