---
id: CHORE-0011
uid: d65c6f
type: chore
status: open
stage: doing
title: 站点部署配置
created_at: "2026-01-19T13:57:44"
opened_at: "2026-01-19T13:57:44"
updated_at: 2026-01-19 14:25:48
parent: EPIC-0018
dependencies: []
related: []
domains: []
tags:
  - "#CHORE-0011"
  - "#EPIC-0018"
files: []
isolation:
  type: branch
  ref: feat/chore-0011-站点部署配置
  path: null
  created_at: "2026-01-19T14:25:48"
---

## CHORE-0011: 站点部署配置

## 目标

配置持续集成/持续部署 (CI/CD) 流水线，实现文档站点的自动化发布。

## 验收标准

- [x] 配置了 Vercel 部署所需的 `vercel.json`。
- [x] 提供了 GitHub Actions 流水线示例。
- [x] 构建命令集成了内容同步脚本。

## 技术任务

- [x] 选择部署平台 (推荐 Vercel)。
- [x] 添加构建配置 (`site/vercel.json`)。
- [x] 配置 GitHub Actions (`.github/workflows/deploy-docs.yml`)。
- [x] 验证生产环境构建流程。

## Review Comments

- 已添加 `site/vercel.json`。
- 已添加 `.github/workflows/deploy-docs.yml`。
- 构建流程已将内容从 `docs/` 同步至 `site/src/`。
