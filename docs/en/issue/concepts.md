# Monoco Issue Core Concepts

This document defines the semantic model of Monoco Issue System, including Issue taxonomy, state machine, and relationships.

## 1. Taxonomy

Monoco defines work units based on "Mindset" rather than pure user narrative.

### 1.1 Strategy Layer

#### 🏆 EPIC

- **Prefix**: `EPIC-`
- **Mindset**: Architect
- **Definition**: Grand goal spanning multiple cycles, acting as a "Container of Vision". Usually contains multiple Features.
- **Output**: Defines system boundaries and core values.

### 1.2 Value Layer

#### ✨ FEATURE

- **Prefix**: `FEAT-`
- **Mindset**: Product Owner / Principal Engineer
- **Definition**: Concrete, functional unit in the system. Represents **Value Delivery**.
- **Atomicity Principle**: Feature = Design + Dev + Test + Doc + i18n. They are an indivisible whole.
- **Note**: This concept replaces traditional "Story".

### 1.3 Execution Layer

#### 🧹 CHORE

- **Prefix**: `CHORE-`
- **Mindset**: Builder / Maintainer
- **Definition**: Engineering maintenance, refactoring, or upgrade. **Does not directly produce** user functional value, but is crucial for system health.
- **Scenario**: Architecture upgrade, CI/CD fix, dependency update.
- **Note**: This concept replaces traditional "Task".

#### 🐛 FIX

- **Prefix**: `FIX-`
- **Mindset**: Debugger
- **Definition**: Correction of deviation between "Expectation" and "Reality".
- **Note**: This concept replaces traditional "Bug".

---

## 2. State Machine

Monoco uses a **Two-Layer State Machine** to manage lifecycle: **Status** (Physical State) and **Stage** (Logical Stage).

### 2.1 Status (Physical)

Determines Issue's **Visibility** and **Storage Location**.

- **Backlog**:
  - **Meaning**: Ideas not yet scheduled or temporarily shelved.
  - **Location**: `Issues/*/backlog/`
  - **Stage**: Locked as `Freezed` until Pulled.

- **Open**:
  - **Meaning**: Tasks in progress or planned for near future.
  - **Location**: `Issues/*/open/`
  - **Stage**: Can transition (Todo -> Doing -> Review).

- **Closed**:
  - **Meaning**: Lifecycle ended.
  - **Location**: `Issues/*/closed/`
  - **Stage**: Forced to `Done`.

### 2.2 Stage (Logical)

Describes **Execution Progress** of Issue in `Open` status.

- **Todo**: Scheduled, waiting to start.
- **Doing**: In progress. Coding or designing. Usually corresponds to a Git branch or Worktree.
- **Review**: Under review. Code committed, waiting for merge or acceptance.
- **Done**: Completed. Achieved only when Issue is closed.

---

## 3. Topology (Relationships)

Issues are connected via three types of relationships, forming the project's knowledge graph.

### 3.1 Relationship Types

#### Parent

- **Semantics**: Hierarchy / Belonging.
- **Direction**: Many-to-One.
- **Typical Scenario**: Feature belongs to Epic; Chore belongs to Epic.
- **Constraint**: No circular reference supported.

#### Dependency

- **Semantics**: Blocking / Precondition.
- **Direction**: A depends on B (B block A).
- **Constraint**: A can only be closed after B is closed.

#### Related

- **Semantics**: Reference / Context.
- **Direction**: Bi-directional weak association.
- **Typical Scenario**: Reference related Issues to provide background info.

### 3.2 Workspace Referencing

Supports Workspace-level issue tracking. Use namespace syntax to reference Issues in other projects.

- **Syntax**: `project_name::ISSUE-ID`
- **Example**: `monoco::EPIC-001`
- **Requirement**: Must configure `members` in `.monoco/config.yaml`.
