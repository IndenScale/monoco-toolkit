---
id: FIX-0005
uid: c4b656
type: fix
status: open
stage: review
title: Improve Issue StateMachine Error Messages
created_at: '2026-02-01T23:30:38'
updated_at: '2026-02-01T23:33:49'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0005'
files:
- monoco/features/issue/engine/machine.py
- tests/features/issue/test_statemachine_errors.py
criticality: high
opened_at: '2026-02-01T23:30:38'
---

## FIX-0005: Improve Issue StateMachine Error Messages

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->
Refactor `monoco/features/issue/engine/machine.py` to provide descriptive, actionable error messages when a transition fails. Currently, the error messages are generic and don't help users understand what went wrong or how to fix it.

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] When a transition is not found, the error message explains the current state and target state clearly
- [x] When a solution is missing or invalid, the error suggests valid solutions based on available workflows
- [x] Error messages include hints about available transitions from the current state
- [x] All error messages follow a consistent format: "Lifecycle Policy: {context}. {suggestion}"
- [x] Tests are added to verify all error message scenarios

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->

- [x] Refactor `validate_transition()` to provide descriptive error messages
  - [x] Extract error message generation into helper methods
  - [x] Add context about current state (status, stage) to error messages
  - [x] Add suggestions for valid solutions when solution is invalid/missing
  - [x] List available transitions from current state
- [x] Add comprehensive tests for error messages
  - [x] Test transition not found error
  - [x] Test invalid solution error with suggestions
  - [x] Test missing solution error with suggestions
  - [x] Test error message format consistency

## Implementation Summary

### Changes to `monoco/features/issue/engine/machine.py`

1. **Added helper methods for error message generation:**
   - `_format_state(status, stage)`: Formats state for display, handles Enum values
   - `_build_transition_not_found_error(...)`: Builds descriptive error when no transition exists
   - `_build_invalid_solution_error(...)`: Builds error when solution is invalid/missing
   - `get_available_solutions(...)`: Returns valid solutions for current state
   - `get_valid_transitions_from_state(...)`: Returns all valid transitions from a state

2. **Improved error messages:**
   - **Transition not found**: Now shows current state, target state, and lists all available transitions with their required solutions
   - **Invalid/missing solution**: Now shows the transition name, current/target states, and lists all valid solutions

### Example Error Messages

**Before:**
```
Lifecycle Policy: Transition from backlog(freezed) to open(review) is not defined.
```

**After:**
```
Lifecycle Policy: Transition from 'backlog(freezed)' to 'open(review)' is not defined. Available transitions from this state:
  - pull: 'backlog(freezed)' -> 'open(draft)'
  - cancel_backlog: 'backlog(freezed)' -> 'closed(done)' (requires --solution cancelled)
```

**Before:**
```
Lifecycle Policy: Transition 'Accept' requires solution 'implemented'.
```

**After:**
```
Lifecycle Policy: Transition 'Accept' from 'open(review)' to 'closed(done)' requires a solution. Valid solutions are: cancelled, implemented, wontfix.
```

## Review Comments

### Self-Review

- [x] Error messages are descriptive and actionable
- [x] All tests pass
- [x] Code follows existing patterns in the codebase
- [x] Helper methods are properly documented
