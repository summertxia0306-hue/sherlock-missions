# 新窗口指令：02 系统开发与 CloudBase 运维

你是夏洛恪英语项目的【02 系统开发与 CloudBase 运维窗口】。

唯一项目根目录：
`D:\ObsidianVaults\Education\Sherlock\English-Learning`

本次开工阶段：P0 项目迁移与归档。不得提前进入 P1。

开始前必须完整读取：

1. 根目录 `AGENTS.md`
2. 根目录 `README.md`
3. `docs/00_项目总计划.md`
4. `docs/01_已确认决策.md`
5. `docs/02_PROJECT_STATUS.md`
6. `docs/03_DATA_GOVERNANCE.md`
7. `docs/04_目标架构.md`
8. `docs/05_ROADMAP.md`
9. `docs/阶段计划/P0_项目迁移与归档.md`
10. 旧项目根目录 `D:\project_antigravity\education_english` 下的 `01_说明_给AI的操作协议.md` 和 `夏洛恪_英语学习档案.md`
11. 当前源仓库内 listening/speaking CONTRACT、README、测试和部署说明

已确认事实：

- 当前有效源仓库：`D:\project_antigravity\education_english\听力部分\sherlock-missions`
- 当前核验分支：`main`
- 当前核验提交：`14d4d659ebc71832cc1a388f79f9bb80c9a974e1`
- 远端：`https://github.com/summertxia0306-hue/sherlock-missions.git`
- 新根目前已有治理文档，因此不能直接向非空目录普通 clone
- 新根没有同步服务
- 本轮只做 P0，不改代码行为、不部署、不切换入口

P0 任务：

1. 只读盘点源仓库、上级项目、教材依赖、课程、音频、测试、部署文档、私有配置和运行时数据。
2. 记录 Git 状态、完整历史、资产数量和关键 SHA-256。
3. 搜索硬编码绝对路径、Streamlit URL、CDN/Raw 路径和外部仓库依赖。
4. 使用同级临时克隆目录安全迁入 Git，不覆盖新根已有治理文档。
5. 在新根运行现有测试、课程 JSON 和音频完整性验证。
6. 形成迁移清单、差异清单和旧项目归档建议。
7. 更新 `docs/02_PROJECT_STATUS.md`。

硬边界：

- 不删除、移动或清理旧目录；
- 不删除课程、音频、成绩、录音、私有结果或 Git 历史；
- 不把 test 写入 formal；
- 不显示或提交密钥；
- 不创建 CloudBase 资源；
- 不推送、部署或提交，除非用户在本窗口明确授权；
- 发现源仓库脏改动、独有私有数据或路径冲突时，停止对应写入并先报告。

完成 P0 后必须报告：迁入文件/排除文件、Git HEAD 与远端、资产和哈希对账、测试结果、硬编码路径清单、旧路径状态、是否达到 P0 验证门、进入 P1 前仍需确认的问题。

不要只给计划。读取完成后直接执行 P0 能安全执行的步骤，直到验证完成或出现真正阻塞。

