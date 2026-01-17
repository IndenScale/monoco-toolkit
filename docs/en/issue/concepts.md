# Monoco Issue Core Concepts

This document defines the semantic model and architectural design of the Monoco Issue System.

The Monoco Issue System is more than just a task list; it is a synthesis of a **Universal Atom** and a **Configurable State Machine**, designed to provide a unified collaboration interface for both human engineers and AI agents.

## 1. Architecture

### 1.1 Universal Atom

In Monoco, all units of work—whether grand Epics, specific Features, or trivial Chores—are treated as isomorphic **Issues**.

- **Physical Layer**: Each Issue is a standard Markdown file containing YAML Frontmatter (metadata) and a Body.
- **Persistence**: All state changes map directly to the file system, eliminating dependence on external databases. This makes Git the **Single Source of Truth (SSOT)**.

### 1.2 Two-Layer State Machine

Monoco employs a unique two-layer state machine to manage the lifecycle, balancing the stability of physical storage with the flexibility of logical flow.

#### Status (Physical)

Determines the **physical location** and **visibility** of the Issue in the file system.

- **Open**: Active. Located in `Types/open/`.
- **Closed**: Finalized. Located in `Types/closed/`.
- **Backlog**: Frozen. Located in `Types/backlog/`.

#### Stage (Logical)

Determines the **execution progress** of the Issue while in the Open status. Stage transitions occur entirely in memory and do not involve file movement.

- _Default_: Draft, Doing, Review, Done, Freezed (Configurable).

## 2. Core Model

### 2.1 Taxonomy -> Configurable

While Monoco provides a default set of mindset-based categories (Epic/Feature/Chore/Fix), this is completely **configurable**. You can define your own types:

- **Name**: Internal identifier (e.g., `story`)
- **Label**: Display name (e.g., `User Story`)
- **Prefix**: ID prefix (e.g., `STORY`)
- **Folder**: Storage directory (e.g., `Stories`)

### 2.2 Workflows -> Configurable

All state transitions are defined by a set of explicit rules. A Transition includes:

- **Trigger**: Source state (From Status/Stage)
- **Action**: Action name (e.g., `submit`)
- **Effect**: Target state (To Status/Stage)
- **Side Effect**: Triggered CLI command (e.g., run Agent)

This design allows you to attach various automation logic to the state machine, such as "Automatically run AI Code Review Agent when entering the Review stage."

## 3. Topology

Issues are connected via three strong reference types, forming the project's knowledge graph.

| Type           | Semantics            | Direction     | Constraint                          |
| :------------- | :------------------- | :------------ | :---------------------------------- |
| **Parent**     | Hierarchy/Ownership  | Many-to-One   | Child must be within Parent context |
| **Dependency** | Blocker/Precondition | Any           | A cannot close until B is closed    |
| **Related**    | Reference/Context    | Bidirectional | No strong constraints               |

### Workspace Referencing

Supports referencing Issues from other projects within the same Workspace: `project_name::ISSUE-ID` (e.g., `backend::API-102`).
