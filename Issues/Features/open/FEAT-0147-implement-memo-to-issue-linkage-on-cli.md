---
id: FEAT-0147
uid: 19a0cf
type: feature
status: open
stage: draft
title: Implement Memo-to-Issue Linkage on CLI
created_at: '2026-02-01T21:21:20'
updated_at: '2026-02-01T21:21:20'
parent: EPIC-0029
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0029'
- '#FEAT-0147'
files: []
criticality: high
opened_at: '2026-02-01T21:21:20'
---

## FEAT-0147: Implement Memo-to-Issue Linkage on CLI

## Objective
增强 CLI 和 Memo 系统，实现 Issue 创建与 Memo 状态流转的自动闭环。支持在创建 Issue 时显式关联源 Memo，自动将其标记为 `Tracked` 并链接到新 Issue，解决目前 Memo 状态滞后和数据断点的问题。

## Acceptance Criteria
- [ ] **CLI Support**: `monoco issue create` 支持 `--from-memo <uid>` 参数（支持多选）。
- [ ] **Auto Status Update**: 原 Memo 状态自动变为 `tracked`。
- [ ] **Auto Referencing**: 原 Memo 的 `ref` 字段自动填充为新 Issue ID。
- [ ] **Validation**: 如果提供的 Memo ID 不存在，应给出非阻塞警告。
- [ ] **Idempotency**: 重复关联同一 Memo 不应产生副作用。

## Technical Tasks
- [ ] Mod: Update `monoco/daemon/models.py` -> `CreateIssueRequest` with `from_memos: List[str]`.
- [ ] Mod: Update `monoco/features/issue/cli.py` to parse `--from-memo` args.
- [ ] Core: Implement `link_memos_to_issue(issue_id, memo_ids)` service logic.
- [ ] Agent: Update `Architect` Agent Prompt to use this new parameter.
- [ ] Verify: End-to-end test from Memo creation to Issue generation.


## Review Comments


