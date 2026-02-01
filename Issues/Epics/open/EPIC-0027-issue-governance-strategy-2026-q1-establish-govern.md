---
id: EPIC-0027
uid: 1ed7f6
type: epic
status: open
stage: draft
title: 'Issue Governance Strategy 2026 Q1: Establish Governance and Archival Baseline'
created_at: '2026-02-01T10:27:42'
updated_at: '2026-02-01T10:27:42'
parent: EPIC-0000
dependencies: []
related: []
domains: 
- IssueGovernance
tags:
- '#EPIC-0027'
- '#EPIC-0000'
- governance
- archival
- q1-2026

- narrative
files: []
criticality: high
opened_at: '2026-02-01T10:27:42'
---

## EPIC-0027: Issue Governance Strategy 2026 Q1: Establish Governance and Archival Baseline

> **Narrative Epic**: Issue 治理与质量控制的长期叙事

## Objective
建立 Monoco Toolkit 的 Issue 治理基线，确立 "Issue Governance" 为核心领域。解决随着项目演进带来的 Issue 膨胀、元数据混乱和历史债务问题。本 Epic 旨在通过自动化工具 (Lint, CLI) 和标准流程 (SOP) 来降低维护成本，确保 Issue Library 始终保持高信噪比。

## Acceptance Criteria
- [ ] **Archival Strategy**: 完成历史 Issue 的物理归档，并确保 CLI/IDE 工具能够正确处理归档数据 (忽略或按需加载)。
- [ ] **Lint Enhancement**: 升级 `monoco issue lint`，支持更复杂的业务规则校验 (如状态流转完整性、标签完整性)。
- [ ] **Legacy Cleanup**: 清理并归档 2025 年及之前的过时 Issue，Close 长期未完成的僵尸 Epic。

## Technical Tasks

### Governance & Process
- [x] **Define Domains**: 创建 `IssueGovernance`, `Infrastructure`, `DevEx` 等核心 Domain 定义文件。
- [x] ** Integration**: 已合并 。
- [ ] **Refine Rules**: 在 `monoco/features/issues/resources/rules/` 中固化 Issue 编写规范。

### Tooling & Automation
- [ ] **FEAT-Archival-CLI**: 实现 `monoco issue archive <id>` 命令，自动移动文件并更新元数据。
- [ ] **FEAT-Lint-Upgrade**: 增强 Linter 以支持 Domain 继承校验和 Cross-Reference 完整性检查。

### Operations (The "Vacuum" Operation)
- [ ] **Cleanup**: 扫描并归档所有 `status: closed` 且 `updated_at < 2026-01-01` 的 Issue。
- [ ] **Re-org**: 将散落在 Root 下的 Feat/Fix 归类到具体的 Domain Epic 中。

## Review Comments
*None yet.*
