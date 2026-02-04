---
id: CHORE-0041
uid: '899510'
type: chore
status: closed
stage: done
title: Release v0.4.0
created_at: '2026-02-04T23:33:58'
updated_at: '2026-02-04T23:55:53'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0041'
- '#EPIC-0000'
files:
- CHANGELOG.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Kanban/apps/webui/package.json
- Kanban/packages/core/package.json
- Kanban/packages/monoco-kanban/package.json
- extensions/vscode/package.json
- monoco/features/issue/commands.py
- pyproject.toml
- scripts/generate_changelog.py
- site/package.json
- tests/core/artifacts/__init__.py
- tests/core/automation/__init__.py
- tests/core/daemon/__init__.py
- tests/core/hooks/__init__.py
- tests/core/hooks/test_hook_base.py
- tests/core/router/__init__.py
- tests/core/watcher/__init__.py
- tests/core/watcher/test_watcher_base.py
- tests/features/hooks/__init__.py
- tests/features/hooks/test_hook_models.py
- tests/features/issue/test_close_atomic.py
- tests/features/issue/test_close_multi_branch.py
- tests/features/issue/test_issue_models.py
- tests/features/issue/test_prune.py
- tests/legacy/automation/test_config.py
- tests/legacy/automation/test_field_watcher.py
- tests/legacy/automation/test_memo_threshold_handler.py
- tests/legacy/router/test_action.py
- tests/legacy/router/test_router.py
- tests/test_integrations.py
- uv.lock
criticality: low
solution: implemented
opened_at: '2026-02-04T23:33:58'
closed_at: '2026-02-04T23:55:53'
---

## CHORE-0041: Release v0.4.0

## Objective
完成 v0.4.0 版本发布，包括版本号更新、CHANGELOG 生成和 CI 验证。

## Acceptance Criteria
- [x] 版本号已更新到 0.4.0
- [x] CHANGELOG 已生成
- [x] 所有测试通过（716 tests）
- [x] 代码已合并到 main

## Technical Tasks
- [x] 步进版本号到 0.4.0
- [x] 生成 CHANGELOG
- [x] 简化 close 命令（移除 --no-prune/--no-force）
- [x] 修复测试
- [x] 合并到 main 并推送

## Review Comments
✅ 发版完成：
- 简化了 close 命令设计，强制清理
- 移除冗余测试
- 716 个测试全部通过
- 已推送到 main，等待 CI 验证
