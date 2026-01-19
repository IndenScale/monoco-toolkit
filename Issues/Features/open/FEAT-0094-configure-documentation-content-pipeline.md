---
id: FEAT-0094
uid: a74498
type: feature
status: open
stage: doing
title: 内容管道与国际化策略
created_at: "2026-01-19T13:47:02"
opened_at: "2026-01-19T13:47:02"
updated_at: 2026-01-19 14:22:11
parent: EPIC-0018
dependencies: []
related: []
domains: []
tags:
  - "#EPIC-0018"
  - "#FEAT-0094"
files: []
isolation:
  type: branch
  ref: feat/feat-0094-内容管道与国际化策略
  path: null
  created_at: "2026-01-19T14:22:11"
---

## FEAT-0094: 内容管道与国际化策略

## 目标

建立从 `Toolkit/docs` 到 `Toolkit/site` 的内容同步机制，并配置 VitePress 的 i18n 多语言支持。

## 验收标准

- [x] 存在自动化脚本 `sync-site-content.js` 可同步文档。
- [x] 站点 URL 结构支持 `/` (Eng) 和 `/zh/` (中文)。
- [x] 侧边栏导航能正确反映文档目录结构。
- [x] 切换语言时，导航栏和内容同步切换。

## 技术任务

- [x] 分析 `Toolkit/docs` 目录结构。
- [x] 编写 `scripts/sync-site-content.js` 脚本。
  - [x] 复制 `docs/en` 到 `site/src/` (root)。
  - [x] 复制 `docs/zh` 到 `site/src/zh`。
- [x] 在 `config.mts` 中配置 `locales`。
- [x] 配置基础 Sidebar 导航。

## Review Comments

- 内容同步脚本已就绪：`scripts/sync-site-content.js`。
- 多语言配置已在 `config.mts` 中完成。
- 侧边栏已根据当前文档结构进行基础划分。
