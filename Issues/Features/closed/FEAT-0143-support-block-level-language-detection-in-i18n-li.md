---
id: FEAT-0143
uid: '880488'
type: feature
status: closed
stage: done
title: Support Block-Level Language Detection in i18n Linter
created_at: '2026-02-01T20:56:51'
updated_at: '2026-02-02T12:20:52'
parent: EPIC-0029
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0029'
- '#FEAT-0143'
files:
- monoco/features/i18n/core.py
- monoco/features/issue/validator.py
- tests/features/i18n/test_block_level_language_detection.py
criticality: medium
solution: implemented
opened_at: '2026-02-01T20:56:51'
closed_at: '2026-02-02T12:20:52'
---

## FEAT-0143: Support Block-Level Language Detection in i18n Linter

## 背景与目标

本功能旨在增强 i18n linter 的语言检测能力，支持块级检测以避免混合语言文件中的误报。当前 linter 可能将中文文档中的英文内容（如代码块、英文评审备注）误判为"未翻译"或"语言错误"。需要尊重块边界（如段落、代码块、标题章节）进行语言检测，确保评审备注章节中的英文文本不会被错误地标记为问题，同时正确处理代码块的语言检测策略。

## Objective
Enhance the i18n linter to support block-level language detection to avoid false positives in mixed-language Markdown files.

**Context**:
- Currently, the linter may flag English content within Chinese documents (e.g., code blocks, English review comments in a Chinese Issue) as "untranslated" or "wrong language".
- Need to respect block boundaries (e.g., `Review Comments` section, code blocks) during language detection.

## Acceptance Criteria
- [x] Linter correctly identifies language at the block level (e.g., paragraph, code block, header section).
- [x] Code blocks are ignored for language checks (they always contain English keywords).
- [x] Technical terms are properly handled and don't cause false positives.
- [x] Narrative text in all sections (including Review Comments) should be in Chinese; English should only appear as isolated nouns (technical terms, filenames).

## Technical Tasks
- [x] Refactor `monoco/features/i18n/core.py` to parse Markdown blocks.
- [x] Implement block-scoped language detection logic.
- [x] Add unit tests for mixed-language scenarios.

## Review Comments

### 2026-02-02 归属调整

**变更**: Parent 从 EPIC-0000 调整为 EPIC-0029 (Knowledge Engine & Memory System)

**理由**: i18n Linter 属于文档生态系统 (Documentation Ecosystem)，是 EPIC-0029 中 "多语言文档国际化" 目标的一部分。
