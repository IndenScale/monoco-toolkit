---
id: FEAT-0165
uid: c8e92a
type: feature
status: open
stage: draft
title: Enhance Issue CLI and Templates for Smoother Lifecycle Management
created_at: '2026-02-03T13:43:00'
updated_at: '2026-02-03T13:43:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0165'
files: []
criticality: medium
solution: null
opened_at: '2026-02-03T13:43:00'
---

## FEAT-0165: Enhance Issue CLI and Templates for Smoother Lifecycle Management

## Objective
优化 Issue 生命周期管理的 DevEx，解决 CLI 闭环困难和模版缺失字段的问题。
(Context: `UX Feedback` [325b48], `DevEx` [0c262b])

## Acceptance Criteria
- [ ] `monoco issue update` 支持 `--solution` 参数
- [ ] Issue Markdown 模版 Front Matter 包含 `solution: null` 默认值
- [ ] CLI 报错信息明确指导如何解决

## Technical Tasks
- [ ] 修改 `IssueTemplate` 生成逻辑，添加 `solution` 字段
- [ ] 更新 `monoco issue update` 命令参数定义，支持 `--solution`
- [ ] 验证通过 CLI 完成 `open` -> `close` 闭环流程

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
