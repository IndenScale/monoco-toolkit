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

## 背景与目标

记录关于 ACP 和 Kimi CLI 的架构决策，明确技术选型理由。Agent Client Protocol（ACP）专为编辑器到代理的通信设计（基于 JSON-RPC），而 Monoco 需要的是编排器到代理的无头接口。经过评估，ACP 对于南向接口引入了不必要的复杂性（服务器管理、RPC 客户端）。本决策记录将阐明为何继续采用 EngineAdapter 加 CLI 模式，而非直接集成 ACP，为未来可能的北向接口（编辑器到 Monoco）保留 ACP 的应用空间。

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