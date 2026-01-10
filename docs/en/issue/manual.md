# Monoco Issue System User Manual

The Monoco Issue System is a project management tool built on **"Agent-Native Semantics."** It treats work units as "Universal Atoms," aiming to reduce the translation overhead between human intent and agent execution.

This manual details the core concepts, workflow, and command-line usage of the Issue System.

## 1. Core Ontology

Monoco moves away from the traditional "User Narrative" model, defining work units based on "Mindsets" and "Direct Functionality."

### 1.1 Strategy Layer

#### 🏆 EPIC

- **Mindset**: Architect
- **Definition**: A grand objective spanning multiple cycles. It is a "container for vision."
- **Output**: Defines the system's boundaries and core value.
- **Prefix**: `EPIC-`

### 1.2 Value Layer

#### ✨ FEATURE

- **Mindset**: Product Owner / Lead Engineer
- **Definition**: A concrete functional unit of the system. Represents **Value Delivery**.
- **Focus**: "What" (What function is being added?).
- **Atomicity**: Feature = Design + Dev + Test. They are an inseparable whole.
- **Prefix**: `FEAT-`
  > _Note: Replaces the "Story" concept._

### 1.3 Execution Layer

#### 🧹 CHORE

- **Mindset**: Builder / Maintainer
- **Definition**: Engineering maintenance, refactoring, or tooling improvements. These **do not produce** direct user functional value but are strictly necessary for system health.
- **Scenarios**: Architecture upgrades, writing build scripts, fixing CI/CD pipelines, library updates.
- **Focus**: "How" (What must be done to support system operation).
- **Prefix**: `CHORE-`
  > _Note: Replaces the "Task" concept._

#### 🐛 FIX

- **Mindset**: Debugger
- **Definition**: A correction of a deviation between expectation and reality.
- **Focus**: "Repair" (Restore to intended state).
- **Prefix**: `FIX-`
  > _Note: Replaces the "Bug" concept._

### Relationship Chain

- **Primary**: `EPIC` (Vision) -> `FEATURE` (Value Delivery)
- **Secondary**: `CHORE` (Maintenance) - Valid as standalone technical work.
- **Scope**: Features deliver value; Chores maintain the factory; Fixes repair broken windows.

---

## 2. Command Reference

The Monoco Issue System strongly recommends using CLI tools to manage Issues to ensure synchronization between metadata and the file system.

### 2.1 Create

Create a new Issue. Automatically assigns the next available ID.

```bash
monoco issue create <type> --title "Title" [options]
```

- **Arguments**:
  - `<type>`: `epic`, `feature`, `chore`, `fix`
  - `--title, -t`: Title of the Issue.
  - `--parent, -p`: Parent Issue ID (e.g., linking a Feature to an Epic).
  - `--backlog`: Create directly in Backlog status (default is Open).
  - `--subdir, -s`: Specify a subdirectory (for organization, e.g., `Backend/Auth`).

**Example**:

```bash
monoco issue create feature --title "Implement User Login" --parent EPIC-001
```

### 2.2 Transition

#### Open

Move an Issue to `open` status.

```bash
monoco issue open <issue_id>
```

#### Backlog

Move an Issue to `backlog` status.

```bash
monoco issue backlog <issue_id>
```

#### Close

Complete or close an Issue.

```bash
monoco issue close <issue_id> [--solution <type>]
```

- **--solution**: Specify the reason for closing. Options:
  - `implemented` (Default)
  - `cancelled`
  - `wontfix`
  - `duplicate`

#### Cancel

Shortcut command, equivalent to `close --solution cancelled`.

```bash
monoco issue cancel <issue_id>
```

### 2.3 Scope

View the current project's Issue progress in a tree structure.

```bash
monoco issue scope [options]
```

- **--all, -a**: Show all Issues (including Closed and Backlog). Default only shows Open.
- **--sprint**: Filter by Sprint ID.
- **--recursive, -r**: Recursively scan subdirectories.

### 2.4 Lint

Verify the integrity of the `Issues/` directory. Checks for ID collisions, file location errors, broken links, etc.

```bash
monoco issue lint [--recursive]
```

---

## 3. Best Practices

### 3.1 Directory Structure

The Issue System adopts a **"Type-first, Status-second"** hierarchical storage strategy:

```text
Issues/
├── Epics/
│   ├── open/
│   └── closed/
├── Features/
│   ├── open/
│   └── ...
└── ...
```

### 3.2 Core Principles

1. **Prioritize CLI**: Avoid manually moving files to prevent inconsistencies between metadata (Frontmatter) and physical paths.
2. **Mandatory Validation**: If you manually edit a Markdown file, you **must** run `monoco issue lint` to ensure data integrity.
3. **Atomicity**: A Feature is the smallest unit of delivery. Do not split a Feature into separate Task files; related Design/Dev/Test tasks should be managed as a Checklist (`- [ ]`) within the Feature itself.

### 3.3 Template Specification

All Issue files must include the following Frontmatter:

```yaml
---
id: FEAT-0123
type: feature
status: open
title: "Feature Title"
created_at: YYYY-MM-DD
tags: [tag1]
---
```
