---
id: EPIC-0026
uid: bf71df
type: epic
status: open
stage: draft
title: Issue Governance & Archival Strategy
created_at: '2026-02-01T09:37:26'
updated_at: '2026-02-01T09:37:26'
opened_at: '2026-02-01T09:37:26'
priority: medium
owner: IndenScale
parent: EPIC-0000
dependencies: []
related: []
domains:
- IssueTracing
files: []
tags:
- '#EPIC-0000'
- '#EPIC-0026'
- archival
- governance
- maintenance
criticality: medium
progress: 1/2
files_count: 0
---

## EPIC-0026: Issue Governance & Archival Strategy

## 目标 (Objective)
建立长效的 Issue 治理机制，解决随着项目演进导致的 Issue 数量膨胀、信噪比降低性能下降问题。
核心在于引入 "归档 (Archival)" 概念，将历史数据与活跃数据物理隔离，同时在逻辑上保持可追溯性。

## 验收标准 (Acceptance Criteria)
- [ ] **Archival Structure**: 在文件系统中建立标准的归档目录结构（如 `Issues/Features/archived/`）。
- [ ] **Lint Compatibility**: `monoco issue lint` 能够识别并放行归档目录，不再报错。
- [ ] **Scan Performance**: 默认的 `monoco issue list` 和 VS Code 视图忽略归档数据，显著提升加载速度。
- [ ] **Historical Access**: 提供 `--all` 或类似参数，允许在需要时检索归档数据。
- [ ] **Domain Governance**: 实施基于规模的领域强制规则 (Domain Coverage)。

## 技术任务 (Technical Tasks)

- [ ] **FEAT-0135**: 增强 Issue 目录结构与 Lint 规则，支持 Archived 目录及忽略策略。
- [ ] **FEAT-0136**: 强制实施领域治理规则与自动继承 (Domain Governance Rules)。

## Review Comments
*No comments yet.*
