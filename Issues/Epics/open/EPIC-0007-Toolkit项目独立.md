---
id: EPIC-0007
type: epic
status: closed
title: "EPIC-0007: Toolkit 项目独立化 (Toolkit Independence)"
created_at: 2026-01-12
tags:
  - architecture
  - devops
  - strategic
progress: 4/4
files_count: 0
stage: done
close_reason: completed
solution: >
  Toolkit has been successfully extracted to `../monoco-toolkit`.
  Monoco `pyproject.toml` now depends on the external toolkit.
  Local `Toolkit/` directory has been pruned.
---

## EPIC-0007: Toolkit 项目独立化 (Toolkit Independence)

## 目标 (Objective)

将 Toolkit (`/Toolkit`) 从 Monoco 主仓库 (`/`) 中完全解耦，使其成为一个独立版本控制、独立发布、可被外部项目复用的通用 Agent Native 开发工具链。

## 关键交付 (Key Deliverables)

1.  **独立仓库 (Standalone Repository)**: 已创建 `monoco-toolkit`。
2.  **独立构建流水线 (Independent CI/CD)**: 已建立 CI/Test。
3.  **回引依赖 (Re-integration)**: Monoco 主仓库已通过 Editable Mode 引用新 Toolkit。
4.  **清理 (Cleanup)**: Monoco 主仓库已移除 Toolkit 源码。

## 执行历史 (Execution History)

- [x] [[FEAT-0035]]: 初始化 Toolkit 独立仓库与历史迁移 (Done)
- [x] [[FEAT-0036]]: 建立 Toolkit 独立构建与发布流程 (Done)
- [x] [[FEAT-0037]]: 重构 Monoco 依赖以适配外部 Toolkit (Done)
- [x] [[CHORE-0050]]: 清理 Monoco 主仓库中的 Toolkit 遗留 (Done)
