---
id: EPIC-0018
uid: c1310c
type: epic
status: open
stage: doing
title: Monoco Toolkit 文档站点建设
created_at: '2026-01-19T13:37:37'
opened_at: '2026-01-19T13:37:37'
updated_at: 2026-01-19 14:25:36
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0018'
files: []
progress: 4/5
files_count: 0
isolation:
  type: branch
  ref: feat/epic-0018-monoco-toolkit-文档站点建设
  path: null
  created_at: '2026-01-19T14:25:36'
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

- [ ] **基础设施**:
  - `Toolkit/site` 初始化完成，VitePress 正常运行。
  - Tailwind CSS 配置生效，主色调符合 Monoco 品牌。
  - i18n 路由配置完成 (`/` -> English, `/zh/` -> Chinese)。
- [ ] **内容管道**:
  - 实现 `sync-docs.js` 脚本，将 `../docs` 内容同步至站点内容目录。
  - 侧边栏 (Sidebar) 能够根据文件结构自动生成或通过配置映射。
- [ ] **关键页面**:
  - 首页 (Hero Section + Features)。
  - 宣言 (Manifesto) - 阐述 "Agent-Native" 理念。
  - CLI Reference - 自动生成或手动维护的命令手册。
- [ ] **部署**:
  - 能够 build 出静态文件 `Toolkit/site/.vitepress/dist`。

## 子任务

- **基础设施**: FEAT-0093 (Site Infrastructure and Design System)
- **管道**: FEAT-0094 (Content Pipeline and i18n Strategy)
- **内容**: FEAT-0095 (Documentation Content and CLI Reference)
- **部署**: CHORE-0011 (Site Deployment Configuration)

## 技术任务

1.  **基础设施初始化**
    - [ ] 在 `Toolkit/site` 中执行 `npx vitepress init`。
    - [ ] 安装并配置 Tailwind CSS (含 PostCSS)。
    - [ ] 清理默认样式，应用 Monoco "Dark/Terminal" 主题变量。

2.  **内容管理**
    - [ ] 分析 `Toolkit/docs` 结构。
    - [ ] 创建 `scripts/sync-site-content.js`：将 `Toolkit/docs/{en,zh}` 复制到 `Toolkit/site/{en,zh}`。
    - [ ] 配置 `config.mts` 以支持 i18n 区域设置及导航/侧边栏。

3.  **特定页面**
    - [ ] 设计并实现落地页 (`index.md`，包含自定义布局特性)。
    - [ ] 将 `EPIC-0018` 战略内容迁移至 `Manifesto.md`。

## 审查评论

<!-- Required for Review/Done stage. Record review feedback here. -->
