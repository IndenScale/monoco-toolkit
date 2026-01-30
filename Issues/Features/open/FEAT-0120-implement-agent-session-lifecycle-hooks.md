---
id: FEAT-0120
uid: 3a9b1c
type: feature
status: open
stage: draft
title: Implement Agent Session Lifecycle Hooks
created_at: '2026-01-30T16:55:00'
updated_at: '2026-01-30T16:55:00'
parent: EPIC-0022
dependencies: []
related: []
domains:
- Guardrail
tags:
- '#FEAT-0120'
- '#EPIC-0022'
files: []
opened_at: '2026-01-30T16:55:00'
---

## FEAT-0120: Implement Agent Session Lifecycle Hooks

## 目标 (Objective)
为 Agent Session 实现生命周期钩子机制，特别是在 Session 结束时 (Teardown/Cleanup) 的自动化处理。
旨在解决“Agent 完成任务后环境残留”的问题，确保每次 Session 结束时，工作区都能恢复到干净、预期的状态（如切回主分支、删除临时分支）。

## 核心需求 (Core Requirements)
1.  **Reviewer Cleanup**:
    - 在 Reviewer Agent 结束会话前，必须确保当前 git HEAD 已切回 `main` 分支。
    - 必须确保本次 Session 关联的 Issue 分支（如果已合并）被安全删除。
2.  **Hook System**:
    - 在 `monoco/core/agent/session.py` 中实现 `on_session_start` 和 `on_session_end` 钩子接口。

## 验收标准 (Acceptance Criteria)
- [ ] 实现 `SessionLifecycleHook` 抽象类或接口。
- [ ] 在 `SessionManager.end_session()` 中集成 Hook 调用逻辑。
- [ ] 实现 `GitCleanupHook`：
    - [ ] `on_session_end`: 检查当前分支。
    - [ ] `on_session_end`: 如果当前分支不是 `main`，尝试 `git checkout main`。
    - [ ] `on_session_end`: 检测关联 Issue 状态，如果已完成/合并，执行 `git branch -D <feature-branch>`。
- [ ] 只有在操作安全（无未提交更改、分支已合并等）时才执行清理，否则发出警告。

## 技术任务 (Technical Tasks)
- [ ] **Design**: 设计 Hook 注册与执行机制。
- [ ] **Impl**: 修改 `monoco/features/agent/session.py` 添加 Hook 支持。
- [ ] **Impl**: 编写 `GitCleanupHook` 逻辑。
- [ ] **Test**: 编写单元测试模拟 Session 结束时的分支切换与删除场景。
