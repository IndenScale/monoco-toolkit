---
id: FEAT-0108
uid: 0bb83e
type: feature
status: closed
stage: done
title: 从 submit 命令中移除 prune 标志
created_at: '2026-01-26T00:01:40'
updated_at: 2026-01-26 00:13:11
parent: null
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0108'
files: []
opened_at: '2026-01-26T00:01:40'
closed_at: '2026-01-26T00:13:06'
solution: implemented
---

## FEAT-0108: 从 submit 命令中移除 prune 标志

## 目标 (Objective)

### 背景 (Why)
目前，`monoco issue submit` 包含用于删除分支/工作树的 `--prune` 和 `--force` 标志。这在语义上是不正确的，因为：

1. **提交 ≠ 完成**：`submit` 将 Issue 移动到评审 (Review) 阶段，而非完成。如果评审有反馈，可能需要进一步迭代。
2. **过早清理**：在评审通过之前删除工作环境会造成不必要的摩擦，并可能导致数据丢失。
3. **生命周期错位**：环境清理应发生在 Issue 生命周期的 **终点** (`close`)，而不是交接点 (`submit`)。

### 方案 (What)
从 `monoco issue submit` 命令中移除 `--prune` 和 `--force` 标志。环境清理应仅通过 `monoco issue close --prune` 提供。

## 验收标准 (Acceptance Criteria)

- [x] `monoco issue submit --help` 不再显示 `--prune` 或 `--force` 选项
- [x] `monoco issue close --help` 继续显示 `--prune` 和 `--force` 选项
- [x] 现有测试已更新以反映新行为
- [x] 文档 (GEMINI.md, CLI 帮助文本) 反映此更改

## 技术任务 (Technical Tasks)

- [x] 从 `submit` 命令定义中移除 `--prune` 和 `--force` 标志
  - [x] 更新 `monoco/features/issue/commands.py` - 从 `submit` 函数移除标志
  - [x] 从 `submit` 实现中移除分支/工作树清理逻辑
- [x] 验证 `close` 命令保留清理功能
  - [x] 确认 `--prune` 和 `--force` 标志存在于 `close` 命令中
  - [x] 测试清理行为正常工作
- [x] 更新测试
  - [x] 不存在 `submit --prune` 行为的测试 (通过 grep 验证)
  - [x] 现有工作流测试仍然通过
- [x] 更新文档
  - [x] `submit` 命令的 CLI 帮助文本自动更新
  - [x] 在 `Toolkit/GEMINI.md` 中添加关于正确清理时机的指导

## 评审备注 (Review Comments)
<!-- Required for Review/Done stage. Record review feedback here. -->
