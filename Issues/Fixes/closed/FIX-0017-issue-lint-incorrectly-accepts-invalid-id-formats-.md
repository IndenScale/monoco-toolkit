---
id: FIX-0017
uid: 690a0e
type: fix
status: closed
stage: done
title: Issue lint 错误地接受了带后缀的无效 ID 格式
created_at: '2026-01-29T18:41:06'
updated_at: '2026-01-29T19:00:37'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0017'
files: []
opened_at: '2026-01-29T18:41:06'
closed_at: '2026-01-29T19:00:37'
solution: implemented
isolation:
  type: branch
  ref: feat/fix-0017-issue-lint-错误地接受了带后缀的无效-id-格式
  created_at: '2026-01-29T18:52:28'
---

## FIX-0017: Issue lint 错误地接受了带后缀的无效 ID 格式

## 目标 (Objective)

**Bug**: Issue lint 目前允许类似 `FEAT-0007~1`, `FEAT-0007~2` 这样带后缀的 ID，这违反了 Monoco ID 格式规范（应为 `TYPE-XXXX`，且必须是 4 位数字）。

**当前行为**: 运行 `monoco issue lint --fix` 时，linter 会为这些无效 ID 添加标签，而不是拒绝它们。

**预期行为**: Lint 应报告无效 ID 格式的错误（ERROR），并引导用户使用 `parent` 字段来建立父子关系，而不是通过 ID 命名约定来表达层级。

## 验收标准 (Acceptance Criteria)

- [x] Lint 拒绝带后缀（如 `~1`, `~2`, `~3`）的 ID（例如 `FEAT-0007~1`）
- [x] 错误消息清楚地说明正确的 ID 格式为：`TYPE-XXXX`（仅限 4 位数字）
- [x] 错误消息建议使用 `parent` 字段处理子功能/子任务
- [x] `--fix` 模式不会自动为无效 ID 添加标签
- [x] 所有现有的合法 ID 仍能通过 lint

## 技术任务 (Technical Tasks)

- [x] 更新 `monoco/issue/models.py` 中的 ID 验证正则，严格执行 4 位数字格式
- [x] 在验证逻辑中增加关于使用 `parent` 字段的引导性错误消息
- [x] 更新 lint logic，拒绝无效 ID 而不是尝试自动修复
- [x] 增加针对无效 ID 格式（FEAT-0007~1, FIX-0001~2等）的测试用例
- [x] 增加测试用例确保合法 ID 仍能通过
- [x] 修改文档，明确 ID 格式规则及 parent 字段的用法

## Review Comments

- [x] Self-Review: 验证了模型层的 Pydantic 校验和 Validator 层的正文引用分析。
- [x] 单元测试覆盖了非法后缀拒绝及合法 ID 通过的情景。
- [x] 文档已更新 (SKILL.md)。
