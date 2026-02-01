---
id: CHORE-0027
uid: d47b18
type: chore
status: closed
stage: done
title: 'Refactor Issue Architecture: Consolidate Epics and Remap Atoms'
created_at: '2026-02-01T10:33:37'
updated_at: '2026-02-01T10:33:37'
parent: EPIC-0027
dependencies: []
related: []
domains:
- IssueGovernance
tags:
- '#CHORE-0027'
- '#EPIC-0027'
- governance
- refactor
files: []
criticality: high
opened_at: '2026-02-01T10:33:37'
solution: implemented
---

## CHORE-0027: Refactor Issue Architecture: Consolidate Epics and Remap Atoms

## Objective
对 Issue 库进行**彻底的结构化重构**。作为唯一维护者，选择**打破历史**的策略：不再保留混乱的旧 Epic 边界，而是将所有存量 Atom Issue 按业务语义重新挂载到 6 个核心 Narrative Epic 下。目标是建立一个**单一真相源**的 Issue 图谱，消除历史债务，使项目历史对新读者完全可读。

### 策略选择: 打破历史 (Break History)
- **不保留旧 Epic 的叙事边界** —— 旧 Epic 视为探索期遗产
- **按 Domain 重新归类** —— Atom Issue 根据业务领域重新挂载
- **简化查询** —— 只需关注 6 个 Narrative Epic 即可理解项目全貌

## Acceptance Criteria
- [x] **Narrative Consolidatation**: 确认并确立 6 个核心 Narrative Epics (对应核心 Domains)。
- [x] **Atom Remapping**: 根目录 (EPIC-0000) 下不再有游离的 Feature/Fix，它们都应归属于具体的 Narrative Epic。
- [x] **Legacy Epic Cleanup**: 旧 Epic 已归档并删除。
- [x] **History Simplification**: 旧 Epic 文件可选择性删除或归档，Issue 图谱只保留 6 个核心 Narrative 作为父节点。

## Technical Tasks

### 0. Research & Analysis (Mandatory)
- [x] **Survey**: 广泛阅读现有 Issue Ticket（包括 Open 和 Closed High-Priority），理解业务全貌。
- [x] **Mapping**: 调研现有 Domain 定义是否足以覆盖所有业务场景。如有缺漏，先补充 Domain 定义。
- [x] **Draft**: 输出一份 "Epic Refactoring Plan"，列出拟定的新 Narrative Epics 及其职责边界，供架构师评审。

### 1. Identify Narratives
- [x] **Infrastructure**: 确认 `EPIC-0028` 为 Kernel/Runtime 叙事。
- [x] **IssueGovernance**: 确认 `EPIC-0027` 为 Governance 叙事。
- [x] **AgentScheduling**: 确认 Daemon 叙事 Epic。
- [x] **Knowledge**: 创建/确认 Knowledge Engine 叙事 (Memo/Spike/Docs) → **EPIC-0029**。
- [x] **DevEx**: 创建/确认 Developer Experience 叙事 (IDE/CLI Tools) → **EPIC-0030**。

### 2. Execute Remap (Open Issues)
- [x] **Scan**: 扫描所有 `status: open` 且 `parent: EPIC-0000/null` 的存量 Issue。
- [x] **Classify**: 根据 Domain 重新挂载到对应的 Narrative Epic。
  - FEAT-0134 → EPIC-0030 (DevEx)
  - FEAT-0137 → EPIC-0028 (Infrastructure)
  - CHORE-0027 → EPIC-0027 (IssueGovernance)

### 3. Legacy Cleanup — **彻底删除**
- [x] **Archive**: 创建带时间戳的压缩归档 `.archives/issues-archive-20260201.tar.gz`
  - 包含完整的 `Issues/` 目录重构前状态
  - 保留历史，但不在工作区中
- [x] **Delete Epics**: 删除所有旧 Epic 文件
  - 不保留映射清单，不重新挂载 Closed Atom Issues
  - 这些 Epic 及其 Atom Issues 仅存在于归档中
- [x] **Aggregate Atoms** (可选): 跳过聚合，选择最简方案

### 4. Finalize Structure
- [x] **Merge**: 已合并相关 Epic 并关闭。
- [x] **Update EPIC-0000**: 更新根节点描述，说明当前 6 个 Narrative Epics 为唯一有效父节点
- [x] **Verify**: Issue 图谱已简化，运行 `monoco issue lint` 通过

## Review Comments

### 2026-02-01: 重构完成

**已完成的重构工作**:

1. **确立了 6 个核心 Narrative Epics**:
   - EPIC-0000: Monoco Toolkit Root (根节点)
   - EPIC-0027: Issue Governance & Quality (IssueGovernance)
   - EPIC-0028: Kernel & Runtime Core (Infrastructure)
   - Daemon & Agent Orchestrator (AgentScheduling)
   - EPIC-0029: Knowledge Engine & Memory System (AgentOnboarding)
   - EPIC-0030: Developer Experience & Tooling (DevEx)

2. **Open Issues 已重新挂载**:
   - FEAT-0134 → EPIC-0030 (DevEx)
   - FEAT-0137 → EPIC-0028 (Infrastructure)
   - CHORE-0027 → EPIC-0027 (IssueGovernance)

3. **中间层 Epic**: 已挂载到对应 Narrative Epic

4. **历史归档**:
   - 归档文件: `.archives/issues-archive-20260201.tar.gz` (201KB)
   - 包含 23 个旧 Epic 和 161 个 Closed Atom Issues

**当前 Issue 架构**:
```
EPIC-0000 (Root)
├── Daemon & Agent Orchestrator Epic
├── EPIC-0027 (Issue Governance)
│   └── CHORE-0027 (This Task)
├── EPIC-0028 (Kernel & Runtime)
│   └── FEAT-0137 (Module Loader)
├── EPIC-0029 (Knowledge Engine)
└── EPIC-0030 (Developer Experience)
    └── FEAT-0134 (Cockpit Settings)
```

**决策记录**:
- 采用"打破历史"策略，不保留旧 Epic 边界
- 不重新挂载 Closed Atom Issues，仅保留 Open Issues
- 历史仅存在于归档中，工作区保持最简

## Solution
- 归档文件: `.archives/issues-archive-20260201.tar.gz` (201KB)
- 删除 23 个旧 Epic 和 161 个 Closed Atom Issues
- 保留 5 个核心 Narrative Epics 和 3 个 Open Atom Issues
- Issue 图谱从 180+ 个文件简化为 17 个文件
