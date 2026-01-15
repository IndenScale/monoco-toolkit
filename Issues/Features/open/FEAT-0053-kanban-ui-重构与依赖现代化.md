---
id: FEAT-0053
uid: e1a2b3
type: feature
status: in_progress
stage: draft
title: Kanban UI 重构与依赖现代化
created_at: "2026-01-13T16:33:00"
opened_at: "2026-01-13T16:33:00"
updated_at: "2026-01-13T16:33:00"
parent: EPIC-0003
dependencies: []
related: []
tags:
  - tech-debt
  - ui
---

## FEAT-0053: Kanban UI 重构与依赖现代化

## Objective

重写 Kanban WebUI 以彻底解决 React 19、Next.js 16+ 与旧版组件库（Blueprint.js）之间的依赖冲突问题，并提升 UI 现代化程度。目前的临时方案（依赖锁定降级）不可持续，阻碍了技术栈的升级。

## Acceptance Criteria

- [ ] **现代化组件库**：迁移至 Shadcn/UI 或 Mantine 等现代 React 组件库，全面支持 React 19。
- [ ] **技术栈升级**：
  - Next.js: 升级至 `16.1.1` 或更新。
  - React: 升级至 `19.2.x` (最新稳定版)。
  - Node.js: 升级至 `v24` (Current/LTS Candidate)。
- [ ] **React 19 支持**：确保所有依赖与 React 19 兼容，无 Peer Dependency 警告。
- [ ] **ESLint 9 兼容**：升级构建和 lint 工具链至最新标准。
- [ ] **功能对齐**：确保现有的看板、列表、详情页等功能在重构后完整保留。

## Technical Tasks

- [x] 评估并选型新的 UI 组件库（推荐 Shadcn/UI）。
- [x] 初始化新的 UI 框架配置。
- [ ] 逐步迁移 `apps/webui` 中的组件。
- [x] 移除 `Toolkit/Kanban/package.json` 中的 `overrides` 配置。
- [ ] 验证全链路构建通过。
