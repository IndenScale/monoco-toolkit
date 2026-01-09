---
parent: EPIC-0001
id: FEAT-0004
type: feature
status: closed
title: "Feature: Repo Management (Spike)"
created_at: 2026-01-08
tags: [toolkit, feature, repo, workspace]
solution: implemented
---

parent: EPIC-0001

## FEAT-0004: Repo Management (Spike)

## Objective

重构 `monoco spike` (或 `repo`) 命令，使其专注于多仓库管理，而非 Markdown 文档的 CRUD。
核心目标是让 Agent 能够直接访问和同步项目依赖的仓库，通过简单的配置管理工作区。

## Acceptance Criteria

1. **Delete CRUD**: 移除原有的 create/list/link/archive 文档管理命令。
2. **Init**: `monoco spike init` 能够初始化环境并在 `.gitignore` 中配置必要规则。
3. **Add**: `monoco spike add <url>` 能够在项目配置文件中记录仓库信息。
4. **Remove**: `monoco spike remove <name>` 能够从配置中移除仓库，并询问是否物理删除。
5. **Sync**: `monoco spike sync` 能够对配置文件中记录的所有仓库执行 `git pull` (若不存在则 clone)。
6. **Path Convention**: 强制使用 `.references` 目录作为下载路径

## Technical Tasks

- [x] Update `MonocoConfig` model to include `spike_repos` (List/Dict).
- [x] Implement `init` command: Check/Update `.gitignore`.
- [x] Implement `add` command: Update config file with new repo URL.
- [x] Implement `remove` command: Update config and optionally delete dir.
- [x] Implement `sync` command: Iterate repos, `clone` if missing, `git pull` if exists.
- [x] Remove legacy CRUD commands from `monoco/features/spike/commands.py`.
