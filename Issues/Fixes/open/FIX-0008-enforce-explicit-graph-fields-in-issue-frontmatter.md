---
id: FIX-0008
uid: 982be8
type: fix
status: open
stage: review
title: Enforce Explicit Graph Fields in Issue Frontmatter
created_at: '2026-01-25T14:27:24'
opened_at: '2026-01-25T14:27:24'
updated_at: '2026-01-25T14:32:07'
isolation:
  type: branch
  ref: feat/fix-0008-enforce-explicit-graph-fields-in-issue-frontmatter
  created_at: '2026-01-25T14:27:53'
parent: null
dependencies: []
related: []
domains: []
tags:
- '#FIX-0008'
files:
- monoco/features/issue/domain/models.py
---

## FIX-0008: Enforce Explicit Graph Fields in Issue Frontmatter

## Objective
修复 `IssueFrontmatter` 定义过于宽容的问题。`parent`, `dependencies`, `related` 等图字段目前在 Pydantic 模型中拥有默认值 (`None` 或 `[]`)，导致 YAML Frontmatter 中可以完全省略这些 Key。

为了强制用户（和 Agent）显式思考 Issues 之间的关联，我们需要强制这些字段在 Frontmatter 中必须存在（Explicity over Implicity），即使值为 `null` 或空列表。

## Acceptance Criteria
- [ ] `parent` 字段必须在 Front Matter 中存在（允许为 `null`）。
- [ ] `dependencies` 字段必须在 Front Matter 中存在（允许为 `[]`）。
- [ ] `related` 字段必须在 Front Matter 中存在（允许为 `[]`）。
- [ ] 现有的 `monoco issue lint` 能够检测出缺少这些 Key 的 Issue 并报错。

## Technical Tasks
- [x] 修改 `monoco/features/issue/domain/models.py`:
    - [x] 移除 `parent` 的默认值。
    - [x] 移除 `dependencies` 的默认值。
    - [x] 移除 `related` 的默认值。
- [x] 验证：运行 `monoco issue lint` 扫描当前 Issue 库，确认检测到违规文件。
- [x] 修复：更新所有现有 Issue 文件，补全缺失的字段。

## Review Comments
- **2026-01-25 Agent**: 已完成 Schema 的严格化修改。
  - 修改了 `monoco/features/issue/core.py` 允许 `parse_issue` 抛出错误。
  - 修改了 `monoco/features/issue/linter.py` 捕获并报告 Schema 错误。
  - 修复了 FEAT-0102, FEAT-0103, FEAT-0104 的 Frontmatter 缺失字段。
  - 验证了 `issue lint` 现在可以正确拦截 Schema 违规。
