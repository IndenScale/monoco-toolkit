# Agent Integration

Monoco is more than a CLI tool; it is an **Agent Behavior Protocol**. This chapter reveals how Monoco constrains and guides Agents through mechanism design.

## 1. Skill Injection

When you run `monoco init`, the system automatically generates a set of standard documents under `.agent/skills/monoco_issue/`:

- `SKILL.md`: Defines ontology, workflows, and validation rules.
- `AGENTS.md`: A minimalist, token-friendly cheatsheet for Agents.

**Any Agent interfacing with Monoco (e.g., in the VS Code Extension) must load these skills into its System Prompt.**

## 2. Behavior Shaping

Monoco does not rely on Agent "goodwill" but on **environmental constraints**.

### Constraint 1: Mandatory Linting

An Agent cannot submit a malformed Issue because the `submit` command enforces a `lint` run. If it fails, the process is blocked, and the Agent must self-correct based on error messages.

### Constraint 2: Branch Isolation

If an Agent tries to take a shortcut by modifying the main branch directly, the Linter's **Environment Policy** throws an error, forcing the Agent to learn and execute branch switching operations.

### Constraint 3: Explicit Context Tracking

Through `sync-files`, we force implicit code changes to become explicit. When an Agent resume a task, it doesn't need to rediscover "what was changed last time"—it just reads the `files` list.

## 3. Why Git-Native?

Many Agent frameworks try to build their own "sandboxes" or "databases." Monoco chooses Git because:

1.  **Git is the Standard**: Any Agent eventually delivers code to Git anyway.
2.  **Diff is the Best Context**: `git diff` is the most precise and token-efficient way to express "what was done."
3.  **Zero Migration Cost**: Your project is already in Git. Monoco doesn't require you to migrate data.

Monoco simply lays a "semantic track" for Agents on top of Git.

---

[Previous: 03. Workflow](./03_workflow.md) | [Back to Overview](./00_overview.md)
