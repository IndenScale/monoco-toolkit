---
name: atom-code-dev
description: Atomic operations for code development - research, implementation, testing, documentation
---

## Code Development Atomic Operations

Atomic operations for code development - research, implementation, testing, documentation

### System-level Compliance Rules

- Follow project code standards
- Prioritize writing tests (TDD mindset)
- Keep code simple and intuitive (KISS mindset)

### Operation Definitions

#### 1. Investigate
- **Description**: Understand requirements and context, identify relevant code and dependencies
- **Reminder**: Understand requirements before coding, identify relevant files and dependent Issues
- **Checkpoints**:
  - Read and understand Issue description
  - Identify relevant code files
  - Check dependent Issue status
  - Evaluate technical feasibility
- **Output**: Technical solution draft, risk list

#### 2. Implement
- **Description**: Implement code changes
- **Reminder**: Follow project code standards, commit in small steps, handle edge cases
- **Checkpoints**:
  - Follow project code standards
  - Write/update necessary documentation
  - Handle edge cases
  - Maintain code reviewability (single commit < 400 lines)

#### 3. Test
- **Description**: Run tests to ensure code quality
- **Reminder**: All tests must pass, check test coverage
- **Checkpoints**:
  - Write/update unit tests
  - Run test suite (pytest, cargo test, etc.)
  - Fix failed tests
  - Check test coverage
- **Compliance Rule**: All unit tests must pass before submission

#### 4. Document
- **Description**: Update documentation
- **Reminder**: Code changes must be accompanied by documentation updates
- **Checkpoints**:
  - Update code comments
  - Update related documentation
  - Update CHANGELOG (if applicable)
