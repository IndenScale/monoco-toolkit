---
id: FEAT-0037
type: feature
status: closed
stage: done
title: CLI Advanced Issue Query
created_at: '2026-01-13T08:55:29.551568'
opened_at: '2026-01-13T08:55:29.551554'
updated_at: '2026-01-13T09:26:20.225208'
closed_at: '2026-01-13T09:26:20.225293'
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0037: CLI Advanced Issue Query

## Objective

在 CLI 中实现与 Web 端一致的高级过滤逻辑，使用户能够在终端环境中通过复杂查询（正向/反向关键词、逻辑与）快速定位 Issues，确保持续的“一次编写，到处查询”体验。

## Acceptance Criteria

- [ ] **新命令**: 实现 `monoco issue query <QUERY_STRING>` 命令。
- [ ] **查询语法**:
  - 支持 `term` (Nice to have / 评分项)。
  - 支持 `+term` (必须包含)。
  - 支持 `-term` (必须不包含)。
  - 支持 `"quoted phrase"` (短语匹配)。
  - 忽略大小写。
- [ ] **搜索范围**: 涵盖 ID, Title, Tags, Status, Stage。
- [ ] **结果展示**:
  - 默认以表格形式展示匹配的 Issues。
  - （可选）支持 `--tree` 视图以展示父子层级上下文（如匹配子任务时显示父 Epic）。

## Technical Tasks

- [x] 在 `monoco/features/issue/commands.py` 中注册 `query` 命令。
- [x] 实现 Python 版的 `parse_search_query` 逻辑 (Port from TS)。
- [x] 复用 `monoco.features.issue.core` 的 issue 加载逻辑。
- [x] 集成 `rich` 表格进行结果渲染。
