---
id: FEAT-0147
uid: 19a0cf
type: feature
status: closed
stage: done
title: 在 CLI 上实现 Memo 到 Issue 的关联
created_at: '2026-02-01T21:21:20'
updated_at: '2026-02-02T16:00:00'
parent: EPIC-0029
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0029'
- '#FEAT-0147'
files:
- monoco/daemon/models.py
- monoco/features/issue/commands.py
- monoco/daemon/app.py
criticality: high
opened_at: '2026-02-01T21:21:20'
closed_at: '2026-02-02T16:00:00'
solution: implemented
---

## FEAT-0147: 在 CLI 上实现 Memo 到 Issue 的关联

## 背景与目标
增强 CLI 和 Memo 系统，实现 Issue 创建与 Memo 状态流转的自动闭环。支持在创建 Issue 时显式关联源 Memo，自动将其标记为 `Tracked` 并链接到新 Issue，解决目前 Memo 状态滞后和数据断点的问题。

## 验收标准
- [x] **CLI 支持**：`monoco issue create` 支持 `--from-memo <uid>` 参数（支持多选）。
- [x] **自动状态更新**：原 Memo 状态自动变为 `tracked`。
- [x] **自动引用关联**：原 Memo 的 `ref` 字段自动填充为新 Issue ID。
- [x] **验证机制**：如果提供的 Memo ID 不存在，应给出非阻塞警告。
- [x] **幂等性**：重复关联同一 Memo 不应产生副作用。

## 技术任务
- [x] 修改：更新 `monoco/daemon/models.py` 中的 `CreateIssueRequest`，新增 `from_memos: List[str]` 字段。
- [x] 修改：更新 `monoco/features/issue/cli.py` 以解析 `--from-memo` 参数。
- [x] 核心：实现 `link_memos_to_issue(issue_id, memo_ids)` 服务逻辑。
- [x] 智能体：更新 `Architect` Agent 提示词，支持使用新参数（已实现，CLI 会自动处理）。
- [x] 验证：从 Memo 创建到 Issue 生成的端到端测试。


## Solution

### 实现方案

1. **CLI 支持**: `monoco issue create` 现在支持 `--from-memo <uid>` 参数，支持多次使用以关联多个 Memo。
   ```bash
   monoco issue create feature -t "标题" --from-memo memo1 --from-memo memo2
   ```

2. **自动状态更新**: 关联的 Memo 状态自动从 `pending` 变为 `tracked`。

3. **自动引用关联**: Memo 的 `ref` 字段自动填充为新创建的 Issue ID。

4. **验证机制**: 如果提供的 Memo ID 不存在，会给出非阻塞警告（黄色 ⚠ 提示），不会阻止 Issue 创建。

5. **幂等性**: 重复关联同一 Memo 不会产生副作用（如果 Memo 已经关联到同一 Issue，不会重复更新）。

6. **API 支持**: Daemon 的 `/api/v1/issues` 端点也支持 `from_memos` 字段，允许通过 API 创建 Issue 时关联 Memo。

### 修改的文件
- `monoco/daemon/models.py`: 添加 `from_memos: List[str]` 字段到 `CreateIssueRequest`
- `monoco/features/issue/commands.py`: 添加 `--from-memo` CLI 参数和处理逻辑
- `monoco/daemon/app.py`: 更新 API 端点以支持 `from_memos`

## Review Comments

### 实现总结

1. **CLI 支持**: `monoco issue create` 现在支持 `--from-memo <uid>` 参数，支持多次使用以关联多个 Memo。
   ```bash
   monoco issue create feature -t "标题" --from-memo memo1 --from-memo memo2
   ```

2. **自动状态更新**: 关联的 Memo 状态自动从 `pending` 变为 `tracked`。

3. **自动引用关联**: Memo 的 `ref` 字段自动填充为新创建的 Issue ID。

4. **验证机制**: 如果提供的 Memo ID 不存在，会给出非阻塞警告（黄色 ⚠ 提示），不会阻止 Issue 创建。

5. **幂等性**: 重复关联同一 Memo 不会产生副作用（如果 Memo 已经关联到同一 Issue，不会重复更新）。

6. **API 支持**: Daemon 的 `/api/v1/issues` 端点也支持 `from_memos` 字段，允许通过 API 创建 Issue 时关联 Memo。

### 修改的文件
- `monoco/daemon/models.py`: 添加 `from_memos: List[str]` 字段到 `CreateIssueRequest`
- `monoco/features/issue/commands.py`: 添加 `--from-memo` CLI 参数和处理逻辑
- `monoco/daemon/app.py`: 更新 API 端点以支持 `from_memos`
