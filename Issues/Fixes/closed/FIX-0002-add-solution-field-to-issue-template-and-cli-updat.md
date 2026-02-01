---
id: FIX-0002
uid: d5f310
type: fix
status: closed
stage: done
title: Add 'solution' field to Issue Template and CLI update command
created_at: '2026-02-01T21:42:30'
updated_at: '2026-02-01T21:49:52'
parent: EPIC-0030
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0030'
- '#FIX-0002'
files:
- monoco/features/issue/core.py
- monoco/features/issue/commands.py
criticality: high

opened_at: '2026-02-01T21:42:30'
closed_at: '2026-02-01T21:55:00'
solution: implemented

---

## FIX-0002: Add 'solution' field to Issue Template and CLI update command

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->
在 Issue 模版和 CLI update 命令中增加 `solution` 字段，以确保与 close 命令的一致性，并改进 Issue 生命周期管理。 (Add the `solution` field to Issue templates and CLI update command to ensure consistency with the close command and improve issue lifecycle management.)

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] Issue 模版包含带有帮助说明的 `solution` 字段
- [x] CLI `update` 命令支持 `--solution` 参数
- [x] Solution 字段正确序列化至 YAML frontmatter

## Technical Tasks

- [x] 在 `core.py` 的 `_serialize_metadata()` 中添加 `solution` 字段
- [x] 添加 YAML 注释以提供 solution 字段指引
- [x] 向 CLI `update` 命令添加 `--solution` 参数

## Review Comments
Fix completed. The solution field is now:
1. Included in new issue templates with a helpful comment showing valid values
2. Supported by the `monoco issue update` command via `--solution` parameter
