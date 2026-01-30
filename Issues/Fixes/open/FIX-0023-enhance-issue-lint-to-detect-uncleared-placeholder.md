---
id: FIX-0023
uid: a8daad
type: fix
status: open
stage: review
title: Enhance issue lint to detect uncleared placeholders
created_at: '2026-01-30T15:24:26'
updated_at: '2026-01-30T15:32:02'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0023'
files:
- monoco/features/issue/validator.py
criticality: high
opened_at: '2026-01-30T15:24:26'
isolation:
  type: branch
  ref: feat/fix-0023-enhance-issue-lint-to-detect-uncleared-placeholder
  created_at: '2026-01-30T15:30:57'
---

## FIX-0023: Enhance issue lint to detect uncleared placeholders

## Objective
改进 `monoco issue lint` 命令，使其能够识别并检查 Issue 模板中未清除或未替换的占位符（如 `<!-- ... Required for Review/Done stage... -->`），防止开发者提交包含默认指引内容的 Ticket，确保交付质量。

## Acceptance Criteria
- [x] `monoco issue lint` 能够识别常见的模板占位符（特别是包含 "Required for Review/Done" 等字样的 HTML 注释）。
- [x] 当 Issue 处于 `review` 或 `done` 阶段且包含此类占位符时，lint 检查应抛出 ERROR。
- [x] 在 `draft` 或 `open` 阶段，此类占位符应作为 WARNING 提示。
- [x] 确保检查逻辑不会误伤用户自定义的合法 HTML 注释。

## Technical Tasks
- [x] 调研并确定 Issue 模板中所有需要检查的占位符特征。
- [x] 在 `monoco/features/issue/validator.py` 中实现 `_validate_placeholders` 方法。
- [x] 为 Linter 添加基于阶段（stage）的错误/警告权重逻辑。
- [x] 验证实现能正确检测不同阶段下的占位符。


## Review Comments
- [x] 实现 `_validate_placeholders` 方法检测占位符
- [x] 验证 `review`/`done` 阶段抛出 ERROR，`draft`/`open` 阶段抛出 WARNING
- [x] 测试通过，功能正常工作
