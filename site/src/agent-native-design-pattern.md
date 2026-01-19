# Agent Native Software Design Patterns

> **Design for Agents first, Humans second.**

Agent Native software differs fundamentally from traditional software. Traditional software assumes users possess intuition and error-correction capabilities, whereas Agent Native software must assume users (Agents) require determinism, explicitness, and idempotency.

## 1. CLI First Principle

The CLI is the most natural interface for Agents.

- **Programmable Output**: Must provide options to disable Rich Print/ANSI Color (usually via `--json` or auto-detecting non-TTY environments).
- **Parsable Structure**: `stdout` is for structured data (JSON) only; `stderr` is for logs and diagnostics. NEVER mix debug logs with print output in `stdout`.

## 2. Explicit over Implicit

Agents are prone to errors when dealing with "context" and "implicit state".

- **Verbose Parameters**: Embrace verbose parameter lists instead of relying on implicit configuration lookup orders.
  - _Bad_: `monoco build` (Guesses target based on current directory)
  - _Good_: `monoco build --target ./src/main.py --out ./dist`
- **State Transparency**: If a command relies on a certain state, error messages must explicitly point out the missing state file path.

## 3. Zero Interaction

Interactive inputs (Interactive Prompts, Wizards) are nightmares for Agent automation.

- **Avoid Prompts**: All inputs must be providable via Arguments/Options.
- **No "Are you sure?"**: If confirmation is needed, must support `--yes` or `--force` flags.
- **Dry Run**: For destructive operations, provide a `--dry-run` option to allow Agents to rehearse the outcome.

## 4. Declarative & Idempotent

Agents might execute commands repeatedly or retry in the middle of a failed task.

- **Idempotency**: Running the same command multiple times should yield the same result and must not crash (or should return a safe status code).
  - `create --id 123`: If it naturally exists, it should not Crash, but return "Already Exists" or perform an "Upsert" (depending on semantics).
- **Happy Path APIs**: Provide high-level, aggregated APIs covering common paths (`create_feature` instead of `create_file` + `write_metadata`).
- **Safety Rails**: Unless `--force` is used, do not overwrite existing files with conflicting content.

## 5. File as API & Governance

Allow Agents to manipulate underlying data (files) directly, rather than forcing them to interact exclusively via CLI. However, governance means must be provided.

- **Hackability**: Allow users (or Agents) to directly modify `.md` or configuration files using an editor. Do not design binary or opaque storage formats.
- **Trust but Verify (Lint/Check)**:
  - Must provide `lint` or `check` commands.
  - Mount checks on critical paths (e.g., git commit, build).
  - If an Agent manually modifies a file and breaks the Schema, the `lint` command must provide precise repair suggestions (e.g., `Line 5: Missing 'status' field`).
