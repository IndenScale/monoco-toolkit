---
id: FEAT-0114
uid: db0077
type: feature
status: open
stage: draft
title: Issue Criticality System with Immutable Policy Enforcement
created_at: '2026-01-30T08:33:16'
updated_at: '2026-01-30T08:33:16'
parent: EPIC-0001
dependencies: []
related: []
domains:
- Guardrail
- IssueTracing
tags:
- '#EPIC-0001'
- '#FEAT-0114'
files: []
opened_at: '2026-01-30T08:33:16'
---

## FEAT-0114: Issue Criticality System with Immutable Policy Enforcement

## Objective
在 Issue 创建时引入 `criticality` 字段，用于固化质量标准和审查策略。执行者（Builder/Agent）只能严格执行或申请升级，不能降低标准。为后续的 Agent Code Review 验收关卡提供策略基础。

## Acceptance Criteria
- [ ] Issue 模型支持 `criticality` 字段（low | medium | high | critical）
- [ ] `criticality` 在创建后不可直接修改
- [ ] 支持通过 Escalation 流程申请升级（需审批）
- [ ] 根据 `criticality` 自动派生 `_policy`（agent_review, human_review, test_coverage 等）
- [ ] CLI 支持 `--criticality` 参数创建 Issue
- [ ] 类型默认映射（feature→medium, fix→high 等）
- [ ] 路径/标签自动提升规则（如 payment/** → critical）
- [ ] 子 Issue 继承父 Issue 的最低 criticality

## Technical Tasks

### 1. 模型层扩展
- [ ] 在 `IssueMetadata` / `IssueFrontmatter` 添加 `criticality: CriticalityLevel` 字段
- [ ] 添加 `CriticalityLevel` Enum（low, medium, high, critical）
- [ ] 实现 `_policy` 派生逻辑（`resolved_policy` property）
- [ ] 实现 `Policy` 模型（agent_review, human_review, coverage, rollback_on_failure）
- [ ] 添加 `EscalationRequest` 模型

### 2. 核心业务逻辑
- [ ] 实现 `PolicyResolver`（根据 criticality 解析策略）
- [ ] 实现 `CriticalityInheritanceService`（子 Issue 继承规则）
- [ ] 实现 `AutoEscalationDetector`（路径/标签自动提升）
- [ ] 实现 `EscalationApprovalWorkflow`（升级审批流程）

### 3. CLI 命令
- [ ] `monoco issue create` 支持 `--criticality` 参数
- [ ] `monoco issue escalate <id> --to <level> --reason <text>`
- [ ] `monoco issue approve-escalation <id> --escalation-id <id>`
- [ ] `monoco issue show <id> --policy`（查看解析后的策略）

### 4. 验证与约束
- [ ] 在 `TransitionService` 中集成 policy 检查
- [ ] Submit 时根据 policy 强制执行 Agent Review
- [ ] Builder 权限边界验证（不能 waive/lower）

### 5. 配置与默认值
- [ ] `.monoco/workspace.yaml` 支持 criticality 相关配置
- [ ] 类型默认映射配置
- [ ] 自动提升规则配置

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

## Related
- Parent: EPIC-0001
- 为后续 Agent Code Review 验收关卡提供策略基础

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
