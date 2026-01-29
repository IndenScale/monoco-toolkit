---
id: FIX-0015
uid: 'a3d4e2'
type: fix
status: closed
stage: done
title: 修正 IssueMetadata 字段约束为枚举类型
created_at: '2026-01-29T15:49:00'
updated_at: '2026-01-29T15:49:00'
parent: EPIC-0021
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0021'
- '#FIX-0015'
- '#Quality'
files:
- Toolkit/monoco/features/issue/models.py
solution: implemented
---

## FIX-0015: 修正 IssueMetadata 字段约束为枚举类型

## Objective
目前的 `IssueMetadata` Pydantic 模型对 `type`, `status`, `stage`, `solution` 等关键字段使用了宽泛的 `str` 类型，导致 Linter 无法有效拦截不规范的枚举值（如 `solution: finished`）。

## Acceptance Criteria
- [x] 将 `IssueMetadata.type` 类型更改为 `IssueType`。
- [x] 将 `IssueMetadata.status` 类型更改为 `IssueStatus`。
- [x] 将 `IssueMetadata.stage` 类型更改为 `Optional[IssueStage]`。
- [x] 将 `IssueMetadata.solution` 类型更改为 `Optional[IssueSolution]`。
- [x] 确保 `normalize_fields` 校验器仍然保留，以处理输入时的自动纠偏（如大小写）。

## Technical Tasks
- [x] 修改 `Toolkit/monoco/features/issue/models.py` 中的类型定义。
- [x] 验证 `monoco issue lint` 是否能正确检测出非法字符串。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
