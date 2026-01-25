---
id: FEAT-0107
uid: 942d89
type: feature
status: closed
stage: done
title: 多项目引用优先级解析 (Multi-Project Reference Priority Resolution)
created_at: '2026-01-25T22:00:33'
updated_at: 2026-01-26 00:23:42
parent: EPIC-0001
dependencies: []
related: []
domains:
- intelligence
tags:
- '#EPIC-0001'
- '#FEAT-0107'
files: []
opened_at: '2026-01-25T22:00:33'
closed_at: '2026-01-26T00:23:42'
solution: implemented
---

## FEAT-0107: 多项目引用优先级解析 (Multi-Project Reference Priority Resolution)

## 目标 (Objective)
在多项目 (Multi-Project) 或工作空间 (Workspace) 环境下，解决 Issue ID 引用的解析歧义问题。当不同项目中存在相同 Short ID (e.g. `EPIC-0001`) 时，Linter 应当具备智能的优先级解析策略。

## 验收标准 (Acceptance Criteria)
- [x] **就近原则 (Proximity Rule)**：优先解析当前 Project 上下文内的 ID。
- [x] **显式命名空间 (Explicit Namespace)**：支持 `namespace::ID` 语法以强制指定引用目标。
- [x] **根回退 (Root Fallback)**：如果当前项目也找不到，自动尝试在 Workspace Root 查找（例如 `EPIC-0000`）。
- [x] **Linter 升级**：更新 `validator.py` 中的 `_validate_references` 逻辑以支持上述策略。

## 技术任务 (Technical Tasks)

- [x] 设计 ID 解析器的优先级算法。
- [x] 实现 `resolve_reference(context_root, target_id)` 核心函数。
- [x] 更新 Linter 集成新的解析逻辑。
- [x] 添加多项目环境下的单元测试用例。

## Review Comments

- [x] 代码逻辑覆盖 (Priority Resolution Logic)
- [x] 多项目集成测试 (Integration Test)
- [x] Linter 兼容性检查
