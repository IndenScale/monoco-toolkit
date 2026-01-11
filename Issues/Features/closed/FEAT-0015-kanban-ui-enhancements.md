---
id: FEAT-0015
type: feature
status: closed
stage: done
title: Kanban UI Enhancements
created_at: '2026-01-11T12:02:00.818615'
opened_at: '2026-01-11T12:02:00.818600'
updated_at: '2026-01-11T13:20:50.734671'
closed_at: '2026-01-11T13:20:50.734702'
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0015: Kanban UI Enhancements

## Objective

Enhance the Kanban Board experience by refining the "Overview" structure and introducing an "Issue Detail Modal". This improves visual hierarchy and allows quick context access without page navigation.

## Acceptance Criteria

1.  **Collapsible Stats Component**:
    - Separate the stats widgets into a standalone `StatsBoard` component.
    - User can toggle (expand/collapse) this section to save vertical space.
    - State is persisted (optional for now, but good UX).
2.  **Issue Detail Modal (UI)**:
    - Clicking an issue card opens a modal overlay instead of navigating away (or alongside).
    - Modal displays formatted Markdown content (Preview).
    - Modal includes an "Edit" button that toggles to a raw Markdown editor (Textarea/Monaco).
    - "Save" button is present but implementation is stubbed (delegated to FEAT-0016).

## Technical Tasks

- [x] **Refactor Stats**: Extract widgets from `page.tsx` into `components/StatsBoard.tsx`.
- [x] **Implement Modal**: Create `IssueDetailModal.tsx` using Blueprint `Dialog`.
- [x] **Markdown Rendering**: Integrate `react-markdown` or similar to render issue bodies in the modal.
- [x] **Editor UI**: Add a simple textarea/editor view for the "Edit" mode.
