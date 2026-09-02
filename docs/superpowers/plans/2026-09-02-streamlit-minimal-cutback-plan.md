# Streamlit 最小回切实施计划

1. 将 `tests/test_access_routes.py` 恢复为切换前的 Streamlit 路由安全测试，先确认当前只读入口不能通过新测试。
2. 仅将 `app.py` 恢复为提交 `14d4d65` 的最后稳定 Streamlit 路由实现，不回滚其他文件。
3. 运行 Streamlit 路由测试、全量 Python 测试、编译检查和 Secret 扫描。
4. 提交并推送最小恢复变更，等待既有 Streamlit Cloud 自动部署。
5. 线上验证固定 URL 已恢复首页和路由；不提交 formal 学习结果。
6. Streamlit 可用后，仅关闭 CloudBase `FORMAL_ENABLED`，不处理其他 CloudBase 资源。
7. 复核单一 formal 入口并记录部署版本、验证结果和未处理的 CloudBase 收尾项。
