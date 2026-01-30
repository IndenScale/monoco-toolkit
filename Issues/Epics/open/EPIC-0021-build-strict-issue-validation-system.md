---
id: EPIC-0021
uid: 772b8c
type: epic
status: open
stage: doing
title: 构建测试体系：严密的 Issue Ticket 验证机制
created_at: '2026-01-29T15:48:00'
opened_at: '2026-01-29T15:48:00'
updated_at: '2026-01-29T15:48:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0021'
- '#Quality'
files: []
progress: 3/3
files_count: 0
---

## EPIC-0021: 构建测试体系：严密的 Issue Ticket 验证机制

## Objective
Monoco 的核心哲学是 "Task as Code"。为了确保任务系统的鲁棒性，必须建立严密的验证机制。
本 Epic 旨在通过强化 Pydantic 模型约束和引入 Pytest 自动化测试，确保 Issue Ticket 的静态字段及状态流转符合设计预期。

## Acceptance Criteria
- [ ] **强类型约束**: IssueMetadata 的 type, status, stage, solution 字段必须使用 Enum。
- [ ] **防御性解析**: 对于非规范的输入（如大小写不一），具备自动纠偏或明确报错的能力。
- [ ] **单元测试覆盖**: 建立专门针对 `monoco.features.issue.models` 的测试套件。
- [ ] **边界检查**: 覆盖 solution 字段乱填、状态机非法流转等边界情况。

## Technical Tasks
- [x] **FIX-0015**: 修正 IssueMetadata 字段约束为枚举类型。
- [ ] **FEAT-0101**: 构建 monoco-issue 核心库的 pytest 单元测试体系。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
