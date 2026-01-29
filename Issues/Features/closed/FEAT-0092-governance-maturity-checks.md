---
id: FEAT-0092
uid: bf8436
parent: EPIC-0000
type: feature
status: closed
stage: done
title: Governance Maturity Checks
created_at: '2026-01-19T11:12:33'
opened_at: '2026-01-19T11:12:33'
updated_at: '2026-01-19T14:40:00'
solution: implemented
domains: []
dependencies: []
related: []
tags:
- '#EPIC-0000'
- '#FEAT-0092'
files: []
---

## FEAT-0092: Governance Maturity Checks

## 目标 (Objective)

<!-- 清晰描述 “为什么” 和 “是什么”。专注于价值。 -->

实现自动化的治理成熟度检查，确保项目在规模增长时保持结构化。

## 验收标准 (Acceptance Criteria)

<!-- 定义成功的二进制条件。 -->

- [x] 检查 frontmatter 中是否包含 `domains` 字段。
- [x] 检查文档语言是否与项目定义的语言匹配。

## 技术任务 (Technical Tasks)

<!-- 分解为原子步骤。对子任务使用嵌套列表。 -->

- [x] 在 `validator.py` 中添加成熟度检查逻辑。
- [x] 更新 `monoco issue lint --fix` 支持自动添加缺失的字段。

## Solution

核心治理检查已上线：

1. `validator.py` 实现了 `domains` 字段必填性检查（针对成熟项目）和语言匹配检查。
2. `linter.py` 补全了 `monoco issue lint --fix` 对 `domains: []` 的自动修复逻辑。

## Review Comments

- [x] 验证逻辑已覆盖现有 Issues。
- [x] Fixer 逻辑在 `monoco issue lint --fix` 中工作正常。

## 评审评论 (Review Comments)

<!-- Review/Done 阶段必填。在此记录评审反馈。 -->
