---
id: FEAT-0114
uid: db0077
type: feature
status: closed
stage: done
title: Issue Criticality System with Immutable Policy Enforcement
created_at: '2026-01-30T08:33:16'
updated_at: '2026-01-30T09:14:09'
parent: EPIC-0001
dependencies: []
related: []
domains:
- Guardrail
- IssueTracing
tags:
- '#EPIC-0001'
- '#FEAT-0114'
files:
- '"Issues/Epics/open/EPIC-0001-Monoco\345\267\245\345\205\267\347\256\261.md"'
- Issues/Features/closed/FEAT-0116-display-available-domains-and-governance-tips-on-i.md
- Issues/Features/open/FEAT-0114-issue-criticality-system-with-immutable-policy-enf.md
- monoco/core/config.py
- monoco/features/issue/commands.py
- monoco/features/issue/core.py
- monoco/features/issue/criticality.py
- monoco/features/issue/domain/models.py
- monoco/features/issue/engine/machine.py
- monoco/features/issue/models.py
- tests/features/issue/test_governance_domains.py
- tests/test_criticality.py
criticality: high
opened_at: '2026-01-30T08:33:16'
closed_at: '2026-01-30T09:14:09'
solution: implemented
---

## FEAT-0114: Issue Criticality System with Immutable Policy Enforcement

## Objective
在 Issue 创建时引入 `criticality` 字段，用于固化质量标准和审查策略。执行者（Builder/Agent）只能严格执行或申请升级，不能降低标准。为后续的 Agent Code Review 验收关卡提供策略基础。

## Acceptance Criteria
- [x] Issue 模型支持 `criticality` 字段（low | medium | high | critical）
- [x] `criticality` 在创建后不可直接修改
- [x] 支持通过 Escalation 流程申请升级（需审批）
- [x] 根据 `criticality` 自动派生 `_policy`（agent_review, human_review, test_coverage 等）
- [x] CLI 支持 `--criticality` 参数创建 Issue
- [x] 类型默认映射（feature→medium, fix→high 等）
- [x] 路径/标签自动提升规则（如 payment/** → critical）
- [x] 子 Issue 继承父 Issue 的最低 criticality

## Technical Tasks

### 1. 模型层扩展
- [x] 在 `IssueMetadata` / `IssueFrontmatter` 添加 `criticality: CriticalityLevel` 字段
- [x] 添加 `CriticalityLevel` Enum（low, medium, high, critical）
- [x] 实现 `_policy` 派生逻辑（`resolved_policy` property）
- [x] 实现 `Policy` 模型（agent_review, human_review, coverage, rollback_on_failure）
- [x] 添加 `EscalationRequest` 模型

### 2. 核心业务逻辑
- [x] 实现 `PolicyResolver`（根据 criticality 解析策略）
- [x] 实现 `CriticalityInheritanceService`（子 Issue 继承规则）
- [x] 实现 `AutoEscalationDetector`（路径/标签自动提升）
- [x] 实现 `EscalationApprovalWorkflow`（升级审批流程）

### 3. CLI 命令
- [x] `monoco issue create` 支持 `--criticality` 参数
- [x] `monoco issue escalate <id> --to <level> --reason <text>`
- [x] `monoco issue approve-escalation <id> --escalation-id <id>`
- [x] `monoco issue show <id> --policy`（查看解析后的策略）

### 4. 验证与约束
- [x] 在 `TransitionService` 中集成 policy 检查
- [x] Submit 时根据 policy 强制执行 Agent Review
- [x] Builder 权限边界验证（不能 waive/lower）

### 5. 配置与默认值
- [x] `.monoco/workspace.yaml` 支持 criticality 相关配置
- [x] 类型默认映射配置
- [x] 自动提升规则配置

## Design Notes

### Criticality 与 Policy 映射

| criticality | agent_review | human_review | min_coverage | rollback_on_failure |
|-------------|--------------|--------------|--------------|---------------------|
| low | lightweight | optional | 0 | warn |
| medium | standard | recommended | 70 | rollback |
| high | strict | required | 85 | block |
| critical | strict+audit | required+record | 90 | block+notify |

### 权限矩阵

| 操作 | Builder | Creator | Tech Lead |
|------|---------|---------|-----------|
| 创建时指定 criticality | ❌ | ✅ | ✅ |
| 执行 policy | ✅ | ✅ | ✅ |
| escalate（申请升级） | ✅ | ✅ | ✅ |
| approve escalation | ❌ | ✅ | ✅ |
| lower criticality | ❌ | ❌ | ❌（系统禁止）|
| waive requirement | ❌ | ❌ | ❌（系统禁止）|

## Implementation Summary

### 新增文件
- `monoco/features/issue/criticality.py` - 核心 criticality 系统实现
- `tests/test_criticality.py` - 46 个单元测试

### 修改文件
- `monoco/features/issue/models.py` - IssueMetadata 添加 criticality 字段和 resolved_policy 属性
- `monoco/features/issue/domain/models.py` - IssueFrontmatter 添加 criticality 字段
- `monoco/features/issue/core.py` - create_issue_file 支持 criticality 参数，继承父 Issue 逻辑
- `monoco/features/issue/commands.py` - 添加 escalate, approve-escalation, show --policy 命令
- `monoco/features/issue/engine/machine.py` - StateMachine 集成 policy 检查
- `monoco/core/config.py` - 添加 CriticalityConfig 配置支持
- `tests/features/issue/test_governance_domains.py` - 修复 domain 验证测试断言

## Bug Fixes
- 修复 `test_issue_to_domain_reference_validation` 测试断言，匹配实际的错误消息格式

## Related
- Parent: EPIC-0001
- 为后续 Agent Code Review 验收关卡提供策略基础

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
