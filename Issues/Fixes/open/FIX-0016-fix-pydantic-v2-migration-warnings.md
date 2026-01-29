---
id: FIX-0016
uid: 8760f5
type: fix
status: open
stage: review
title: Fix Pydantic V2 migration warnings
created_at: '2026-01-29T16:53:41'
updated_at: '2026-01-29T16:58:44'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0016'
files: []
opened_at: '2026-01-29T16:53:41'
isolation:
  type: branch
  ref: feat/fix-0016-fix-pydantic-v2-migration-warnings
  created_at: '2026-01-29T16:53:48'
---

## FIX-0016: Fix Pydantic V2 migration warnings

## Objective
Remove Pydantic V2 warnings during pytest execution in Toolkit.
Key warnings to fix:
1. `PydanticDeprecatedSince20`: Class-based config in `Session` model.
2. `PydanticSerializationUnexpectedValue`: Enum serialization warnings for `IssueMetadata`.

## Acceptance Criteria
- [x] All Pydantic warnings are resolved when running `pytest`.
- [x] No regressions in tests.

## Technical Tasks

- [x] Replace `class Config` with `model_config = ConfigDict(...)` in `monoco/features/scheduler/session.py`.
- [x] Force Enum coercion in `IssueMetadata.normalize_fields` to prevent `PydanticSerializationUnexpectedValue` warnings.
- [x] Enable `validate_assignment=True` in `IssueMetadata` model config.

## Review Comments
- Verified that warnings are gone locally.
- Verified that `repro_warning.py` behaves correctly.
