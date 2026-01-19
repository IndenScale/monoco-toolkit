---
id: FEAT-0016
type: feature
status: closed
stage: done
title: 安全 Issue 编辑 (Safe Issue Editing)
created_at: '2026-01-11T12:02:01.293307'
opened_at: '2026-01-11T12:02:01.293307'
updated_at: '2026-01-11T13:20:52.819608'
closed_at: '2026-01-11T13:20:52.819640'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0003'
- '#FEAT-0016'
parent: EPIC-0003
uid: 88a412
---

## FEAT-0016: 安全 Issue 编辑 (Safe Issue Editing)

## 目标 (Objective)

实现健壮的 Issue 编辑机制，确保数据完整性。用户通过 UI 进行的编辑只有在通过严格的 `monoco issue lint` 验证规则后才应持久化。如果验证失败，必须回滚更改（或通过错误拒绝）。

## 验收标准 (Acceptance Criteria)

1.  **后端编辑 API (Backend Edit API)**:
    - `PATCH /api/v1/issues/{id}/content` (或类似) 接收原始 Markdown 内容。
    - API 必须将内容写入临时位置或内存，然后运行验证。
2.  **Lint 验证 (Lint Validation)**:
    - 调用 `monoco.features.issue.lint.validate_issue(path)` 或等效项。
    - 如果有效: 交换/覆盖原始文件。
    - 如果无效: 返回 400 和具体的 lint 错误。
3.  **前端集成 (Frontend Integration)**:
    - 模态框中的“保存”按钮（来自 FEAT-0015）将内容发送到此 API。
    - 根据响应显示成功提示或错误警报。

## 技术任务 (Technical Tasks)

- [x] **API 端点**: 在 Daemon 中实现内容更新端点。
- [x] **验证器集成**: 重用 CLI 中现有的 lint 逻辑。
- [x] **前端连线**: 将 FEAT-0015 UI 连接到此 API。

## Review Comments

- [x] Self-Review
