# Monoco Issue Configuration Guide

The Monoco Issue System is highly configurable. By defining configurations in `.monoco/workspace.yaml` or `.monoco/project.yaml`, you can completely control Issue types, statuses, stages, and transition rules.

## Configuration Structure

Configuration is located under the `issue` node.

```yaml
issue:
  types: [...] # Define Issue Types
  statuses: [...] # Define Physical Statuses
  stages: [...] # Define Logical Stages
  solutions: [...] # Define Solutions for Closing
  workflows: [...] # Define Transition Rules
```

## 1. Issue Types

Define the types of Issues that exist in the system.

```yaml
types:
  - name: feature # Internal ID (lowercase)
    label: Feature # Display Name
    prefix: FEAT # ID Prefix (e.g. FEAT-001)
    folder: Features # Storage Directory Name
    description: "..." # Description
```

## 2. Status & Schema

Define the vocabulary of the state machine.

```yaml
# Physical Statuses (Modification usually not recommended as it involves file structure)
statuses:
  - open
  - closed
  - backlog

# Logical Stages (Define freely)
stages:
  - draft
  - doing
  - review
  - done
  - freezed

# Solutions (For Close action)
solutions:
  - implemented
  - cancelled
  - wontfix
  - duplicate
```

## 3. Global Workflows

Define the state transition matrix. Each item represents an executable Action.

```yaml
workflows:
  - name: start # Action ID
    label: Start # UI Display Label
    icon: "$(play)" # UI Icon (VS Code codicons)

    # --- Triggers ---
    from_status: open # Only available in open status
    from_stage: draft # Only available in draft stage

    # --- Targets ---
    to_status: open # Stays in open status
    to_stage: doing # Changes to doing stage

    # --- Side Effects ---
    command_template: "monoco issue start {id}" # Executed CLI command
    description: "Start working on the issue"

  - name: close_done
    label: Close
    icon: "$(close)"
    from_status: open
    from_stage: done
    to_status: closed
    to_stage: done
    required_solution: implemented # This action requires solution=implemented
```

### Field Recommendations

- **Status/Stage**: If changing state via Action, `to_status` and `to_stage` must be explicitly specified.
- **Universal Actions**: If `from_status` and `from_stage` are empty, the action is visible in any state (usually used for triggering Agent tasks, e.g., "Investigate").

## Default Configuration Reference

Monoco comes with a standard development flow configuration built-in. You can view the full defaults in `monoco/features/issue/engine/config.py` or override it directly in `workspace.yaml`.
