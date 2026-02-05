# The Lifecycle Loop

Monoco defines a strict, closed-loop lifecycle to ensure every task has a beginning and an end.

## Macro Loop

### 1. Drafting

- **Actor**: Human
- **Action**: `create`
- **State**: `open/draft`
- **Description**: This is a fuzzy intent. No code is needed, only define the "Why" and "What."

### 2. Branching

- **Actor**: Human / Agent
- **Action**: `start --branch`
- **State**: `open/doing`
- **Key Changes**:
  - Stage changes to `Doing`.
  - **Physical Isolation**: Automatically creates `feat/FEAT-XXX` branch.
  - **Environment Policy**: From this point on, all code modifications must happen on this branch. The Trunk becomes read-only.

### 3. Execution & Tracking

- **Actor**: Agent
- **Action**: Coding...
- **Micro-Loop**:
  1.  Agent modifies code.
  2.  **Sync**: Run `monoco issue sync-files`.
      - Compares `Branch` vs `Trunk`.
      - Automatically updates the `files: [...]` list in the Issue Frontmatter.
  3.  Agent checks off `Technical Tasks` in the Body (`[ ]` -> `[x]`).

### 4. Submission

- **Actor**: Agent
- **Action**: `submit`
- **State**: `open/review`
- **Description**: The Agent believes the work is finished. The `submit` command runs Lint checks, prunes temporary resources, and prompts to create a PR.

### 5. Review

- **Actor**: Human
- **Action**: Review Code & Issue
- **Description**: Human inspects code and Issue description.
  - **Approve**: Merge PR.
  - **Reject**: Add `## Review Comments` to the Issue and move it back to `Doing`.

### 6. Archiving

- **Actor**: System (via CI/CD or Manual)
- **Action**: `close`
- **State**: `closed/done`
- **Description**: The Issue file is physically moved to the `closed/` directory. It becomes part of the project's permanent knowledge base.

---

## Environment Policy

To maintain the integrity of the loop, the Linter enforces the following policies:

- **Dirty Trunk Protection**: Modifying code directly on Trunk (`main`, `master`, or `production`) is strictly prohibited.
  - If the Linter finds uncommitted changes on the Trunk, it will **throw an error and block operations**.
  - **Solution**: `git stash` -> `monoco issue start --branch` -> `git stash pop`.

---

[Previous: 01. Structure](./01_structure.md) | \*\*Next: 03. Workflow](./03_workflow.md)
