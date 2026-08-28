# 夏洛恪英语数字练习系统

本目录是夏洛恪英语项目迁移后的唯一活跃开发根目录，目标是建设一个面向 iPad 的 CloudBase 原生 PWA。

当前只实现两个正式模块：

- 听力训练
- 跟读与口语训练

当前核心还包括学校练习/考试材料的批改归档、校内错题库，以及由 00 总控维护的唯一权威学习档案。学生答卷与档案只保存在被 Git 排除的本地 `private/` 目录。

背单词、自动出纸面卷、互动课件、ChatGPT 陪练及其他新增功能均未立项；未来须回到 00 窗口重新讨论。历史材料继续保留，但不自动恢复旧工程。

## 当前状态

- 日期：2026-08-28
- 阶段：P5 上线切换与验收完整通过；CloudBase PWA 为唯一正式入口，Streamlit 保持只读
- 新项目根目录：`D:\ObsidianVaults\Education\Sherlock\English-Learning`
- 切换目标：CloudBase 原生 PWA 成为唯一正式入口，Streamlit 仅保留只读迁移提示
- 当前唯一开发根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`
- 旧代码源：`D:\project_antigravity\education_english\听力部分\sherlock-missions`（原地保留，只读参考）
- P5 主切换提交：`e2bc8fa`（已推送 `main`）
- P5 iOS 录音修复提交：`419e669`（已推送 `main`）
- P5 服务端以 `FORMAL_ENABLED` 为唯一正式写入开关；普通入口使用服务端 formal 会话，家长验收仍独立写 test
- CloudBase 地址：`https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/`

## 新窗口开始前必读

1. `AGENTS.md`
2. `docs/00_项目总计划.md`
3. `docs/01_已确认决策.md`
4. `docs/02_PROJECT_STATUS.md`
5. 与本次任务对应的阶段计划或窗口指令

## 文档入口

- 总计划：`docs/00_项目总计划.md`
- 已确认决策：`docs/01_已确认决策.md`
- 当前状态：`docs/02_PROJECT_STATUS.md`
- 数据治理：`docs/03_DATA_GOVERNANCE.md`
- 目标架构：`docs/04_目标架构.md`
- 路线图：`docs/05_ROADMAP.md`
- Codex 窗口架构：`docs/06_Codex窗口架构.md`
- 文档清单与开工顺序：`docs/07_文档清单与开工顺序.md`
- 分阶段实施：`docs/阶段计划/`
- 新窗口启动指令：`docs/窗口指令/`

## 关键边界

- 普通儿童入口提交默认是 `formal`。
- 家长测试必须经过认证并写为 `test`。
- `test` 不产生儿童完成状态，也不进入学情分析。
- 不删除成绩、错题、订正、录音、私有结果或 Git 历史。
- 迁移验收完成后，所有新增内容只写入本目录。
- 对孩子掌握程度的结论只能基于正式学习证据，不能由开发测试推断。
