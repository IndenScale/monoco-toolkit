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

### Directory Structure

`Issues/{CapitalizedPluralType}/{lowercase_status}/`

- `{TYPE}`: `Epics`, `Features`, `Chores`, `Fixes`
- `{STATUS}`: `open`, `backlog`, `closed`

### Path Transitions

Use `monoco issue`:

1. **Create**: `monoco issue create <type> --title "..."`

   - Params: `--parent <id>`, `--dependency <id>`, `--related <id>`, `--sprint <id>`, `--tags <tag>`

2. **Transition**: `monoco issue open/close/backlog <id>`

3. **View**: `monoco issue scope`

4. **Validation**: `monoco issue lint`

5. **Modification**: `monoco issue start/submit/delete <id>`

6. **Commit**: `monoco issue commit` (Atomic commit for issue files)
