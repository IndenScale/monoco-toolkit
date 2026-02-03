---
name: atom-knowledge
description: Atomic operations for knowledge management - capture, process, convert, archive
---

## Knowledge Management Atomic Operations

Atomic operations for knowledge management - capture, process, convert, archive

### System-level Compliance Rules

- Memos are temporary and should not accumulate indefinitely
- Actionable ideas must be converted to Issue tracking

### Operation Definitions

#### 1. Capture
- **Description**: Quickly capture fleeting ideas
- **Command**: `monoco memo add <content>`
- **Reminder**: Keep it concise, don't interrupt current workflow, add context
- **Checkpoints**:
  - Use concise descriptions
  - Add context (-c file:line if applicable)
  - Don't interrupt current task flow

#### 2. Process
- **Description**: Regularly process Memos, evaluate value
- **Command**: `monoco memo list`
- **Reminder**: Regularly review and categorize Memos (recommended weekly)
- **Checkpoints**:
  - Run monoco memo list to view all Memos
  - Evaluate value of each Memo
  - Categorize: actionable / reference only / no value

#### 3. Convert
- **Description**: Convert actionable Memos to Issues
- **Command**: `monoco issue create <type> -t <title>`
- **Reminder**: Convert valuable ideas to Issues quickly
- **Checkpoints**:
  - Determine Issue type (feature/chore/fix)
  - Write clear description and acceptance criteria
  - Link to original Memo
- **Compliance Rule**: Actionable ideas must be converted to Issue tracking

#### 4. Archive
- **Description**: Archive pure reference materials
- **Reminder**: Archive pure reference materials, delete worthless ones directly
- **Checkpoints**:
  - Confirm Memo content is pure reference material
  - Move to knowledge base or documentation
  - Remove from Memo list
