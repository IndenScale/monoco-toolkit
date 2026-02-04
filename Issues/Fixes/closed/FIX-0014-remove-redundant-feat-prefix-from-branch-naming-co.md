---
id: FIX-0014
uid: 60ec63
type: fix
status: closed
stage: done
solution: implemented
closed_at: '2026-02-04T12:30:00'
title: Remove redundant feat/ prefix from branch naming convention
created_at: '2026-02-04T12:26:05'
updated_at: '2026-02-04T12:26:05'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0014'
files:
- monoco/features/issue/core.py
- monoco/features/issue/commands.py
- monoco/features/issue/resources/en/skills/monoco_atom_issue/SKILL.md
- monoco/features/issue/resources/zh/skills/monoco_atom_issue_lifecycle/SKILL.md
- monoco/features/issue/resources/en/AGENTS.md
- monoco/features/issue/resources/zh/AGENTS.md
- tests/features/issue/test_cli_logic_start.py
- tests/features/issue/test_sync_files_uncommitted.py
- tests/features/issue/test_branch_id_matching.py
criticality: high
opened_at: '2026-02-04T12:26:05'
---

## FIX-0014: Remove redundant feat/ prefix from branch naming convention

## Objective

当前分支命名使用 `feat/{id}-{slug}` 格式，导致：
1. **语义冗余**: Issue 已有 `type` 字段，分支名再次嵌套前缀（如 `feat/feat-0123-slug`）
2. **命名不一致**: Fix/Chore/Epic 类型也使用 `feat/` 前缀不合理
3. **额外层级**: 增加路径深度，无实际收益

改为 `{id}-{slug}` 扁平格式：
- `FEAT-XXXX-login-page`
- `FIX-XXXX-critical-bug`
- `CHORE-XXXX-refactor`

## Acceptance Criteria
- [x] 分支命名改为 `{id}-{slug}` 格式
- [x] 更新所有 Issue resources 中的文档（AGENTS.md, SKILL.md）
- [x] 更新所有相关测试用例
- [x] 向后兼容：能识别旧格式的 isolation.ref

## Technical Tasks
- [x] 修改 `core.py` 中 `start_issue_isolation()` 的分支命名逻辑
- [x] 修改 `commands.py` 中 `close` 命令的分支查找逻辑
- [x] 修改 `commands.py` 中 `sync-files` 命令的分支推断逻辑
- [x] 更新英文 SKILL.md 文档
- [x] 更新中文 SKILL.md 文档
- [x] 更新英文 AGENTS.md 文档
- [x] 更新中文 AGENTS.md 文档
- [x] 更新测试用例
- [x] 移除向后兼容逻辑（彻底放弃旧格式）

## Review Comments
- 验证通过。分支命名已统一为 `{id}-{slug}`，显著减少了路径嵌套深度。
- 文档与测试已同步更新。
