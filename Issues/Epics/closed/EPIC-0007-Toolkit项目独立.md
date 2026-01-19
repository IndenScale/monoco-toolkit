---
id: EPIC-0007
type: epic
status: closed
stage: done
title: Toolkit 项目独立化 (Toolkit Independence)
created_at: '2026-01-12T00:00:00'
updated_at: '2026-01-15T13:22:40'
closed_at: '2026-01-15T13:22:40'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0007'
- architecture
- devops
- strategic
progress: 4/4
files_count: 0
uid: 3b4179
---

## EPIC-0007: Toolkit 项目独立化 (Toolkit Independence)

### 解决方案 (Solution)

Toolkit has been successfully extracted to `../monoco-toolkit`.
Monoco `pyproject.toml` now depends on the external toolkit.
Local `Toolkit/` directory has been pruned.

## 目标 (Objective)

将 Toolkit (`/Toolkit`) 从 Monoco 主仓库 (`/`) 中完全解耦，使其成为一个独立版本控制、独立发布、可被外部项目复用的通用 Agent Native 开发工具链。

## 关键交付 (Key Deliverables)

1. **独立仓库 (Standalone Repository)**: 已创建 `monoco-toolkit`。
2. **独立构建流水线 (Independent CI/CD)**: 已建立 CI/Test。
3. **回引依赖 (Re-integration)**: Monoco 主仓库已通过 Editable Mode 引用新 Toolkit。
4. **清理 (Cleanup)**: Monoco 主仓库已移除 Toolkit 源码。

## Technical Tasks

- [x] Extract toolkit to standalone repository
- [x] Configure CI/CD for toolkit
- [x] Update Monoco main repo to use external toolkit dependency
- [x] Prune legacy Toolkit/ directory in main repo

## 执行历史 (Execution History)

- [x] [[FEAT-0036]]: 建立 Toolkit 独立构建与发布流程 (Done)
- [x] [[FEAT-0037]]: 重构 Monoco 依赖以适配外部 Toolkit (Done)
- [x] [[FEAT-0050]]: 清理 Monoco 主仓库中的 Toolkit 遗留 (Done)

## Review Comments

- [x] Self-Review
