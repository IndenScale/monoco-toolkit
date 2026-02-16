---
id: FEAT-0202
uid: d01e34
type: feature
status: open
stage: draft
title: 添加 trunk_branch 配置项支持自定义主干分支
created_at: '2026-02-16T16:17:51'
updated_at: '2026-02-16T16:17:51'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0202'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-16T16:17:51'
---

## FEAT-0202: 添加 trunk_branch 配置项支持自定义主干分支

## Objective
当前 Monoco 在多处硬编码使用 `main` 或 `master` 作为主干分支名称，这限制了使用其他分支命名（如 `develop`、`trunk`）的团队。本功能添加可配置的 `trunk_branch` 选项，使 TBD (Trunk Based Development) 工作流更加灵活。

## Acceptance Criteria
- [ ] `ProjectConfig` 中添加 `trunk_branch` 配置项，默认值为 `"main"`
- [ ] 创建 `get_trunk_branch()` 辅助函数统一获取主干分支名称
- [ ] `sync_issue_files()` 使用配置值替代硬编码的 `base_ref = "main"`
- [ ] `merge_issue_changes()` 使用配置值替代硬编码的主干分支判断
- [ ] `_validate_branch_context()` 使用配置值替代硬编码的 `["main", "master"]`
- [ ] 所有 hook 相关代码使用配置值替代硬编码
- [ ] 向后兼容：未配置时默认使用 `"main"`，保留原有的 `master` fallback 逻辑
- [ ] 单元测试覆盖自定义主干分支场景

## Technical Tasks
- [ ] 修改 `src/monoco/core/config.py` 在 `ProjectConfig` 中添加 `trunk_branch: str = "main"`
- [ ] 在 `src/monoco/core/git.py` 或 `config.py` 添加 `get_trunk_branch()` 辅助函数
- [ ] 修改 `src/monoco/features/issue/core.py`:
  - [ ] `sync_issue_files()` 使用配置值
  - [ ] `merge_issue_changes()` 使用配置值
- [ ] 修改 `src/monoco/features/issue/commands.py`:
  - [ ] `_validate_branch_context()` 使用配置值
- [ ] 修改 `src/monoco/features/issue/hooks/integration.py` 使用配置值
- [ ] 修改 `src/monoco/core/hooks/context.py` 使用配置值
- [ ] 添加单元测试
- [ ] 更新 AGENTS.md 相关文档（如需要）

## Review Comments
