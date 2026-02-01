---
id: FEAT-0136
uid: 16590c
type: feature
status: closed
stage: done
title: Enforce Domain Governance Rules and Auto-Inheritance
created_at: '2026-02-01T09:37:27'
updated_at: '2026-02-01T10:12:16'
priority: medium
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
opened_at: '2026-02-01T09:37:27'
closed_at: '2026-02-01T10:12:16'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0136-enforce-domain-governance-rules-and-auto-inheritan
  created_at: '2026-02-01T10:11:55'
owner: IndenScale
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

- [x] **Stats**: 在 Linter 中实现全库统计功能（Count Epics/Issues）。
- [x] **Rule Implementation**: 实现 `DomainCoverageRule`。
  - Check: `if (stats.epics > 32 or stats.issues > 128) and (untracked_ratio > 0.25): raise Violation`.
- [x] **Inheritance Logic**:
  - 修改 Validator，当检查 Feature 的 Domain 时，如果为空，尝试获取 Parent 的 Domain。
  - 如果 Parent 也没有 Domain 且处于严格模式，则报错。

## Review Comments

### Implementation Summary (2026-02-01)

1. **Scale-Aware Thresholds**: 在 `linter.py` 的 `check_integrity()` 函数中实现了项目规模统计，当检测到 `num_issues > 128` 或 `num_epics > 32` 时激活严格模式。

2. **Domain Coverage Rule**: 在 `linter.py` 中添加了项目级别的 Domain 覆盖率检查。计算未分配 Domain 的 Epic 比例，如果超过 25% 则报错。

3. **Auto-Inheritance Logic**: 在 `validator.py` 的 `_validate_domains()` 中实现了逻辑继承：
   - 如果子 Issue 没有 domains 但 parent 有，则视为有效继承（不产生错误）
   - 如果子 Issue 和 parent 都没有 domains，且处于大规模模式，则报错

4. **Tests**: 添加了 5 个测试用例验证：
   - 大规模项目低覆盖率触发错误
   - 足够覆盖率通过检查
   - 子 Issue 逻辑继承 parent 的 Domain
   - 子 Issue 和 parent 都无 Domain 时报错
   - 小规模项目不触发严格检查

**Files Modified**:
- `monoco/features/issue/linter.py`: 添加项目级别 Domain 覆盖率检查
- `monoco/features/issue/validator.py`: 添加 `all_issues` 参数和继承逻辑
- `tests/features/issue/test_domain_governance.py`: 新增测试文件

## Delivery
<!-- Monoco Auto Generated -->
**Commits (1)**:
- `2c919f6` feat(issue): FEAT-0136 enforce domain governance rules and auto-inheritance

**Touched Files (4)**:
- `Issues/Features/open/FEAT-0136-enforce-domain-governance-rules-and-auto-inheritan.md`
- `monoco/features/issue/linter.py`
- `monoco/features/issue/validator.py`
- `tests/features/issue/test_domain_governance.py`