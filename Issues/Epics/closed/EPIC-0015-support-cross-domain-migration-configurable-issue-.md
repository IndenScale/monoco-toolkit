---
id: EPIC-0015
uid: ef2d2e
type: epic
status: closed
stage: done
title: 支持跨领域迁移与可配置化 Issue 系统
created_at: '2026-01-17T07:55:00'
opened_at: '2026-01-17T07:55:00'
updated_at: '2026-01-17T09:26:04'
closed_at: '2026-01-17T09:25:00'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0015'
path: /Users/indenscale/Documents/Projects/Monoco/Toolkit/Issues/Epics/closed/EPIC-0015-support-cross-domain-migration-configurable-issue-.md
progress: 3/3
files_count: 35
parent: EPIC-0000
---

## EPIC-0015: 支持跨领域迁移与可配置化 Issue 系统

## 目标 (Objective)

通过实现 **Issue 系统的可配置化**，使 Monoco 能够跨越软件工程的边界，支持营销、法务、内容创作等多领域的协作模式。这将涉及从底层的硬编码状态机迁移到**数据驱动的状态机**。

**Parent Architecture**: `ARCH-0001` (跨领域适应性架构)

## 验收标准 (Acceptance Criteria)

- [x] **配置驱动**: Issue 类型 (Type)、状态 (Status) 和 阶段 (Stage) 可通过 `monoco.yaml` 配置，而非硬编码。
- [x] **自定义工作流**: 支持用户定义特定的状态转移规则 (Transition Rules)，例如限制 "Backlog" 只能流转到 "Analysis"。
- [x] **影子对象层**: 实现并集成了 "Rich Domain Model"，能将 Markdown 解析为结构化对象。
- [x] **兼容性**: 系统内置默认的 `EPIC/FEATURE` 预设，确保现有软件工程项目的平滑过渡。

## 技术任务 (Technical Tasks)

- [x] **领域建模 (Domain Modeling)**: 设计并实现影子对象层 (Shadow Object Layer) `FEAT-0086`
- [x] **解析器增强 (Parser Enhancement)**: 实现基于 Block 的 Markdown 解析器，支持 AST 导出。
- [x] **配置加载器**: 实现 Schema Loader，用于读取和校验自定义工作流配置。
- [x] **动态状态机**: 实现可配置的 State Machine Engine，替代 `core.py` 中的 `if-else` 跳转逻辑。
- [x] **重构 Validator**: 基于新的领域模型重构校验逻辑。

## Review Comments

- [x] Self-Review

## Delivery

<!-- Monoco Auto Generated -->

**Commits (1)**:

- `ad26e9d` epic: close 15 (configurable issue)

**Touched Files (1)**:

- `Issues/Epics/open/EPIC-0015-support-cross-domain-migration-configurable-issue-.md`
