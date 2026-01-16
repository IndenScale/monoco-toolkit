---
name: monoco-issue
description: Official skill for Monoco Issue System. Treats Issues as Universal Atoms, managing the lifecycle of Epic/Feature/Chore/Fix.
---

# Issue Management

Use this skill to create and manage **Issues** (Universal Atoms) in Monoco projects.

## Core Ontology

### 1. Strategy Layer

- **🏆 EPIC**: Grand goals, vision containers. Mindset: Architect.

### 2. Value Layer

- **✨ FEATURE**: Value increments from user perspective. Mindset: Product Owner.
- **Atomicity Principle**: Feature = Design + Dev + Test + Doc + i18n. They are one.

### 3. Execution Layer

- **🧹 CHORE**: Engineering maintenance, no direct user value. Mindset: Builder.
- **🐞 FIX**: Correcting deviations. Mindset: Debugger.

## Guidelines

### Directory Structure & Naming

`Issues/{CapitalizedPluralType}/{lowercase_status}/`

- **Types**: `Epics`, `Features`, `Chores`, `Fixes`
- **Statuses**: `open`, `backlog`, `closed`

### Structural Integrity

Issues are validated via `monoco issue lint`. key constraints:

1. **Mandatory Heading**: `## {ID}: {Title}` must match front matter.
2. **Min Checkboxes**: At least 2 checkboxes (AC/Tasks).
3. **Review Protocol**: `## Review Comments` required for `review` or `done` stages.

### Path Transitions

Use `monoco issue`:

1. **Create**: `monoco issue create <type> --title "..."`

   - Params: `--parent <id>`, `--dependency <id>`, `--related <id>`, `--sprint <id>`, `--tags <tag>`

2. **Transition**: `monoco issue open/close/backlog <id>`

3. **View**: `monoco issue scope`

4. **Validation**: `monoco issue lint`

5. **Modification**: `monoco issue start/submit/delete <id>`

6. **Commit**: `monoco issue commit` (Atomic commit for issue files)
7. **Validation**: `monoco issue lint` (Enforces compliance)

## Validation Rules (FEAT-0082)

To ensure data integrity, all Issue tickets must follow these strict rules:

### 1. Structural Consistency

- Must contain a Level 2 Heading matching exactly: `## {ID}: {Title}`.
- Example: `## FEAT-0082: Issue Ticket Validator`

### 2. Content Completeness

- **Checkboxes**: Minimum of 2 checkboxes required (one for AC, one for Tasks).
- **Review Comments**: If `stage` is `review` or `done`, a `## Review Comments` section is mandatory and must not be empty.

### 3. Checkbox Syntax & Hierarchy

- Use only `- [ ]`, `- [x]`, `- [-]`, or `- [/]`.
- **Inheritance**: If nested checkboxes exist, the parent state must reflect child states (e.g., if any child is `[/]`, parent must be `[/]`; if all children are `[x]`, parent must be `[x]`).

### 4. State Matrix

The `status` (folder) and `stage` (front matter) must be compatible:

- **open**: Draft, Doing, Review, Done
- **backlog**: Draft, Doing, Review
- **closed**: Done
