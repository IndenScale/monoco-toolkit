---
id: FEAT-0020
type: feature
status: closed
stage: done
title: Engineering View
created_at: '2026-01-11T13:41:44.393544'
opened_at: '2026-01-11T13:41:44.393526'
updated_at: '2026-01-11T17:39:19.300854'
closed_at: '2026-01-11T17:39:19.300889'
parent: EPIC-0002
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0020: Engineering View

## Objective
To provide a comprehensive, hierarchical view of all issues, clustered by Epic, to facilitate engineering management and tracking. This view serves as a more accurate and structured alternative to the Kanban overview.

## Analysis: Necessity of Engineering View
While the Kanban Overview provides a process-centric view (Todo -> Doing -> Done), it lacks the structural context required for engineering planning and auditing.
- **Accuracy**: The list view provides a "source of truth" representation that reflects the hierarchical breakdown of work (Epic -> Feature -> Task). It allows engineers to see the "forest" (Epics) and the "trees" (Tasks) simultaneously, ensuring no task is lost in the process flow.
- **Structure**: By clustering issues by Epic, we can track the progress of larger initiatives rather than just individual tasks.
- **Density**: A table/tree view allows for displaying more metadata (ID, Type, Status, Created Date) in a compact form, suitable for scanning and auditing.

## Acceptance Criteria
1.  **Tree Structure Display**:
    - Issues must be clustered by their parent Epic.
    - Issues without a parent should be grouped separately or listed at the root level.
    - The hierarchy should be visually distinct (e.g., indentation).

2.  **Sorting Logic**:
    - Primary Sort: Group by Epic (Parent).
    - Secondary Sort: Within each group, sort by Issue Type (e.g., Feat, Fix, Chore).
    - Tertiary Sort: Within same type, sort by Issue ID (Number).

3.  **Visual Indicators**:
    - Use status-based coloring (e.g., Tags or row accents) to quickly identify issue state.

4.  **Interaction**:
    - Clicking on an issue row should open the Issue Detail Modal (shared with Overview).
    - Support expanding/collapsing Epic groups.

## Technical Tasks
- [ ] Refactor `IssueList` or `EngineeringView` to process flat issue list into a tree structure.
- [ ] Implement grouping logic based on `parent` field.
- [ ] Implement sorting logic (Epic -> Type -> ID).
- [ ] Update UI to render nested/grouped rows.
- [ ] Integrate `IssueDetailModal` for row click interactions.
