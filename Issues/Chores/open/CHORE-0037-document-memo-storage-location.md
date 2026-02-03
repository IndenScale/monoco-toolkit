---
id: CHORE-0037
uid: 3d3610
type: chore
status: open
stage: draft
title: Document Memo Storage Location
created_at: '2026-02-03T20:45:02'
updated_at: '2026-02-03T20:45:02'
parent: EPIC-0000
dependencies: []
related: []
domains:
- Documentation
tags:
- '#CHORE-0037'
- '#EPIC-0000'
files:
- GEMINI.md
- docs/zh/
criticality: low
solution: null
opened_at: '2026-02-03T20:45:02'
---

## CHORE-0037: Document Memo Storage Location

## Objective
补充文档中关于 Memo 存储位置的说明。目前文档中未明确指出 Memo 存储在 `Memos/` 目录（及 `Memos/inbox.md`），导致 Agent 在执行相关任务时可能无法正确定位文件。

## Acceptance Criteria
- [ ] `GEMINI.md` 或相关核心文档中明确说明 Memo 的存储路径规则。
- [ ] 确保 Agent 的 Context File (如 `GEMINI.md`) 包含此信息。

## Technical Tasks
- [ ] 更新 `GEMINI.md` 中的 Memo 章节，注明默认存储路径。
- [ ] 检查并更新 `monoco-toolkit/GEMINI.md` (如果适用)。

## Review Comments