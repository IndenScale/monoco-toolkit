---
id: FEAT-0043
uid: d7f2a1
type: feature
status: open
stage: doing
title: Toolkit 分发渠道建设
created_at: '2026-01-13T10:17:58'
opened_at: '2026-01-13T10:17:58'
updated_at: '2026-01-15T20:19:00'
parent: null
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0043'
---

## FEAT-0043: Toolkit 分发渠道建设

## Objective

构建全渠道分发矩阵，确保 Monoco Toolkit 能够触达从核心开发者到业务架构师的所有目标用户。
采用分级分发策略: Core (GitHub/PyPI/Docker) -> Package (Homebrew/NPM) -> Consumer (Native Wrappers)。

## Acceptance Criteria

- [ ] **Tier 1 (Developer Native)**:
  - [x] GitHub Release 流程自动化。
  - [ ] PyPI 包 (`pip install monoco-toolkit`) 包含编译好的 Kanban UI 资源。
  - [x] `monoco serve` 成功启动并对外暴露开发者 API。
- [ ] **Tier 2 (Package Managers)**:
  - [ ] Homebrew Formula 验证通过。
  - [x] NPM Shim (`npm i -g @monoco-io/kanban`) 发布。
  - [x] 用户可以通过 `npx @monoco-io/kanban` 快速打开本地 Kanban 界面。
- [ ] **Tier 3 (Consumer Native)**:
  - [ ] MacOS App (.dmg) 打包验证 (PyInstaller)。
  - [ ] Windows App (.exe) 打包验证 (PyInstaller)。

## Technical Tasks

- [x] 配置 GitHub Actions 自动构建 PyPI 包。
- [x] 开发 NPM Wrapper 脚本 (调用系统 Python 或下载二进制)。
- [ ] 编写 PyInstaller spec 文件以支持包含静态资源。
- [ ] 研究并验证 MacOS 菜单栏驻留 (Menu Bar App) 方案。
