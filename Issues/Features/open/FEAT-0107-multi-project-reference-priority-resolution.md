---
id: FEAT-0107
uid: 942d89
type: feature
status: open
stage: draft
title: 多项目引用优先级解析 (Multi-Project Reference Priority Resolution)
parent: EPIC-0001
dependencies: []
related: []
domains:
- intelligence
tags:
- '#EPIC-0001'
- '#FEAT-0107'
files: []
created_at: '2026-01-25T22:00:33'
opened_at: '2026-01-25T22:00:33'
---

## FEAT-0107: 多项目引用优先级解析 (Multi-Project Reference Priority Resolution)

## 目标 (Objective)
在多项目 (Multi-Project) 或工作空间 (Workspace) 环境下，解决 Issue ID 引用的解析歧义问题。当不同项目中存在相同 Short ID (e.g. `EPIC-0001`) 时，Linter 应当具备智能的优先级解析策略。

## 验收标准 (Acceptance Criteria)
- [ ] **就近原则 (Proximity Rule)**：优先解析当前 Project 上下文内的 ID。
- [ ] **显式命名空间 (Explicit Namespace)**：支持 `namespace::ID` 语法以强制指定引用目标。
- [ ] **根回退 (Root Fallback)**：如果当前项目也找不到，自动尝试在 Workspace Root 查找（例如 `EPIC-0000`）。
- [ ] **Linter 升级**：更新 `validator.py` 中的 `_validate_references` 逻辑以支持上述策略。

## 技术任务 (Technical Tasks)

- [ ] 设计 ID 解析器的优先级算法。
- [ ] 实现 `resolve_reference(context_root, target_id)` 核心函数。
- [ ] 更新 Linter 集成新的解析逻辑。
- [ ] 添加多项目环境下的单元测试用例。

## 评审备注 (Review Comments)
