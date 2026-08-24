# P1 CloudBase 资源基线

> 核验时间：2026-08-24  
> 核验方式：CloudBase CLI 3.8.0 只读命令、公开 URL HTTP 检查、本地发布包与云端文件逐项校验  
> 环境：`family24-d7gqb6r6m2d722f7a`

## 1. 套餐与费用安全门

- 环境状态：`NORMAL`
- 套餐：体验版（`baas_trial`）
- 创建时间：2026-08-04 14:03:13
- 到期时间：2027-02-04 23:59:59
- 自动续费：关闭
- 超额按量：关闭（`EnableOverrun=false`）
- 当前计费周期：2026-08-04 至 2026-09-04
- 周期额度：3000 点
- 已使用：0.69 点
- 剩余：2999.31 点
- 按量付费扣减：0 点

结论：本轮不需要购买套餐、资源包或开启按量付费。

## 2. 24 点应用基线

- 云应用：`family24-web`
- 路径：`/`
- 当前版本：`family24-web-003`
- 当前版本状态：`SUCCESS`
- 当前 URL：`https://family24-web-family24-d7gqb6r6m2d722f7a.webapps.tcloudbase.com/`
- 公开首页核验：HTTP 200，根节点、PWA manifest 和“家庭 24 点”标题均存在

版本记录：

| 版本 | 构建时间 | 状态 |
|---|---|---|
| `family24-web-003` | 2026-08-05 11:33:13 | SUCCESS |
| `family24-web-002` | 2026-08-05 11:29:11 | FAILED |
| `family24-web-001` | 2026-08-04 14:12:04 | SUCCESS |

## 3. 静态托管备份与对账

- 云端静态托管状态：online
- CDN 域名：`family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com`
- 云端文件总数：19
- 当前 24 点 `dist/` 文件：11
- 当前 24 点本地文件与云端大小/MD5 精确匹配：11/11
- 其他云端文件：6 个 CloudBase 系统认证/管理文件、2 个旧版构建残留资产
- 本地回滚包：`D:\project_antigravity\24\release\family24-PWA-v1.0.1-cloudbase.zip`
- 回滚包 SHA-256：`3EC2B2BC5B760273EA04542B0AA933AC07046DAFB3F95B6D88CC6505B2064370`
- ZIP 条目：11；反斜杠条目：0；包含根 `index.html`、`manifest.webmanifest`、`sw.js`

该本地发布包和当前云端文件已构成 P1 前的 24 点静态备份。P1 不覆盖根路径，不删除旧文件，不修改 `family24-web` 服务或版本。

## 4. 其他现有资源

- 云函数：0
- 云托管服务：0
- HTTP 路由：0
- 普通云存储对象：0
- 云应用：1，仅 `family24-web`
- 文档数据库集合：3 个系统集合
  - `relation_data_depart`：0 条
  - `sys_department`：0 条
  - `sys_user`：1 条
- 用户：1
- CORS 安全域名：11 条，均为环境默认域名或 CloudBase 官方域名

P1 英语资源必须继续遵循：

```text
静态路径：/sherlock-english/
云函数：sherlock-*
数据库集合：sherlock_*
云存储前缀：sherlock-english/*
日志标签：sherlock-english
```

## 5. 创建前结论

资源隔离和费用安全门通过，可以进入 P1 本地实现。任何云端创建动作必须显式使用环境 ID，并在动作前后重新核对 24 点 URL、`family24-web-003` 和根静态文件清单。

这个判断最可能错在哪：资源用量是计费系统当前快照，可能有延迟；P1 每次部署后仍需重新查询用量和现有资源，不能把本文件视为永久额度证明。
