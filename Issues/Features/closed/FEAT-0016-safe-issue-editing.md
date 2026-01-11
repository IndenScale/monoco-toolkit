---
id: FEAT-0016
type: feature
status: closed
stage: done
title: Safe Issue Editing
created_at: '2026-01-11T12:02:01.293307'
opened_at: '2026-01-11T12:02:01.293293'
updated_at: '2026-01-11T13:20:52.819608'
closed_at: '2026-01-11T13:20:52.819640'
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0016: Safe Issue Editing

## Objective

Implement a robust issue editing mechanism that ensures data integrity. User edits via the UI should only be persisted if they pass the strict `monoco issue lint` validation rules. If validation fails, changes must be rolled back (or rejected with error).

## Acceptance Criteria

1.  **Backend Edit API**:
    - `PATCH /api/v1/issues/{id}/content` (or similar) to accept raw Markdown content.
    - API must write content to a temporary location or in-memory, then run validation.
2.  **Lint Validation**:
    - Invoke `monoco.features.issue.lint.validate_issue(path)` or equivalent.
    - If valid: Swap/Overwrite original file.
    - If invalid: Return 400 with specific lint errors.
3.  **Frontend Integration**:
    - "Save" button in the Modal (from FEAT-0015) sends content to this API.
    - Displays Success toast or Error alerts based on response.

## Technical Tasks

- [x] **API Endpoint**: Implement content update endpoint in Daemon.
- [x] **Validator Integration**: Reuse existing lint logic from CLI.
- [x] **Frontend Wiring**: Connect FEAT-0015 UI to this API.
