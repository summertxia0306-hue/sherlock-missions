# 夏洛恪英语数字练习系统

本目录是夏洛恪英语项目迁移后的唯一活跃开发根目录，目标是建设一个面向 iPad 的 CloudBase 原生 PWA。

当前只实现两个正式模块：

- 听力训练
- 跟读与口语训练

单词复习等能力只预留模块接口，未获单独立项前不开发。互动课件、纸质练习、ChatGPT 陪练和历史作业材料不属于本项目的活跃范围。

## 当前状态

- 日期：2026-08-24
- 阶段：P3 跟读与口语模块已部署到 test，等待真实 iPad 验收；不自动进入 P4
- 新项目根目录：`D:\ObsidianVaults\Education\Sherlock\English-Learning`
- 当前线上正式入口：Streamlit
- 目标正式入口：CloudBase 原生 PWA
- 当前唯一开发根：`D:\ObsidianVaults\Education\Sherlock\English-Learning`
- 旧代码源：`D:\project_antigravity\education_english\听力部分\sherlock-missions`（原地保留，只读参考）
- 当前 Git 基线：`main` / `954c02400a69ad7aed22574baa742500dfc15d1a`（P2 独立提交，已推送）；P3 尚未提交
- P3 仅允许在家长认证后的 test 环境验收听力与口语；formal 入口关闭，不产生正式完成状态或学情结论
- CloudBase P3 test 地址：`https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/`

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
