---
id: FEAT-0136
uid: 16590c
type: feature
status: open
stage: draft
title: Enforce Domain Governance Rules and Auto-Inheritance
created_at: '2026-02-01T09:37:27'
updated_at: '2026-02-01T09:37:27'
opened_at: '2026-02-01T09:37:27'
priority: medium
owner: IndenScale
parent: EPIC-0026
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0026'
- '#FEAT-0136'
- cli
- lint
- governance
- domain-driven-design
files: []
criticality: medium
---

## FEAT-0136: Enforce Domain Governance Rules and Auto-Inheritance

## FEAT-0136: 强制实施领域治理规则与自动继承

### 背景

随着项目规模的扩大（Issue 数量 > 128 或 Epic > 32），单纯的列表管理变得不可持续。此时必须引入 **领域 (Domains)** 来进行切分和隔离。为了避免 "Domain 变成摆设"，我们需要在 Linter 中强制执行 "Domain 覆盖率" 规则。

同时，为了减轻由于强制 Domain 带来的填写负担，我们需要实现 "Domain 继承" 机制，即 Feature/Task 默认继承其 Parent Epic 的 Domain。

### 目标

在 `monoco issue lint` 中引入基于规模的治理检查，并实现元数据的自动继承。

### 功能需求

#### 1. 规模感知阈值 (Scale-Aware Thresholds)
Linter 在运行时统计当前项目的总活跃 Issue 数和 Epic 数。
如果满足 **"规模化条件"** (Total Issues > 128 OR Total Epics > 32)，则激活以下严格检查：

#### 2. 强制领域覆盖规则 (Domain Coverage Rule)
当处于 "规模化" 状态时：
- **规则**: `Untracked Epics / Total Epics <= 25%`
- **含义**: 项目中至少 75% 的 Epic 必须明确归属于至少一个 Domain。
- **报错**: 如果未达标，`monoco issue lint` 应报错，提示 "Domain coverage is too low for a project of this scale. Please categorize more Epics."

#### 3. 自动继承机制 (Automatic Inheritance)
- **如果**: 子 Issue (Feature/Fix/Chore) 的 `domains` 字段为空。
- **并且**: 它有有效的 `parent` (Epic)。
- **那么**: Linter 或 Runtime 应当视其拥有 Parent 的所有 Domains。
- **Fix**: `monoco issue lint --fix` 应该能够自动将 Parent 的 Domain 填入子 Issue 的 Front Matter 中（物理继承），或者系统仅在内存中处理（逻辑继承）。
  - *建议实现逻辑继承优先，或者仅在 Create 时填充默认值。lint 检查时若为空，则查找 parent，若 parent 有，则视为 pass。*

### 检查清单

- [ ] **Stats**: 在 Linter 中实现全库统计功能（Count Epics/Issues）。
- [ ] **Rule Implementation**: 实现 `DomainCoverageRule`。
  - Check: `if (stats.epics > 32 or stats.issues > 128) and (untracked_ratio > 0.25): raise Violation`.
- [ ] **Inheritance Logic**:
  - 修改 Validator，当检查 Feature 的 Domain 时，如果为空，尝试获取 Parent 的 Domain。
  - 如果 Parent 也没有 Domain 且处于严格模式，则报错。

## Review Comments
*No comments yet.*
