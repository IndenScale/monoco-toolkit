# Monoco Issue Configuration Guide

The Monoco Issue System is highly configurable. By defining configurations in `.monoco/workspace.yaml` or `.monoco/project.yaml`, you can fully control Issue types, statuses, stages, and transition rules.

## Configuration Structure

Configuration resides under the `issue` node.

```yaml
issue:
  types: [...] # Define Issue types
  statuses: [...] # Define physical statuses
  stages: [...] # Define logical stages
  solutions: [...] # Define solutions for closing
  workflows: [...] # Define state transition rules
```

## 1. Issue Types

Define the kinds of Issues that exist in the system.

```yaml
types:
  - name: feature # Internal ID (lowercase)
    label: Feature # Display Name
    prefix: FEAT # ID Prefix (e.g., FEAT-001)
    folder: Features # Storage directory name
    description: "..."
```

## 2. Status & Schema

Define the vocabulary of the state machine.

```yaml
# Physical Status (Modification not recommended as it affects filesystem structure)
statuses:
  - open
  - closed
  - backlog

# Logical Stages (Freely definable)
stages:
  - draft
  - doing
  - review
  - done
  - freezed

# Solutions (Used for the Close action)
solutions:
  - implemented
  - cancelled
  - wontfix
  - duplicate
```

## 3. Workflows (Global Actions)

Define the state transition matrix. Each entry represents an executable **Action**.

```yaml
workflows:
  - name: start # Action ID
    label: Start # UI Label
    icon: "$(play)" # UI Icon (VS Code codicons)

    # --- Trigger Conditions ---
    from_status: open
    from_stage: draft

    # --- Target State ---
    to_status: open
    to_stage: doing

    # --- Side Effects ---
    command_template: "monoco issue start {id}"
    description: "Start working on the issue"
```

---

[Previous: 04. Agent Integration](./04_agent_protocol.md) | \*\*Next: 06. Query Syntax](./06_query_syntax.md)
