# Streamlit 最小回切记录

日期：2026-09-03

## 结论

- 正式入口已恢复为原 Streamlit：`https://sherlock-missions-pesuyw9p75offrqtdadiag.streamlit.app`
- 本次保留并可进入听力 `W01D50`、口语 `S01D50`。
- 新教材 6 组课程继续保持 `publication_status=test`，不进入孩子正式目录或正式学习记录。
- CloudBase `sherlock-api` 已将 `FORMAL_ENABLED` 从 `true` 改为 `false`；其余 8 项环境配置未变化。
- CloudBase 的云函数、静态站点、数据库、成绩、录音和历史文件均保留，未做清理或反向迁移。

## 验证证据

- `python -m pytest tests -q`：56 passed，481 subtests passed。
- Python 编译检查通过；本地 Streamlit 启动并返回 HTTP 200。
- 线上首页已显示“进入听力”“进入口语”，不再显示迁移提示。
- 线上直达 `W01D50` 显示“听力综合测评 · Full review”及试音门。
- 线上直达 `S01D50` 显示“口语综合测评 · Full review”及麦克风试音门。
- 新教材测试课程直链不会进入正式答题页。
- CloudBase 环境变量复核：9 项键完整保留，除 `FORMAL_ENABLED` 外无值漂移。
- CloudBase 调用 `startChildSession` 返回 `FORMAL_DISABLED`，证明其正式写入已关闭。

## 边界

- 本次没有要求孩子重复完成课程；真实 iPad 录音、讯飞评分与 GitHub 私有结果写入沿用原 Streamlit 链路，在下一次自然学习时观察。
- CloudBase 收尾暂缓，后续如决定彻底停用，再单独设计清理与数据保全方案。

## 对应提交

- `3f880d3 docs: design minimal Streamlit cutback`
- `a00300f docs: plan minimal Streamlit cutback`
- `53847b5 feat: restore Streamlit formal entry`
