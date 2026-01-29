---
id: FEAT-0095
uid: 3937b7
type: feature
status: closed
stage: done
title: 文档内容与 CLI 参考
created_at: "2026-01-19T13:47:03"
opened_at: "2026-01-19T13:47:03"
updated_at: "2026-01-19T14:42:00"
solution: implemented
parent: EPIC-0018
dependencies: []
related: []
domains: []
tags:
  - "#EPIC-0018"
  - "#FEAT-0095"
files: []
isolation:
  type: branch
  ref: feat/feat-0095-文档内容与-cli-参考
  path: null
  created_at: "2026-01-19T14:23:53"
---

## FEAT-0095: 文档内容与 CLI 参考

## 目标

完成核心文档页面的内容迁移与创作，包括首页、宣言和 CLI 参考手册。

## 验收标准

- [x] 首页 (Landing Page) 展示清晰的价值主张和 "Agent-Native" 视觉风格。
- [x] 宣言 (Manifesto.md) 完整阐述项目理念。
- [x] CLI Reference 包含所有子命令的用法说明。
- [x] 现有 `Toolkit/docs` 内容正确显示在站点中。

## 技术任务

- [x] 设计首页布局 (`index.md` + Frontmatter 配置)。
- [x] 迁移/撰写 `Manifesto.md`。
- [x] 整理 CLI 帮助文档，生成 Markdown 格式的参考手册。
- [x] 验证图片和相对链接在同步后是否正常工作。

## Review Comments

- 首页已采用 VitePress Home Layout 重新设计。
- `Manifesto.md` 已创作并同步至英/中两个版本。
- CLI 参考手册已整合至 `tools/cli.md`。
