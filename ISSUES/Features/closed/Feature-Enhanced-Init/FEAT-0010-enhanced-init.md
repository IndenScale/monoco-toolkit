---
id: FEAT-0010
type: FEATURE
status: CLOSED
priority: NORMAL
solution: implemented
title: Enhanced Monoco Init Command
description: |
  Expand `monoco init` to recursively initialize all sub-modules (Issue, Spike, I18n, Skills) to ensure a fully ready environment with a single command.
dependencies: []
related: []
tags: [cli, init, devops]
---

# Objective

Enhance `monoco init` to be the single entry point for project initialization. It should not only scaffold the `Issues` directory but also trigger initialization logic for `Spike`, `I18n`, and `Skills` modules, ensuring a complete and consistent environment setup.

# Comparison & Gap Analysis

| Module     | Current `monoco init`                              | Current Capability                                           | Gap                                                                           |
| :--------- | :------------------------------------------------- | :----------------------------------------------------------- | :---------------------------------------------------------------------------- |
| **Core**   | Scaffolds `.monoco/config.yaml`.                   | `init_cli` in `core/setup.py`                                | None.                                                                         |
| **Issue**  | Scaffolds `Issues/{Type}` directories (Hardcoded). | Basic directory creation.                                    | Logic is hardcoded in `core/setup.py` instead of delegated to `issue` module. |
| **Spike**  | **Ignored**.                                       | `monoco spike init` exists (sets `.gitignore`, creates dir). | `init` does not call `spike init`.                                            |
| **I18n**   | **Ignored**.                                       | No `init` command. Relies on `config` defaults.              | Should populate `config.i18n` or ensure defaults are explicit.                |
| **Skills** | **Ignored**.                                       | No code.                                                     | Need to scaffold `Toolkit/skills` or similar structure.                       |

# Technical Tasks

- [x] **Infrastructure: Module Resource Interface**: Define a standard way (`get_resources()`) for feature modules (`issue`, `spike`, `i18n`) to expose their `SKILL` (documentation) and `PROMPT` (agent guide) content.
- [x] **Refactor Issue Init**: Extract issue directory scaffolding from `core/setup.py` to `features/issue`. Implement `get_resources` to return Issue Management skills.
- [x] **Refactor Spike Init**: Integrate `spike.init`. Implement `get_resources` to return Spike methodology skills.
- [x] **Create I18n Init**: Implement `i18n.init`. Implement `get_resources` to return I18n workflow skills.
- [x] **Implement Skills Init**:
  - Create `Toolkit/skills` directory.
  - Aggregate `SKILL` content from all modules and write/update corresponding files in `Toolkit/skills`.
- [x] **Implement Agent Docs Injection**:
  - Target `AGENTS.md`, `GEMINI.md`, and `CLAUDE.md`.
  - Implement a "Section Replacement" utility: Find `## Monoco Toolkit`, replace everything until the next `##` or EOF with the aggregated `PROMPT` content from modules.
  - Ensure idempotency (no duplicate sections).
- [x] **Orchestrate**: Update `monoco.core.setup.init_cli` to drive this sequence.

# Implementation Notes

- **Terminology Update**: During the refactoring of `issue` module resources, the terminology was updated from `Story/Task/Bug` to **`Feature/Chore/Fix`** to align with Agentic workflows.
- **Feature Definition**: The definition of a `Feature` (formerly Story) was explicitly enhanced to `Feature = Design + Dev + Test + Doc + i18n`, enforcing documentation and internationalization as part of the atomic value delivery.
- **Resource Aggregation**: The `skills` module now dynamically pulls `SKILL` and `PROMPT` content from registered feature modules, ensuring that `monoco init` always deploys the latest definitions without code duplication.

# Acceptance Criteria

1.  **One-Stop Shop**: `monoco init` sets up Config, Issues, Spikes, I18n, and **Skills**.
2.  **Skill Population**: `Toolkit/skills` is populated with `issue`, `spike`, `i18n` skill guides derived from the modules themselves.
3.  **Agent Docs**: `AGENTS.md` (and friends) are created/updated. They contain a `## Monoco Toolkit` section with instructions for all enabled modules.
4.  **Idempotency**: Running `init` multiple times updates the `## Monoco Toolkit` section in place without duplication.
5.  **Modular**: Core does not hold the content string; it pulls it from the modules.
