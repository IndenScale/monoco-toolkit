# Workflow in Action (CLI Guide)

This guide explains how to use the Monoco CLI to manage Issues throughout their lifecycle.

## 1. Basic Operations

### 1.1 Create

```bash
monoco issue create <type> --title "Title" [options]
```

- **Arguments**:
  - `<type>`: `epic`, `feature`, `chore`, `fix` (or custom types)
  - `--title, -t`: Title
  - `--parent, -p`: Parent ID (e.g., EPIC-001)
  - `--backlog`: Create directly in Backlog

### 1.2 View

#### List View

```bash
monoco issue list [-s open] [-t feature]
```

#### Board View (Terminal Kanban)

```bash
monoco issue board
```

#### Scope View (Hierarchy)

```bash
monoco issue scope [--sprint SPRINT-ID] [--all]
```

---

## 2. Development Workflow

### 2.1 Start Working

Move an Issue from `Draft` to `Doing`. We recommend using `--branch` for isolation.

```bash
# Start and Create Git Branch (Auto-checkout)
monoco issue start FEAT-101 --branch
```

### 2.2 Syncing Context

While working, sync the files you've modified back to the Issue metadata.

```bash
monoco issue sync-files
```

### 2.3 Submitting for Review

```bash
# Submit and Prune Resources (Delete branch)
monoco issue submit FEAT-101
```

### 2.4 Closing

```bash
monoco issue close FEAT-101 --solution implemented
```

---

## 3. Maintenance

### Linting

Verify the integrity of the `Issues/` directory.

```bash
monoco issue lint [--fix]
```

---

[Previous: 02. Lifecycle Loop](./02_lifecycle.md) | \*\*Next: 04. Agent Integration](./04_agent_protocol.md)
