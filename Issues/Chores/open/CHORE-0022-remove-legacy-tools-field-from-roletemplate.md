---
id: CHORE-0022
uid: 3759a1
type: chore
status: open
stage: review
title: Remove legacy 'tools' field from RoleTemplate
created_at: '2026-01-30T15:24:26'
updated_at: '2026-01-30T15:30:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0022'
- '#EPIC-0000'
files:
- monoco/features/scheduler/models.py
- monoco/features/scheduler/defaults.py
criticality: low
opened_at: '2026-01-30T15:24:26'
---

## CHORE-0022: Remove legacy 'tools' field from RoleTemplate

## Objective
从 `RoleTemplate` 模型及其相关配置中彻底移除废弃的 `tools` 字段。该字段曾用于辅助上下文注入，但目前已被独立于模型之外的工具加载机制替代，在运行时已属于"安慰剂"代码。清理该字段有助于保持数据模型的简洁和第一性原理设计。

## Acceptance Criteria
- [x] `monoco/features/scheduler/models.py` 中的 `RoleTemplate` 模型不再包含 `tools` 字段。
- [x] `monoco/features/scheduler/defaults.py` 中的所有内建角色（如 Planner, Builder 等）定义中已删除 `tools` 属性。
- [x] 确保 `monoco agent role info` 命令输出中不再显示该字段，且不影响其它功能。

## Technical Tasks
- [x] 在 `monoco/features/scheduler/models.py` 中删除 `tools` 字段及相关的 Pydantic 校验逻辑（如有）。
- [x] 同步更新 `monoco/features/scheduler/defaults.py` 中的 `DEFAULT_ROLES` 常量。
- [x] 全局搜索代码库，清理任何仍在使用 `role.tools` 属性的残留代码。
- [x] 验证 `monoco agent role list` 和 `monoco agent role info` 的可用性。

## Review Comments
- 已移除 `RoleTemplate` 模型中的 `tools: List[str]` 字段
- 已移除 `List` 导入（不再需要）
- 已更新 `defaults.py` 中所有 6 个默认角色的定义，删除 `tools` 属性
- 全局搜索确认无其他代码使用 `role.tools` 属性
- Python 验证通过，配置加载正常
