---
id: FEAT-0147
uid: 19a0cf
type: feature
status: open
stage: draft
title: 在 CLI 上实现 Memo 到 Issue 的关联
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

## FEAT-0147: 在 CLI 上实现 Memo 到 Issue 的关联

## 背景与目标
增强 CLI 和 Memo 系统，实现 Issue 创建与 Memo 状态流转的自动闭环。支持在创建 Issue 时显式关联源 Memo，自动将其标记为 `Tracked` 并链接到新 Issue，解决目前 Memo 状态滞后和数据断点的问题。

## 验收标准
- [ ] **CLI 支持**：`monoco issue create` 支持 `--from-memo <uid>` 参数（支持多选）。
- [ ] **自动状态更新**：原 Memo 状态自动变为 `tracked`。
- [ ] **自动引用关联**：原 Memo 的 `ref` 字段自动填充为新 Issue ID。
- [ ] **验证机制**：如果提供的 Memo ID 不存在，应给出非阻塞警告。
- [ ] **幂等性**：重复关联同一 Memo 不应产生副作用。

## 技术任务
- [ ] 修改：更新 `monoco/daemon/models.py` 中的 `CreateIssueRequest`，新增 `from_memos: List[str]` 字段。
- [ ] 修改：更新 `monoco/features/issue/cli.py` 以解析 `--from-memo` 参数。
- [ ] 核心：实现 `link_memos_to_issue(issue_id, memo_ids)` 服务逻辑。
- [ ] 智能体：更新 `Architect` Agent 提示词，支持使用新参数。
- [ ] 验证：从 Memo 创建到 Issue 生成的端到端测试。


## Review Comments
