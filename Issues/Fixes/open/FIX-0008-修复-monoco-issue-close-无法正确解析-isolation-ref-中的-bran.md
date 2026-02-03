---
id: FIX-0008
uid: ff72a9
type: fix
status: open
stage: doing
title: '修复 monoco issue close 无法正确解析 isolation.ref 中的 branch: 前缀的问题'
created_at: '2026-02-03T09:52:32'
updated_at: '2026-02-03T09:52:47'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0008'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T09:52:32'
---

## FIX-0008: 修复 monoco issue close 无法正确解析 isolation.ref 中的 branch: 前缀的问题

## Objective
当 `monoco issue close` 处理 `isolation.ref` 时，如果前缀包含 `branch:` 或 `worktree:`，会导致 Git 无法找到物理分支而报错。本任务旨在修复该解析逻辑。

## Acceptance Criteria
- [ ] `monoco issue close` 能够正确识别并剥离 `isolation.ref` 中的 `branch:` 前缀。
- [ ] `FEAT-0160` 可以使用该指令正常关闭。

## Technical Tasks
- [ ] 调研 `monoco issue close` 的核心逻辑（通常在 `monoco/features/issue/cli.py` 或相关 core 模块中）。
- [ ] 修正 `isolation` 模型的解析或在 `close` 命令中进行预处理。
- [ ] 验证修复效果。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
