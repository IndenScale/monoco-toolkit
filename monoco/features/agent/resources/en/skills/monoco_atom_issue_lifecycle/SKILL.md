---
name: atom-issue-lifecycle
description: Atomic operations for Issue lifecycle management - create, start, submit, close work units
---

## Issue Lifecycle Management Atomic Operations

Atomic operations for Issue lifecycle management - create, start, submit, close work units

### System-level Compliance Rules

- Prohibited from directly modifying code on main/master branch
- Must use feature branch for development
- Must pass lint check before submission
- Each Issue must contain at least 2 Checkboxes
- Review/Done phase must contain Review Comments

### Operation Definitions

#### 1. Create

- **Description**: Create a new Issue work unit
- **Command**: `monoco issue create <type> -t <title>`
- **Reminder**: Choose appropriate type (epic/feature/chore/fix), write clear description
- **Checkpoints**:
  - Must contain at least 2 Checkboxes
  - Title must match Front Matter

#### 2. Start

- **Description**: Start development, create feature branch
- **Command**: `monoco issue start <ID> --branch`
- **Reminder**: Ensure use --branch to create feature branch, prohibited from developing on main/master
- **Checkpoints**:
  - Prohibited from directly modifying code on main/master branch
  - Must create feature branch

#### 3. Sync

- **Description**: Sync file tracking, record modified files
- **Command**: `monoco issue sync-files`
- **Reminder**: Regularly sync file tracking, keep Issue in sync with code changes

#### 4. Lint

- **Description**: Check Issue compliance
- **Command**: `monoco issue lint`
- **Reminder**: Must run lint check before submission
- **Checkpoints**:
  - Must pass all compliance checks

#### 5. Submit

- **Description**: Submit code for review
- **Command**: `monoco issue submit <ID>`
- **Reminder**: Ensure all tests pass, no lint errors before submitting
- **Checkpoints**:
  - All unit tests must pass
  - Must pass lint check

#### 6. Close

- **Description**: Close Issue, clean up environment
- **Command**: `monoco issue close <ID> --solution completed `
- **Reminder**: Close Issue promptly after code merge, clean up feature branch
