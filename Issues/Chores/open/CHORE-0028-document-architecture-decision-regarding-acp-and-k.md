---
id: CHORE-0028
uid: a4e3c5
type: chore
status: open
stage: draft
title: Document Architecture Decision regarding ACP and Kimi CLI
created_at: '2026-02-01T20:57:13'
updated_at: '2026-02-01T20:57:13'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0028'
- '#EPIC-0000'
files: []
criticality: low
opened_at: '2026-02-01T20:57:13'
---

## CHORE-0028: Document Architecture Decision regarding ACP and Kimi CLI

## Objective
Document the architectural decision to **NOT** use ACP (Agent Client Protocol) for internal Monoco Agent orchestration, but rather continue using the EngineAdapter + CLI pattern.

**Context**:
- **ACP** is designed for Editor-to-Agent communication (JSON-RPC over stdio/HTTP).
- **Monoco Requirement**: Orchestrator-to-Agent (Headless).
- **Decision**: ACP introduces unnecessary complexity (server management, RPC client) for the south-bound interface. It might be useful as a north-bound interface (Editor -> Monoco) in the future, but not for wrapping Kimi CLI.
- **Ref**: Memo [6f50db].

## Acceptance Criteria
- [ ] Architecture Decision Record (ADR) or equivalent documentation created (e.g., in `Issues/Domains/Infrastructure.md` or a new ADR file).
- [ ] The decision is clearly explained with "Context", "Decision", and "Consequences".

## Technical Tasks
- [ ] Create/Update documentation file.
- [ ] Commit documentation.

## Review Comments