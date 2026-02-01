---
id: FIX-0003
uid: bb2fdf
type: fix
status: open
stage: doing
title: Fix unit test regressions
created_at: '2026-02-01T22:05:08'
updated_at: '2026-02-01T22:05:32'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0003'
files: []
criticality: high
opened_at: '2026-02-01T22:05:08'
---

## FIX-0003: Fix unit test regressions

## Objective
Fix regressions in unit tests caused by recent changes and strict validation rules.

## Acceptance Criteria
- [x] All tests in `tests/features/issue/test_models.py` pass.
- [x] All tests in `tests/features/memo/test_memo_lifecycle.py` pass.
- [x] All tests in `tests/features/test_session.py` pass.
- [x] All tests in `tests/features/test_reliability.py` pass.

## Technical Tasks
- [x] Update IssueMetadata tests to respect strict stage validation (DRAFT vs TODO).
- [x] Fix Memo lifecycle tests to use object attribute access instead of dict access.
- [x] Isolate SessionManager tests using `tmp_path` to avoid environment pollution.

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
