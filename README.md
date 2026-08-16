# Sherlock English Missions · 听说模块

小学英语听说训练 Streamlit 应用（沪教牛津版）。

- 部署/更新操作 → `00_部署指南_零基础版.md`
- **与统一系统对接（Codex 必读）→ `listening/CONTRACT.md`**：完整目录结构注释、
  功能清单（已实现/计划中/明确不做）、接口契约、结果结构、信息隔离红线
- 范围说明：本模块只做听力；跟读/口语/录音归口语模块（Codex）
- 设计与决策记录 → 项目文件夹 `听力部分/10_Streamlit迁移设计_v1_待确认.md`
- 新课开发流程：AI 写 `content/listening/W0xD0x.json` → `tools/生成音频_v2.bat` → commit+push
- 当前公共课件：听力 `W01D39–W01D50`，口语 `S01D39–S01D50`。`39–40` 保持原 M3U2 课程不变；`41–48` 依次综合复习 4A M1U1–M3U2，`49` 为 M1–M2 综合复习，`50` 为 M1–M3U2 全范围复习；不进入 M3U3。
- 历史保留：`01–38` 的公开课程 JSON、示范音和构建片段不再部署；正式成绩、错题、订正、口语明细、录音、私有结果库数据与 Git 历史均保留。
- 当前推荐：自动选择“第一个已可见且 formal 未完成的课程”。儿童列表以它为中心滚动显示最多 5 课；全部完成时显示最后 5 课。家长端仍可查看全部现存公共课件。
- 云端依赖：`streamlit==1.55.0`、`websocket-client==1.9.0` 已精确锁定；更新前必须先在干净环境验证健康检查和听力/口语入口。
- 热部署兼容：入口会同步 reload `storage.progress` 与页面模块，避免云端进程混用新页面和旧共享模块。

结构：`app.py` 临时入口（统一架构将替换）；`listening/` 引擎+页面+受限播放组件；
`content/` 课程数据；`static/audio/` 音频资产；`storage/` 进度接口（v1 运行目录存储）；
`tools/` 开发期课程与音频生成（`build_courses_41_50.py` 可重建本批综合复习 JSON，
`build_parent_docs_41_50.py` 可重建家长文档，`prune_public_courses.py` 负责受限清理历史公共资产）。
