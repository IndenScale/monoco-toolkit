---
name: monoco_workflow_agent_engineer
description: Standardized workflow for the Engineer role (Flow Skill). Defines the standard operating procedure from requirement investigation to code submission, ensuring test coverage and code quality.
type: workflow
role: engineer
version: 1.0.0
---

# Engineer Flow

Standardized workflow for the Engineer role, ensuring code development follows the "Investigate → Code → Test → Report → Submit" process.

## Workflow State Machine

```mermaid
stateDiagram-v2
    [*] --> Investigate: Receive Task
    
    Investigate --> Code: Requirements Clear
    Investigate --> Investigate: Requirements Fuzzy<br/>(Request Clarification)
    
    Code --> Test: Coding Complete
    
    Test --> Test: Test Failed<br/>(Fix Code)
    Test --> Report: Test Passed
    
    Report --> Submit: Report Complete
    
    Submit --> [*]: Submission Successful
```

## Execution Steps

### 1. Investigate

- **Goal**: Fully understand requirements, identify technical risks and dependencies
- **Input**: Issue description, relevant code, dependent Issues
- **Output**: Technical solution draft, risk checklist
- **Checkpoints**:
  - [ ] Read and understand Issue description
  - [ ] Identify relevant code files
  - [ ] Check dependent Issue status
  - [ ] Assess technical feasibility

### 2. Code

- **Goal**: Implement feature or fix defect
- **Prerequisites**: Requirements are clear, branch is created (`monoco issue start <ID> --branch`)
- **Checkpoints**:
  - [ ] Follow project coding standards
  - [ ] Write/update necessary documentation
  - [ ] Handle edge cases

### 3. Test

- **Goal**: Ensure code quality and functional correctness
- **Strategy**: Loop testing until passed
- **Checkpoints**:
  - [ ] Write/update unit tests
  - [ ] Run test suite (`pytest`, `cargo test`, etc.)
  - [ ] Fix failed tests
  - [ ] Check test coverage

### 4. Report

- **Goal**: Document changes, update Issue status
- **Checkpoints**:
  - [ ] Update Issue file tracking (`monoco issue sync-files`)
  - [ ] Write change summary
  - [ ] Update task checklist (Checkboxes)

### 5. Submit

- **Goal**: Complete code submission, enter review process
- **Checkpoints**:
  - [ ] Run `monoco issue lint` for compliance check
  - [ ] Run `monoco issue submit <ID>`
  - [ ] Wait for review results

## Decision Branches

| Condition | Action |
|-----------|--------|
| Requirements unclear | Return to Investigate, request clarification |
| Test failed | Return to Code, fix issues |
| Lint failed | Fix compliance issues, resubmit |
| Review rejected | Return to Code, modify according to feedback |

## Compliance Requirements

- **Prohibited**: Skip tests and submit directly
- **Prohibited**: Modify code directly on main/master branch
- **Required**: Use `monoco issue start --branch` to create feature branch
- **Required**: All unit tests must pass before Submit
