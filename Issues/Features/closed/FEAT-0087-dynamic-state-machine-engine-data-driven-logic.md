---
id: FEAT-0087
uid: c2f4a1
type: feature
status: closed
stage: done
title: 动态状态机引擎 (数据驱动逻辑)
created_at: "2026-01-17T08:26:45"
opened_at: "2026-01-17T08:26:45"
updated_at: "2026-01-17T08:43:37"
closed_at: "2026-01-17T08:43:37"
parent: EPIC-0015
solution: implemented
dependencies: []
related: []
tags: []
path: /Users/indenscale/Documents/Projects/Monoco/Toolkit/Issues/Features/open/FEAT-0087-dynamic-state-machine-engine-data-driven-logic.md
---

## FEAT-0087: 动态状态机引擎 (数据驱动逻辑)

## 目标 (Objective)

将目前散落在 `core.py` 中的硬编码状态流转逻辑（`if-else`），重构为一个**动态状态机引擎 (Dynamic State Machine Engine)**。
该引擎将接受一个 "配置对象"（初期为默认配置）来判定合法的状态转移路径和可用的 Action。

这是实现 "可配置化" 的关键前置步骤: 先将逻辑**数据驱动化 (Data-Driven)**，再实现数据的外部加载。

## 验收标准 (Acceptance Criteria)

- [x] **TransitionRegistry**: 实现注册表，用于存储 `(FromState) -> (ToState)` 的合法路径。
- [x] **ActionService 重构**: Action 生成不再通过 `if-else` 判断，而是查询注册表。
- [x] **Core 瘦身**: `core.py` 中的业务逻辑委托给 Engine 处理，自身只负责 I/O。
- [x] **默认预设**: 将现有的 `EPIC/FEATURE` 逻辑固化为 `DefaultConfiguration` 数据结构。
- [x] **解耦**: 彻底分离 "Issue 状态逻辑" 与 "Agent 执行逻辑"。

## 技术任务 (Technical Tasks)

- [x] 创建 `monoco/features/issue/engine` 模块。
- [x] 实现 `StateMachine` 类，包含 `can_transition(from, to)` 和 `get_actions(state)` 方法。
- [x] 实现 `DefaultConfiguration` (将硬编码规则转化为数据表)。
- [x] 重构 `get_available_actions` 以使用 `StateMachine`。
- [x] 重构 `update_issue` 中的校验逻辑，对接 `StateMachine`。

## Review Comments

- [x] Self-Review

## Delivery

<!-- Monoco Auto Generated -->

**Commits (1)**:

- `76ba8f5` feat(issue): integrate dynamic state machine engine

**Touched Files (6)**:

- `monoco/features/issue/commands.py`
- `monoco/features/issue/core.py`
- `monoco/features/issue/engine/__init__.py`
- `monoco/features/issue/engine/config.py`
- `monoco/features/issue/engine/machine.py`
- `monoco/features/issue/engine/models.py`
