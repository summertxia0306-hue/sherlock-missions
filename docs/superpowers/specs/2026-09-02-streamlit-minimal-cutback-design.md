# Streamlit 最小回切设计

> 日期：2026-09-02  
> 状态：家长已批准；批准后无需再次审核规格，直接实施

## 目标

以最快速度和最小开发量，把儿童正式学习入口恢复为迁移前最后稳定的 Streamlit 模式。停止腾讯云付费域名、CloudRun、独立 Web App 和默认域名绕行方案。

## 实施范围

1. 仅恢复根目录 `app.py` 的 Streamlit 听力、口语、家长端和 test 路由。
2. 沿用现有 `listening/`、`speaking/`、`storage/`，以及 Streamlit 后台已有的 `PARENT_PASSWORD`、`RESULTS_REPO`、`RESULTS_TOKEN`、`XF_APPID`、`XF_API_KEY`、`XF_API_SECRET`。
3. 新的 Streamlit formal 结果与录音继续写入原 GitHub 私有结果库。
4. 不把 CloudBase 新增结果回写 GitHub，不整理、迁移或删除 CloudBase 数据与资源。
5. Streamlit 验证可用后，只关闭 CloudBase 儿童 formal 写入，确保不存在两个正式写入口；CloudBase 的历史数据、录音、函数、静态文件和失败候选全部保留。

## 明确不做

- 不开发 Streamlit 与 CloudBase 混合数据接口。
- 不迁移或合并两边的历史结果与录音。
- 不删除 `sherlock-english` Web App、CloudBase 静态托管、云函数、数据库、存储或 Git 历史。
- 不修改教材、课程内容、学习档案、校内错题库或 formal 学情结论。
- 不新增付费资源，不申请域名或 ICP 备案。

## 数据边界

- 切换前的 CloudBase formal 记录继续以 CloudBase 原始记录为准。
- 切换后的新 formal 记录以 GitHub 私有结果库为准。
- test 继续与 formal 隔离，不能产生儿童完成状态或学习结论。
- 本次不以开发验证结果更新学习档案。

## 切换顺序

1. 在不改变 CloudBase 的情况下恢复 Streamlit 入口。
2. 运行原有自动测试、语法检查和本地启动检查。
3. 部署 Streamlit，并验证线上首页、听力/口语路由和只读状态已经解除。
4. 确认 Streamlit 可用后，将 CloudBase `FORMAL_ENABLED` 关闭；其他配置不变。
5. 复核 Streamlit 为唯一儿童 formal 入口，CloudBase 不再创建新的儿童 formal 会话。

## 验收标准

- 原 Streamlit 固定 URL 可以正常打开，不再显示迁移提示。
- 听力、口语和家长入口可以加载。
- formal/test 代码边界和原测试通过。
- Streamlit 使用原私有结果库与讯飞配置，不在仓库暴露 Secret。
- CloudBase formal 写入关闭，历史资源和数据无删除。
- 家庭 24 点资源不受影响。

## 回滚

如果 Streamlit 部署或线上加载失败，恢复当前只读 `app.py`，CloudBase formal 保持原状态；不得通过删除 CloudBase 数据或放宽 test/formal 边界处理故障。
