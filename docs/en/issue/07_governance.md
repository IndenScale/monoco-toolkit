# Governance Maturity

Monoco adopts a **Progressive Governance** strategy. We don't advocate for heavy specifications at the start; instead, we automatically switch from lightweight to strict governance based on project scale (total Issues, total Epics).

## 1. Maturity Levels

| Level            | Suitable Stage       | Core Requirements            | Governance Means        |
| :--------------- | :------------------- | :--------------------------- | :---------------------- |
| **L1: Draft**    | Personal / Prototype | Only `id`, `title`           | Semantic Parsing        |
| **L2: Standard** | Team Collaboration   | AC, Tasks, Stage Constraints | `monoco issue lint`     |
| **L3: Mature**   | Enterprise / Scale   | Domains, I18n Sync           | Mandatory Linter Checks |

## 2. Auto-Upgrade Mechanism

Monoco's Linter automatically identifies the maturity phase based on project activity:

- **Triggers**: When project `Issues > 50` or `Epics > 8`.
- **Mandatory Requirements**:
  - **Domains**: Frontmatter must include a `domains` field for domain isolation.
  - **Language**: Documentation language must match the project's source language.

## 3. Constraint Rules

### 3.1 Status Consistency

An Issue with `status: closed` must have `stage: done`, and:

- All `Acceptance Criteria` must be completed (`[x]`).
- All `Technical Tasks` must be resolved.
- A `solution` description must be present.

### 3.2 Tag Linkage

The `tags` field for each Issue must include its Parent ID, Dependency IDs, and its own ID. This provides Agents with a comprehensive knowledge retrieval capability.

---

[Previous: 06. Query Syntax](./06_query_syntax.md) | **Next: End of Chapter**
