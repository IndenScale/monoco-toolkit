---
id: FIX-0025
uid: 516e54
type: fix
status: open
stage: review
title: 修复 datetime.utcnow() 废弃警告
created_at: '2026-02-08T10:06:09'
updated_at: '2026-02-08T10:12:35'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0025'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Epics/open/EPIC-0036-test-epic.md
- Issues/Fixes/open/FIX-0024-test-zh-hint.md
- src/monoco/features/courier/adapters/dingtalk_stream.py
- src/monoco/features/courier/outbound_dispatcher.py
- src/monoco/features/courier/outbound_processor.py
- src/monoco/features/courier/outbound_watcher.py
- src/monoco/features/im/models.py
- tests/core/hooks/test_git_cleanup.py
- tests/features/courier/test_dingtalk_stream.py
- tests/features/courier/test_outbound_dispatcher.py
- tests/features/courier/test_outbound_processor.py
- tests/features/courier/test_outbound_watcher.py
- tests/features/issue/test_cli.py
- tests/features/issue/test_close_atomic.py
- tests/features/issue/test_issue_hint_lang.py
- tests/test_scheduler_base.py
- tests/test_scheduler_engines.py
criticality: high
solution: implemented
opened_at: '2026-02-08T10:06:09'
isolation:
  type: branch
  ref: FIX-0025-修复-datetime-utcnow-废弃警告
  created_at: '2026-02-08T10:06:12'
---

## FIX-0025: 修复 datetime.utcnow() 废弃警告

## Objective
修复 Python 3.12+ 中 `datetime.utcnow()` 已废弃的警告，以及 Pydantic v2 中 `class Config` 的废弃警告。

## Acceptance Criteria
- [x] courier 模块测试无 DeprecationWarning
- [x] im 模块测试无 PydanticDeprecatedSince20 警告
- [x] 所有 50+ 测试通过

## Technical Tasks
- [x] 将 `datetime.utcnow()` 替换为 `datetime.now(timezone.utc)`
- [x] 修复 `outbound_watcher.py` 时间戳解析的时区处理
- [x] 修复测试辅助函数时区格式问题
- [x] 将 `class Config` 替换为 `model_config = ConfigDict`

## Review Comments
已完成修复，所有测试通过。
