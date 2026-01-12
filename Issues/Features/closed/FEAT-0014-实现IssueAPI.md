---
id: FEAT-0014
type: feature
status: closed
stage: done
title: 实现 Issue 管理 API (Implement Issue API)
created_at: '2026-01-11T11:44:10.963729'
opened_at: '2026-01-11T11:44:10.963716'
updated_at: '2026-01-11T11:54:37.517210'
closed_at: '2026-01-11T11:54:37.517239'
solution: implemented
dependencies: []
related: []
tags: []
parent: EPIC-0003
---

## FEAT-0014: 实现 Issue 管理 API

## 目标 (Objective)

允许外部工具（如 Kanban/Dashboard）和 CLI 本身通过 Monoco Daemon API 编程式地管理 Issue。这统一了创建、更新和检索 Issue 的逻辑，确保所有接口上的生命周期管理一致。

## 验收标准 (Acceptance Criteria)

1. **创建 Issue**: `POST /api/v1/issues` 创建带有正确 Frontmatter 的新 Issue 文件并返回 `IssueMetadata`。
2. **获取 Issue**: `GET /api/v1/issues/{id}` 返回完整的 Issue 内容和元数据。
3. **更新 Issue**: `PATCH /api/v1/issues/{id}` 支持更新 `status`、`stage` 和 `solution`。必须自动处理文件移动（例如从 `open/` 移动到 `closed/`）。
4. **删除 Issue**: `DELETE /api/v1/issues/{id}` 删除 Issue 文件。
5. **生命周期守卫**: API 必须强制执行有效的转换（例如，如果是必需的，则在没有解决方案的情况下无法关闭）。
6. **错误处理**: 对验证错误或文件丢失返回正确的 HTTP 4xx 代码。

## 技术任务 (Technical Tasks)

- [x] **重构核心逻辑**: 更新 `monoco.features.issue.core` 函数 (`create_issue_file`, `update_issue`) 以返回 `IssueMetadata` 对象，而不是仅打印输出。
- [x] **定义 API 模型**: 在 `monoco.daemon.models` 中为 `CreateIssueRequest`, `UpdateIssueRequest`, 和 `IssueResponse` 创建 Pydantic 模型。
- [x] **实现端点**: 在 `monoco.daemon.app` 中添加 `POST`, `GET`, `PATCH`, `DELETE` 路由。
- [x] **添加测试**: 编写 `pytest` 测试用例以验证 API 端点和核心逻辑更改。