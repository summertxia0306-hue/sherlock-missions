# GitHub Pages formal 切换与 W01D50 / S01D50 实施计划

> 对应设计：`docs/superpowers/specs/2026-09-01-github-pages-formal-cutover-w01d50-design.md`
> 状态：已完成并完成线上自动验收（2026-09-02）

1. 为服务端入口通道、公开课程过滤、formal/TEST 口语分流补失败测试。
2. 在 `sherlock-api` 中加入服务端可信通道与 `FORMAL_ENTRY_MODE` 硬门。
3. 让 Pages 构建只复制 formal 发布课程，函数侧继续保留 test 源用于隔离验收。
4. 让正式口语固定走分块上传，仅 test 在开关允许时尝试云存储直传。
5. 增加旧 CloudBase `/sherlock-english/` 迁移页与限定作用域的缓存清理 Service Worker。
6. 执行全量测试、覆盖率、构建、敏感信息扫描与发布前基线检查。
7. 先发布 Pages，再切换后端 formal 通道，最后发布旧入口迁移页。
8. 完成线上边界验证，登记发布提交、CloudBase 回滚配置和项目状态。
