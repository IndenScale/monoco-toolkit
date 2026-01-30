---
id: FIX-0023
uid: a8daad
type: fix
status: open
stage: doing
title: Enhance issue lint to detect uncleared placeholders
created_at: '2026-01-30T15:24:26'
updated_at: '2026-01-30T15:30:57'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0023'
files: []
criticality: high
opened_at: '2026-01-30T15:24:26'
---

## FIX-0023: Enhance issue lint to detect uncleared placeholders

## Objective
改进 `monoco issue lint` 命令，使其能够识别并检查 Issue 模板中未清除或未替换的占位符（如 `<!-- ... Required for Review/Done stage... -->`），防止开发者提交包含默认指引内容的 Ticket，确保交付质量。

## Acceptance Criteria
- [ ] `monoco issue lint` 能够识别常见的模板占位符（特别是包含 "Required for Review/Done" 等字样的 HTML 注释）。
- [ ] 当 Issue 处于 `review` 或 `done` 阶段且包含此类占位符时，lint 检查应抛出 ERROR。
- [ ] 在 `draft` 或 `open` 阶段，此类占位符应作为 WARNING 提示。
- [ ] 确保检查逻辑不会误伤用户自定义的合法 HTML 注释。

## Technical Tasks
- [ ] 调研并确定 Issue 模板中所有需要检查的占位符特征。
- [ ] 在 `monoco/features/issue/linter.py` 中实现占位符扫描引擎。
- [ ] 为 Linter 添加基于阶段（stage）的错误/警告权重逻辑。
- [ ] 编写测试用例验证不同阶段下的占位符检测行为。


## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
