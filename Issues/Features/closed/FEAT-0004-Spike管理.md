---
id: FEAT-0004
type: feature
status: closed
stage: Done
title: "特性: 仓库管理 (Spike) (Repo Management - Spike)"
created_at: "2026-01-08T00:00:00"
opened_at: "2026-01-11T23:48:45.930778"
updated_at: "2026-01-11T23:48:49.554833"
closed_at: "2026-01-11T23:48:49.554866"
parent: EPIC-0003
solution: implemented
dependencies: []
related: []
tags:
  - toolkit
  - feature
  - repo
  - workspace
uid: bc3287
---

## FEAT-0004: 特性: 仓库管理 (Spike) (Repo Management - Spike)

## 目标 (Objective)

重构 `monoco spike` (或 `repo`) 命令，使其专注于多仓库管理，而非 Markdown 文档的 CRUD。
核心目标是让 Agent 能够直接访问和同步项目依赖的仓库，通过简单的配置管理工作区。

## 验收标准 (Acceptance Criteria)

1. **移除 CRUD (Delete CRUD)**: 移除原有的 create/list/link/archive 文档管理命令。
2. **初始化 (Init)**: `monoco spike init` 能够初始化环境并在 `.gitignore` 中配置必要规则。
3. **添加 (Add)**: `monoco spike add <url>` 能够在项目配置文件中记录仓库信息。
4. **移除 (Remove)**: `monoco spike remove <name>` 能够从配置中移除仓库，并询问是否物理删除。
5. **同步 (Sync)**: `monoco spike sync` 能够对配置文件中记录的所有仓库执行 `git pull` (若不存在则 clone)。
6. **路径规范 (Path Convention)**: 强制使用 `.references` 目录作为下载路径

## 技术任务 (Technical Tasks)

- [x] 更新 `MonocoConfig` 模型以包含 `spike_repos` (List/Dict)。
- [x] 实现 `init` 命令: 检查/更新 `.gitignore`。
- [x] 实现 `add` 命令: 使用新仓库 URL 更新配置文件。
- [x] 实现 `remove` 命令: 更新配置并可选删除目录。
- [x] 实现 `sync` 命令: 迭代仓库，若缺失则 `clone`，若存在则 `git pull`。
- [x] 从 `monoco/features/spike/commands.py` 中移除旧的 CRUD 命令。

## 交付 (Delivery)

<!-- Monoco Auto Generated -->

**Commits (1)**:

- `fb0c09b` feat(cli): implement optional branch/worktree isolation (FEAT-0004)

**Touched Files (5)**:

- `Issues/Features/open/FEAT-0004-optional-branch-isolation.md`
- `Toolkit/monoco/core/git.py`
- `Toolkit/monoco/features/issue/commands.py`
- `Toolkit/monoco/features/issue/core.py`
- `Toolkit/monoco/features/issue/models.py`

## Review Comments

- [x] Self-Review
