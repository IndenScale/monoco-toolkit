---
id: FIX-0018
uid: ca7afd
type: fix
status: closed
stage: done
title: Issue create command gives incorrect language hint
created_at: '2026-01-29T18:44:15'
updated_at: 2026-01-29 18:48:43
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0018'
files:
- monoco/features/issue/commands.py
- tests/features/issue/test_issue_hint_lang.py
opened_at: '2026-01-29T18:44:15'
closed_at: '2026-01-29T18:48:42'
solution: implemented
---

## FIX-0018: Issue create command gives incorrect language hint

## Objective

**Bug**: 当运行 `monoco issue create` 时，CLI 固化提示 "Agent Hint: Please fill the ticket content in English."。

**预期行为**: 该提示应尊重项目根目录 `monoco.yaml` 中的 `source_language` 设置。如果项目语言为 `zh`（如当前 Toolkit 项目），应提示使用中文。

## Acceptance Criteria

- [x] `issue create` 命令的 Hint 消息根据 `source_language` 动态调整。
- [x] 当项目语言为 `zh` 时，提示："Agent Hint: 请使用中文填写 Issue 内容。"。
- [x] 当项目语言为 `en` 时，提示："Agent Hint: Please fill the ticket content in English."。
- [x] 覆盖默认配置情况下的回退逻辑（默认为 English）。

## Technical Tasks

- [x] 在 `monoco/issue/cli.py` (或相关命令实现文件) 中定位 Hint 打印逻辑。
- [x] 注入配置加载器，获取当前项目的 `source_language`。
- [x] 实现简单的多语言消息映射。
- [x] 增加单元测试，验证不同语言配置下的输出。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
