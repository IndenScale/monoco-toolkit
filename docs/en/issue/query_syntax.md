# Monoco Issue Query Syntax Specification

Monoco Issue System (Web & CLI) adopts a unified, semantic query syntax, allowing users to achieve precise filtering through intuitive keyword combinations.

## 1. Basic Syntax

The most basic unit of query is **Term**. We distinguish between "Nice to Have" and "Must Include" semantics.

### Nice to Have

These terms are **not mandatory**, but if present, will increase relevance or serve as candidates.

- **Syntax**: `keyword` (Direct input)
- **Semantics**: **Should Include**.
- **Example**:
  - `login`: Tends to find Issues containing "login".

### Must Include

Target **must contain** specified keywords.

- **Syntax**: `+keyword` (Plus prefix)
- **Semantics**: **Must Include**.
- **Example**:
  - `+bug`: Result **must** contain "bug".

### Excludes

Target **must not contain** specified keywords.

- **Syntax**: `-keyword` (Minus prefix)
- **Semantics**: **Must Not Include**.
- **Example**:
  - `-ui`: Exclude Issues containing "ui".

## 2. Phrases

If a query term contains **spaces** internally, the entire phrase must be wrapped in **double quotes**.

- **Syntax**: `"phrase with space"`
- **Example**:
  - `"login error"` -> Treated as a normal Nice to Have phrase.
  - `+"critical error"` -> Treated as a Must Include phrase.

## 3. Combination Logic

Multiple terms are separated by spaces. Logical priority is as follows:

1. **Excludes (-)** Highest priority: Any Issue matching exclude terms is directly filtered out.
2. **Must Includes (+)** Must all be satisfied (Implicit AND).
3. **Nice to Have** (No prefix):
   - If Must Includes exist: Nice to Have only affects sorting or extra info matching.
   - If **no** Must Includes exist: At least one Nice to Have must be satisfied (Implicit OR) (Note: specific implementation may tweak to full match depending on scenario).

**Common Combination Example**:

- `+bug -ui login`
  - Must contain `bug`
  - Must not contain `ui`
  - `login` is a bonus item (prioritize displaying login-related bugs)

## 4. Scope & Rules

### Rules

- **Case Insensitive**: `Bug`, `BUG`, `bug` are treated as same.
- **Full Scope**: Match all metadata and content in one query.

### Matched Fields

| Field | Description |
| :--- | :--- |
| **ID** | e.g. `FEAT-0012` |
| **Title** | Title text |
| **Body** | Body content |
| **Status** | Status (`open`, `closed`, `backlog`) |
| **Stage** | Stage (`todo`, `doing`, `review`, `done`) |
| **Type** | Type (`epic`, `feature`, `chore`, `fix`) |
| **Tags** | List of tags |
| **Dependencies** | IDs of dependencies |
