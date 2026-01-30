---
id: FEAT-0113
uid: 5c9ec1
type: feature
status: closed
stage: done
title: Introduce physical domain governance and cross-reference validation
created_at: '2026-01-30T08:10:34'
updated_at: '2026-01-30T08:11:44'
parent: EPIC-0021
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0021'
- '#FEAT-0113'
files:
- Issues/Domains/AgentOnboarding.md
- Issues/Domains/AgentScheduling.md
- Issues/Domains/Guardrail.md
- Issues/Domains/IssueTracing.md
- Issues/Features/open/FEAT-0113-introduce-physical-domain-governance-and-cross-ref.md
- monoco/features/issue/linter.py
- monoco/features/issue/validator.py
- tests/features/issue/test_governance_domains.py
opened_at: '2026-01-30T08:10:34'
closed_at: '2026-01-30T08:11:44'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0113-introduce-physical-domain-governance-and-cross-ref
  created_at: '2026-01-30T08:10:38'
---

## FEAT-0113: Introduce physical domain governance and cross-reference validation

## Objective
引入“物理领域治理”机制，将 Domain 定义从硬编码转向物理文件管理（Issues/Domains/），并建立 Issue 到 Domain 的强类型引用校验。

## Acceptance Criteria
- [x] 创建 `Issues/Domains/` 目录并初始化 4 个核心 Domain。
- [x] Linter 支持扫描 Domains 目录并校验文件名与 H1 标题一致性。
- [x] Validator 支持根据物理存在的 Domain 文件校验 Issue 中的 `domains` 引用。
- [x] 增加自动化测试覆盖上述逻辑。

## Technical Tasks
- [x] 初始化物理 Domain 定义文件。
- [x] 重构 `linter.py` 以支持 Domain 扫描与双轨制验证。
- [x] 增强 `IssueValidator` 以支持动态 Domain 集合校验。
- [x] 编写并运行 `test_governance_domains.py`。

## Review Comments
- [x] 代码已实现 Domain 目录的物理扫描逻辑。
- [x] Validator 已增强，支持读取物理 Domain 定义进行引用校验。
- [x] 单元测试已覆盖核心逻辑。
- [x] 已修正 Domain definition 的 H1 标题规范。
