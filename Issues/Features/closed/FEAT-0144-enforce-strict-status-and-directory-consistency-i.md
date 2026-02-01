---
id: FEAT-0144
uid: 47e02d
type: feature
status: closed
stage: done
title: Enforce Strict Status and Directory Consistency in Issue Linter
created_at: '2026-02-01T20:56:58'
updated_at: '2026-02-01T23:37:31'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0144'
files: []
criticality: medium
solution: implemented
opened_at: '2026-02-01T20:56:58'
closed_at: '2026-02-01T23:37:31'
---

## FEAT-0144: Enforce Strict Status and Directory Consistency in Issue Linter

## 背景与目标

增强 Issue linter 的严格性，强制检查状态与文件目录的一致性。现有 linter 无法捕获状态异常（如使用 `done` 而非 `closed`）或文件位置错误（如将 Issue 放在 `Issues/Features/done/` 而非 `closed/` 目录）。本功能需要添加状态枚举验证、目录与状态映射验证、非法目录名检测以及阶段有效性检查，确保 Issue 文件组织规范，提高项目可维护性。

## Objective
Enhance `monoco issue lint` to enforce strict consistency rules between Issue status and file location.

**Context**:
- Found cases where Issues had illegal statuses (e.g., `done` instead of `closed`) or were in the wrong directory (e.g., `Issues/Features/done/` instead of `closed/`).
- The current linter failed to catch these anomalies.

## Acceptance Criteria
- [x] Linter reports error if `status` is not one of: `open`, `closed`, `backlog`.
- [x] Linter reports error if file is not in the directory matching its status.
- [x] Linter reports error for illegal directory names (e.g., `done/`).
- [x] Linter verifies `stage` is valid (e.g., `draft`, `doing`, `review`, `done`).

## Technical Tasks
- [x] Update `monoco/features/issue/linter.py`.
- [x] Add validation rules for Status enum.
- [x] Add validation rules for Directory <-> Status mapping.
- [x] Add unit tests for invalid cases.

## Review Comments

### 2026-02-01

**实现总结**:
1. **Status Enum 验证**: Pydantic 模型 `IssueMetadata` 已在解析时严格验证 status 必须为 `open`, `closed`, `backlog` 或 `archived`。无效值会在解析阶段抛出 `ValidationError`，linter 会将其报告为 Schema Error。

2. **Stage Enum 验证**: 同理，stage 必须为 `draft`, `doing`, `review`, `done` 或 `freezed`。无效值会在解析阶段被拒绝。

3. **目录与 Status 一致性验证**: 在 `linter.py` 中添加了 `Status/Directory Mismatch` 检查。当 Issue 文件的 `status` 字段与其所在目录（如 `open/`, `closed/`, `backlog/`）不匹配时，会报告错误。

4. **非法目录名检测**: 在 `linter.py` 中添加了 `Illegal Directory` 检查。当发现 `done/`, `freeze/`, `freezed/` 等非法目录名时，会报告错误并提示正确的目录名。

5. **单元测试**: 添加了 `tests/features/issue/test_linter_strict_status.py`，包含 12 个测试用例，覆盖所有新验证规则。

**修改的文件**:
- `monoco/features/issue/linter.py`: 添加目录/status一致性检查和非法目录名检测
- `monoco/features/issue/validator.py`: 添加 `_validate_status_enum` 和 `_validate_stage_enum` 方法（作为额外的防御层）
- `tests/features/issue/test_linter_strict_status.py`: 新增测试文件
