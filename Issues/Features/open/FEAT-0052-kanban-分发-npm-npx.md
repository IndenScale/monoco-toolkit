---
id: FEAT-0052
uid: af6399
type: feature
status: open
stage: in_progress
title: Kanban 分发 - NPM/NPX
created_at: "2026-01-13T14:49:04"
opened_at: "2026-01-13T14:49:04"
updated_at: "2026-01-13T14:55:00"
parent: EPIC-0009
dependencies: []
related: []
tags: []
---

## Objective

建立 Monoco Kanban 的 NPM 自动发布流水线，使用户能够通过 `npx @monoco/kanban` 或 `npm install -g @monoco/kanban` 一键启动看板界面。该工具应能自动发现并连接本地运行的 Monoco Toolkit 后端。

## Acceptance Criteria

- [ ] **npx 启动**：运行 `npx @monoco/kanban` 能够启动一个轻量级 Web 服务并自动打开浏览器。
- [ ] **静态分发**：NPM 包应包含 `webui` 的预构建静态资源，无需用户本地进行 `next build`。
- [ ] **后端发现**：能够默认连接到 `http://localhost:3213` (Monoco 默认端口)，并支持通过参数修改。
- [ ] **自动化发布**：Git Tag (`v*`) 触发自动发布至 NPM Registry。
- [ ] **版本同步**：NPM 包版本与 Python Toolkit 版本保持一致。

## Technical Tasks

- [x] 创建 `Toolkit/Kanban/packages/monoco-kanban` 专用分发包。
- [x] 配置 `webui` 支持静态导出 (`output: 'export'`)。
- [x] 编写轻量级 CLI 启动器 (使用 `sirv` 或 `express` 配合 `open`)。
- [x] 创建 `.github/workflows/publish-npm.yml` 工作流并配置 NPM_TOKEN。
- [x] 更新主项目文档，增加 `npx` 使用说明。
- [ ] 验证发布流程：创建 v0.1.0-npm 测试版本。
