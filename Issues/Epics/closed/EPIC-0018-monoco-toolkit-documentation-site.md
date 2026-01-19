---
id: EPIC-0018
uid: c1310c
type: epic
status: closed
stage: done
title: Monoco Toolkit 文档站点建设
created_at: '2026-01-19T13:37:37'
opened_at: '2026-01-19T13:37:37'
updated_at: 2026-01-19 14:26:50
closed_at: '2026-01-19T14:26:50'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0018'
files: []
progress: 4/5
files_count: 0
---

## EPIC-0018: Monoco Toolkit 文档站点建设

## Objective

使用 **VitePress** 为 **Monoco Toolkit** 构建一个高品质的官方文档站点。
该站点将作为 Toolkit 的“使用手册”，聚焦于工具实用性、CLI 指南以及 "Issue as Code" 工作流的最佳实践。它需要与 Typedown 官网以及未来的 Chassis 平台区分开来。

**核心策略**:

- **技术栈**: VitePress + Tailwind CSS (v3/v4) + PostCSS.
- **位置**: `Toolkit/site` (Monorepo 内部管理).
- **多语言**: 必须支持 i18n (en/zh)，复用 `Toolkit/docs` 结构。
- **美学**: "Agent-Native" 风格，强制深色模式 (Dark Mode Only)，主要使用等宽字体和高对比度色彩。
- **内容架构**:
  - `Toolkit/docs` 作为单一内容源 (Single Source of Truth)。
  - 构建时通过脚本或 symlink 映射到 `Toolkit/site/src`。

## 验收标准

- [x] **基础设施**:
  - `Toolkit/site` 初始化完成，VitePress 正常运行。
  - Tailwind CSS 配置生效，主色调符合 Monoco 品牌。
  - i18n 路由配置完成 (`/` -> English, `/zh/` -> Chinese)。
- [x] **内容管道**:
  - 实现 `sync-site-content.js` 脚本，将 `../docs` 内容同步至站点内容目录。
  - 侧边栏 (Sidebar) 已基础映射。
- [x] **关键页面**:
  - 首页 (Hero Section + Features) 已完成设计。
  - 宣言 (Manifesto) 已创作并翻译。
  - CLI Reference 已整合至手册。
- [x] **部署**:
  - 配置了 `vercel.json` 及 GitHub Actions。

## 子任务

- **基础设施**: FEAT-0093 (Done)
- **管道**: FEAT-0094 (Done)
- **内容**: FEAT-0095 (Done)
- **部署**: CHORE-0011 (Done)

## 技术任务

1.  **基础设施初始化**
    - [x] 在 `Toolkit/site` 中执行 `npx vitepress init`。
    - [x] 安装并配置 Tailwind CSS (含 PostCSS)。
    - [x] 清理默认样式，应用 Monoco "Dark/Terminal" 主题变量。

2.  **内容管理**
    - [x] 分析 `Toolkit/docs` 结构。
    - [x] 创建 `scripts/sync-site-content.js`。
    - [x] 配置 `config.mts` 以支持 i18n 区域设置及导航/侧边栏。

3.  **特定页面**
    - [x] 设计并实现落地页。
    - [x] 将战略内容迁移至 `Manifesto.md`。

## Review Comments

- 全面完成了文档站点的搭建工作。
- 实现了内容从 `docs/` 到 `site/src/` 的自动同步。
- 建立了中英双语体系及符合 Monoco 美学的 UI。
- 提供了 Vercel 和 GitHub Actions 的部署配置。
- 所有子任务（FEAT-0093, FEAT-0094, FEAT-0095, CHORE-0011）均已完成并合并。
