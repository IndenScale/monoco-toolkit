---
id: CHORE-0049
uid: d4c081
type: chore
status: closed
stage: done
title: 清除遗留 IM 系统，统一使用 Mailbox/Courier 架构
created_at: '2026-02-10T12:10:42'
updated_at: 2026-02-10 12:17:00
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0049'
- '#EPIC-0000'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Epics/open/EPIC-0036-test-epic.md
- src/monoco/features/courier/im_integration.py
- src/monoco/features/im/__init__.py
- src/monoco/features/im/core.py
- src/monoco/features/im/handlers.py
- src/monoco/features/im/models.py
- src/monoco/features/im/session.py
- tests/features/im/test_session.py
criticality: low
solution: implemented
opened_at: '2026-02-10T12:10:42'
closed_at: '2026-02-10T12:16:59'
---

## CHORE-0049: 清除遗留 IM 系统，统一使用 Mailbox/Courier 架构

## Objective

清除遗留的 IM (Instant Messaging) 系统，统一使用更成熟的 Mailbox/Courier 架构处理外部消息。

遗留 IM 系统与 Mailbox/Courier 功能完全重叠：
- `IMMessage` ↔ `InboundMessage` (protocol/schema.py)
- `IMChannel` ↔ `Session` (protocol/schema.py)
- `MessageStore` ↔ `MailboxStore` (mailbox/store.py)
- Artifacts 集成已在 FEAT-0198 中通过 Courier 实现

## Acceptance Criteria

- [x] 删除 `src/monoco/features/im/` 目录及所有模块
- [x] 删除 `src/monoco/features/courier/im_integration.py`
- [x] 删除 `tests/features/im/` 测试文件
- [x] 提交变更到版本控制

## Technical Tasks

- [x] 删除遗留 IM 系统核心模块 (models.py, core.py, session.py, handlers.py)
- [x] 删除 Courier IM 集成适配器
- [x] 删除相关单元测试
- [x] 验证无其他模块依赖 IM 系统

## Review Comments

清除完成。遗留 IM 系统的功能已由 Mailbox/Courier 架构完全替代。
