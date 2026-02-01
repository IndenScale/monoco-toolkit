---
id: FEAT-0143
uid: '880488'
type: feature
status: open
stage: draft
title: Support Block-Level Language Detection in i18n Linter
created_at: '2026-02-01T20:56:51'
updated_at: '2026-02-01T20:56:51'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0143'
files: []
criticality: medium
opened_at: '2026-02-01T20:56:51'
---

## FEAT-0143: Support Block-Level Language Detection in i18n Linter

## Objective
Enhance the i18n linter to support block-level language detection to avoid false positives in mixed-language Markdown files.

**Context**:
- Currently, the linter may flag English content within Chinese documents (e.g., code blocks, English review comments in a Chinese Issue) as "untranslated" or "wrong language".
- Need to respect block boundaries (e.g., `Review Comments` section, code blocks) during language detection.

## Acceptance Criteria
- [ ] Linter correctly identifies language at the block level (e.g., paragraph, code block, header section).
- [ ] English text in `Review Comments` section of a Chinese Issue is NOT flagged as an error.
- [ ] Code blocks are ignored or handled appropriate for language checks.

## Technical Tasks
- [ ] Refactor `monoco/features/i18n/linter.py` (or equivalent) to parse Markdown AST.
- [ ] Implement block-scoped language detection logic.
- [ ] Add unit tests for mixed-language scenarios.

## Review Comments
