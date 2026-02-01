---
id: FIX-0005
uid: c4b656
type: fix
status: closed
stage: done
title: 改进 Issue 状态机错误消息
created_at: '2026-02-01T23:30:38'
updated_at: '2026-02-01T23:37:30'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0005'
files:
- monoco/features/issue/engine/machine.py
- tests/features/issue/test_statemachine_errors.py
criticality: high
solution: implemented
opened_at: '2026-02-01T23:30:38'
closed_at: '2026-02-01T23:37:30'
---

## FIX-0005: 改进 Issue 状态机错误消息

## Objective
重构 `monoco/features/issue/engine/machine.py` 以在状态转换失败时提供描述性、可操作的错误消息。目前的错误消息过于通用，无法帮助用户理解问题所在或如何修复。

## Acceptance Criteria
- [x] 当找不到状态转换时，错误消息应清晰解释当前状态和目标状态
- [x] 当缺少或无效 solution 时，错误消息应根据可用工作流建议有效的 solution
- [x] 错误消息应包含从当前状态可用的转换提示
- [x] 所有错误消息遵循一致格式："Lifecycle Policy: {context}. {suggestion}"
- [x] 添加测试以验证所有错误消息场景

## Technical Tasks
- [x] 重构 `validate_transition()` 以提供描述性错误消息
  - [x] 将错误消息生成提取到辅助方法中
  - [x] 在错误消息中添加有关当前状态（status, stage）的上下文
  - [x] 在 solution 无效/缺失时添加有效 solution 的建议
  - [x] 列举从当前状态可用的转换
- [x] 为错误消息添加全面测试
  - [x] 测试找不到转换的错误
  - [x] 测试带有建议的无效 solution 错误
  - [x] 测试带有建议的缺失 solution 错误
  - [x] 测试错误消息格式的一致性

## Implementation Summary

### 对 `monoco/features/issue/engine/machine.py` 的更改

1. **添加了用于生成错误消息的辅助方法：**
   - `_format_state(status, stage)`: 格式化状态以供显示，处理 Enum 值
   - `_build_transition_not_found_error(...)`: 在不存在转换时构建描述性错误
   - `_build_invalid_solution_error(...)`: 在 solution 无效/缺失时构建错误
   - `get_available_solutions(...)`: 返回当前状态的有效 solution
   - `get_valid_transitions_from_state(...)`: 返回该状态的所有有效转换

2. **改进了错误消息：**
   - **找不到转换**: 现在显示当前状态、目标状态，并列出所有可用转换及其所需的 solution
   - **无效/缺失 solution**: 现在显示转换名称、当前/目标状态，并列出所有有效 solution

### 错误消息示例

**修改前:**
```
Lifecycle Policy: Transition from backlog(freezed) to open(review) is not defined.
```

**修改后:**
```
Lifecycle Policy: Transition from 'backlog(freezed)' to 'open(review)' is not defined. Available transitions from this state:
  - pull: 'backlog(freezed)' -> 'open(draft)'
  - cancel_backlog: 'backlog(freezed)' -> 'closed(done)' (requires --solution cancelled)
```

**修改前:**
```
Lifecycle Policy: Transition 'Accept' requires solution 'implemented'.
```

**修改后:**
```
Lifecycle Policy: Transition 'Accept' from 'open(review)' to 'closed(done)' requires a solution. Valid solutions are: cancelled, implemented, wontfix.
```

## Review Comments

### 自检 (Self-Review)

- [x] 错误消息具有描述性和可操作性
- [x] 所有测试均通过
- [x] 代码遵循代码库中的现有模式
- [x] 辅助方法已妥善记录
