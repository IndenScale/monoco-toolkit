---
id: EPIC-0021
uid: 772b8c
type: epic
status: closed
stage: done
title: 构建测试体系：严密的 Issue Ticket 验证机制
created_at: '2026-01-29T15:48:00'
updated_at: '2026-01-30T14:26:39'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0021'
- '#Quality'
files: []
criticality: high
opened_at: '2026-01-29T15:48:00'
closed_at: '2026-01-30T14:26:39'
solution: implemented
progress: 3/3
files_count: 0
---

## EPIC-0021: 构建测试体系：严密的 Issue Ticket 验证机制

## Objective
Monoco 的核心哲学是 "Task as Code"。为了确保任务系统的鲁棒性，必须建立严密的验证机制。
本 Epic 旨在通过强化 Pydantic 模型约束和引入 Pytest 自动化测试，确保 Issue Ticket 的静态字段及状态流转符合设计预期。

## Acceptance Criteria
- [x] **强类型约束**: IssueMetadata 的 type, status, stage, solution 字段必须使用 Enum。
- [x] **防御性解析**: 对于非规范的输入（如大小写不一），具备自动纠偏或明确报错的能力。
- [x] **单元测试覆盖**: 建立专门针对 `monoco.features.issue.models` 的测试套件。
- [x] **边界检查**: 覆盖 solution 字段乱填、状态机非法流转等边界情况。

## Technical Tasks
- [x] **FIX-0015**: 修正 IssueMetadata 字段约束为枚举类型。
- [x] **FEAT-0109**: 构建 monoco-issue 核心库的 pytest 单元测试体系。

## Review Comments
- 2026-01-30:
  - 核心 Issue 模型的 Pydantic 约束已全面切换为 Enum，消除了自由文本导致的状态不一致问题。
  - `FEAT-0109` 已成功建立完整的 Pytest 测试矩阵，覆盖了模型校验、生命周期流转和 CLI 命令验证。
  - 通过 `normalization` 逻辑确保了外部输入（特别是 YAML 手动修改）的鲁棒性。
  - 当前进展 100%，系统在底层数据模型层面已具备高度的安全性。

