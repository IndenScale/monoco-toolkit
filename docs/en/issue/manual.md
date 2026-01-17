# Monoco Issue System User Manual

The Monoco Issue System is a project management tool built on **"Agent-Native Semantics"**.

This document focuses on the **CLI Usage Guide**. For core concepts and architecture, please refer to **[Core Concepts](concepts.md)**. For custom configuration, refer to **[Configuration Guide](configuration.md)**.

---

## 1. Basic Operations

### 1.1 Create

```bash
monoco issue create <type> --title "Title" [options]
```

- **Arguments**:
  - `<type>`: `epic`, `feature`, `chore`, `fix` (or custom types)
  - `--title, -t`: Title
  - `--parent, -p`: Parent ID (e.g. EPIC-001)
  - `--backlog`: Create directly in Backlog
  - `--subdir, -s`: Specify subdirectory

### 1.2 View

#### List View

```bash
monoco issue list [-s open] [-t feature]
```

#### Board View

Render a Kanban board in the terminal to visualize tasks across stages.

```bash
monoco issue board
```

#### Scope View

View the tree-like hierarchy of Issues.

```bash
monoco issue scope [--sprint SPRINT-ID] [--all]
```

#### Inspect

View metadata, available actions, and AST structure of an Issue.

```bash
monoco issue inspect <ID>
```

---

## 2. Lifecycle Management (Workflow)

Monoco's lifecycle is driven by **Transitions**.

### 2.1 Start

Move Issue from `Draft` to `Doing`. Supports setting up physical isolation environments.

```bash
# Basic Start
monoco issue start FEAT-101

# Start and Create Git Branch (Auto-checkout)
monoco issue start FEAT-101 --branch

# Start and Create Git Worktree (Recommended for parallel dev)
monoco issue start FEAT-101 --worktree
```

### 2.2 Submit & Review

```bash
# Submit for Review (Doing -> Review)
monoco issue submit FEAT-101

# Submit and Prune Resources (Delete branch/worktree)
monoco issue submit FEAT-101 --prune
```

### 2.3 Close

```bash
monoco issue close FEAT-101 --solution implemented
```

- **Solutions**: `implemented`, `wontfix`, `cancelled`, `duplicate` (Configurable)

### 2.4 Backlog Operations

```bash
# Push to Backlog (Status: Open -> Backlog)
monoco issue backlog push FEAT-101

# Pull from Backlog (Status: Backlog -> Open)
monoco issue backlog pull FEAT-101
```

---

## 3. Code Integration (Atomic Commit)

Monoco provides the `commit` command to ensure commits are linked to Issues.

```bash
# Linked Commit (Auto-appends 'Ref: ID' to msg)
monoco issue commit -m "Implement core logic" -i FEAT-101

# Auto-infer (If staged changes only involve the Issue file)
monoco issue commit -m "Update acceptance criteria" -i FEAT-101

# Detached Commit (Explicitly declare no Issue link)
monoco issue commit -m "Hotfix" --detached
```

---

## 4. Maintenance & Debugging

### Lint

Verify integrity of the `Issues/` directory (dead links, format errors, etc.).

```bash
monoco issue lint [--fix]
```

### Physical Move

Move an Issue to another project (preserves history, assigns new ID).

```bash
monoco issue move FEAT-101 --to ../OtherProject
```
