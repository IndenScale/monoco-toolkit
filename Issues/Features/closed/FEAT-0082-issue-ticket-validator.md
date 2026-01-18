---
id: FEAT-0082
uid: 95fee4
type: feature
status: closed
stage: done
title: Issue Ticket Validator
created_at: "2026-01-16T08:56:11"
opened_at: "2026-01-16T08:56:11"
updated_at: "2026-01-16T09:45:45"
closed_at: "2026-01-16T09:45:45"
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0082: Issue Ticket Validator

## Objective

实现一个强大的 Issue Ticket 校验器 (`IssueValidator`)，用于集中管理和强制执行 Monoco Issue 系统的业务逻辑约束。这将替代目前散落在各处的卫语句，作为 Issue 数据完整性的唯一真理来源。

## Acceptance Criteria

1. **状态矩阵校验**: 必须严格遵循定义的状态-阶段映射:
   - Open: Draft, Doing, Review, Done
   - Close: Done
   - Backlog: Draft, Doing, Review
2. **内容完整性校验**:
   - 每个 Ticket 至少包含 2 个 Checkbox（代表 AC 和 Tasks）。
   - 当 Stage 为 `Review` 或 `Done` 时，所有 Checkbox 必须为已完成状态 (`[x]`) 或已废弃状态 (`[-]`)，不能有空勾选 (`[ ]`)。
3. **引用完整性校验**:
   - 所有引用字段 (`parent`, `dependencies`, `related`) 必须指向存在的 Issue。
   - 支持跨 Project 和 Workspace 的引用解析。
   - 支持 `{hash}` 格式的简化引用。
4. **结构一致性校验**:
   - 必须包含至少一个 Level 2 Heading (`##`)。
   - 该 Heading 的内容必须与 Front Matter 中的 ID 和 Title 严格匹配，格式为 `## {issue-id}: {issue-title}`。
5. **Review 增强校验**:
   - 当 Stage 进入 `Review` 或 `Done` 状态时，文档 Body 中必须包含 `## Review Comments` 标题，且该部分内容不为空（强制要求评审记录）。
6. **CLI 交互优化**:
   - 创建 Issue 时若缺少必要字段（如 closing 时的 solution），CLI 必须报错并列出所有合法的枚举值 (Implemented, Cancelled, Wontfix, Duplicate)。
7. **时间线一致性校验**:
   - 必须满足逻辑顺序: `created_at` <= `opened_at` <= `updated_at` <= `closed_at` (若字段存在)。
8. **Checkbox 严格校验**:
   - 必须使用无序列表符 `-`。
   - 必须使用单层方括号 `[]`。
   - 状态符仅限以下枚举:
     - `[ ]`: 待办/可选
     - `[x]`: 完成/选中
     - `[-]`: 废弃/部分完成/半选
     - `[/]`: 处理中/正在进行
   - **层级一致性**:若存在嵌套列表，父项状态必须正确反映子项状态聚合结果（如: 子项全选则父项必须为 `[x]`；子项有进行中则父项为 `[/]`）。

## Technical Tasks

- [x] **Design Validator Architecture**: 设计 `IssueValidator` 类，支持可插拔的校验规则 (`Rule` pattern)。
- [x] **Implement State Matrix Rule**: 实现状态与阶段的兼容性校验逻辑。
- [x] **Implement Content Completeness Rule**: 正则扫描 Body 内容，统计 Checkbox 数量及状态，针对 Review/Done 阶段实施强校验。
- [x] **Implement Reference Integrity Rule**: 实现引用解析器，验证 `TYPE-ID` 和 Hash 引用的有效性。
- [x] **Integrate with Linter**: 将 Validator 集成到 `monoco issue lint` 命令中。
- [x] **Implement Structure Consistency Rule**: 检查 Markdown Body 中是否存在与 Metadata 匹配的 `## ID: Title` 标题。
- [x] **Implement Review Comments Rule**: 验证在 Review/Done 阶段文档 Body 中是否存在 `## Review Comments` 标题及非空内容。
- [x] **Enhance CLI Enumeration**: 优化 `monoco issue close` 的参数校验，针对 Solution 字段提供交互式选择或详细错误提示。
- [x] **Clean Up Core**: 移除 `core.py` 中冗余的卫语句，完全委托给 Validator。
- [x] **Implement Checkbox Syntax Rule**: 使用正则严格匹配 `- [chk] text` 格式，支持 ` `, `x`, `-`, `/`。
- [x] **Implement Hierarchy Aggregator**: 解析 Checkbox 树状结构，验证父子状态一致性（Recursive check）。
- [x] **Implement Time Consistency Rule**: 解析并比较所有时间戳字段，确保逻辑时序正确。

## Review Comments

- **Self-Review**:
  - Implemented `monoco.core.lsp` to support standard Diagnostic types.
  - Created `IssueValidator` enforcing all acceptance criteria.
  - Refactored `monoco issue lint` to use the new validator.
  - Updated `monoco issue close` to provide helpful error messages for missing solutions.
  - Successfully verified implementation by running the linter against the existing codebase.
