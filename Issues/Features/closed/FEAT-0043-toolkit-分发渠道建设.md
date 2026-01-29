---
id: FEAT-0043
uid: d7f2a1
type: feature
status: closed
stage: done
title: Toolkit 分发渠道建设
created_at: '2026-01-13T10:17:58'
opened_at: '2026-01-13T10:17:58'
updated_at: '2026-01-19T14:32:00'
solution: implemented
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0043'
---

## FEAT-0043: Toolkit 分发渠道建设

## Objective

构建全渠道分发矩阵，确保 Monoco Toolkit 能够触达从核心开发者到业务架构师的所有目标用户。
采用分级分发策略: Core (GitHub/PyPI/Docker) -> Package (Homebrew/NPM) -> Consumer (Native Wrappers)。

## Acceptance Criteria

- [x] **Tier 1 (Developer Native)**:
  - [x] GitHub Release 流程自动化。
  - [x] PyPI 包 (`pip install monoco-toolkit`)。
  - [x] `monoco serve` 成功启动并对外暴露开发者 API。
- [x] **Tier 2 (Package Managers)**:
  - [x] Homebrew Formula 验证通过。
  - [x] NPM Shim (`npm i -g @monoco-io/kanban`) 发布。
  - [x] 用户可以通过 `npx @monoco-io/kanban` 快速打开本地 Kanban 界面。

## Solution

成功建立核心分发渠道:

1. GitHub Release 自动化流程已上线。
2. PyPI 包已发布 (monoco-toolkit)，支持本地 `monoco serve`。
3. NPM Wrapper (`@monoco-io/kanban`) 已发布，支持快速启动可视化界面。
4. 原生 App 打包 (Tier 3) 根据策略调整暂行缓行，待 WAU 达标后再启动。

## Review Comments

- [x] 核心渠道自动化流程已验证。
- [x] 开发者安装体验良好。

## Technical Tasks

- [x] 配置 GitHub Actions 自动构建 PyPI 包。
- [x] 开发 NPM Wrapper 脚本 (调用系统 Python 或下载二进制)。
