---
name: atom-review
description: Atomic operations for code review - checkout, verify, challenge, feedback
---

## Code Review Atomic Operations

Atomic operations for code review - checkout, verify, challenge, feedback

### System-level Compliance Rules

- Must pass Engineer's tests (Verify) first, then conduct adversarial testing (Challenge)
- Must attempt to write at least one edge case test
- Prohibited from direct Approve without testing

### Operation Definitions

#### 1. Checkout
- **Description**: Check out the code to be reviewed
- **Reminder**: Get the PR/Branch to be reviewed, confirm differences from Base branch
- **Checkpoints**:
  - Check out PR/Branch
  - Confirm differences from Base branch
  - Check environment configuration

#### 2. Verify
- **Description**: Verify Engineer's submitted tests (White-box)
- **Reminder**: Run Engineer's tests first to verify functional correctness
- **Checkpoints**:
  - Run Engineer's unit tests
  - Run integration tests (if applicable)
  - Check test coverage report
- **Compliance Rule**: If existing tests fail, directly enter Reject flow

#### 3. Challenge
- **Description**: Adversarial testing, try to break the code (Black-box / Edge Cases)
- **Reminder**: Try to break it - look for edge cases and security vulnerabilities
- **Checkpoints**:
  - Analyze code logic, find blind spots (concurrency, large/small values, injection attacks, etc.)
  - Write new Challenge Test Cases
  - Run these new tests
- **Compliance Rule**: Must attempt to write at least one edge case test

#### 4. Feedback
- **Description**: Provide review feedback
- **Reminder**: Clearly approve, reject, or request changes, provide specific feedback
- **Checkpoints**:
  - Is functionality correctly implemented
  - Does code meet design specifications
  - Are tests sufficient
  - Is documentation updated
  - Does it follow project specifications
