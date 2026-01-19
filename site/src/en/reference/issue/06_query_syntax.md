# Monoco Issue Query Syntax

The Monoco Issue System (Web & CLI) uses a unified, semantic query syntax that allows users to filter tasks precisely through intuitive keyword combinations.

## 1. Basic Syntax

The basic unit of a query is a **Term**. We distinguish between "optional" and "mandatory" semantics.

### Optional (Nice to Have)

These terms are not required, but if present, they increase relevance or act as candidates.

- **Syntax**: `keyword`
- **Example**: `login` -> Tends to find Issues containing "login".

### Mandatory (Must Include)

The target **must** contain the specified keyword.

- **Syntax**: `+keyword`
- **Example**: `+bug` -> Results **must** contain "bug".

### Exclusions (Must Not Include)

The target **must not** contain the specified keyword.

- **Syntax**: `-keyword`
- **Example**: `-ui` -> Excludes Issues containing "ui".

## 2. Phrase Queries

If a query term contains **spaces**, it must be wrapped in **double quotes**.

- **Syntax**: `"phrase with space"`

## 3. Combination Logic

Terms are separated by spaces. Priority:

1. **Exclusions (-)**: Highest priority.
2. **Mandatory (+)**: All must be met (Implicit AND).
3. **Optional**:
   - If mandatory terms exist: Optionals affect sorting.
   - If **no** mandatory terms exist: At least one optional must be met (Implicit OR).

**Example**: `+bug -ui login`

- Must contain `bug`
- Must not contain `ui`
- `login` is a bonus (login-related bugs appear first)

---

[Previous: 05. Configuration](./05_configuration.md) | \*\*Next: 07. Governance Maturity](./07_governance.md)
