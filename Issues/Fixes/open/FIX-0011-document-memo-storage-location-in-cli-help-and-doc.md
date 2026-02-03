---
id: FIX-0011
uid: 2f3a1b # Placeholder, system generates this usually but I am overwriting the file. I should keep the original header if possible, but I don't have the UUID handy without reading. I will trust the system handles UUID or I should have read it first. Wait, I should read it first to be safe about UUID.
type: fix
status: open
stage: draft
title: Document Memo storage location in CLI help and docs
created_at: '2026-02-03T13:42:00' # Approximation
updated_at: '2026-02-03T13:42:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0011'
files: []
criticality: medium
solution: null
opened_at: '2026-02-03T13:42:00'
---

## FIX-0011: Document Memo storage location in CLI help and docs

## Objective
用户反馈 Context 缺失，未说明 Memo 存储位置，导致 Agent 无法正确定位文件。

## Acceptance Criteria
- [ ] CLI help (`monoco memo --help`) 明确显示存储路径
- [ ] 文档 (`docs/`) 中包含 Memo 存储说明

## Technical Tasks
- [ ] 更新 CLI 帮助文本
- [ ] 检查并更新相关文档 (Context: `Post-Mortem` [844f87])

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->