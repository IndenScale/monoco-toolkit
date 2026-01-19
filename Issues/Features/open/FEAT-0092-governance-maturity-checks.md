---
id: FEAT-0092
uid: bf8436
type: feature
status: open
stage: draft
title: Governance Maturity Checks
created_at: "2026-01-19T11:12:33"
opened_at: "2026-01-19T11:12:33"
updated_at: "2026-01-19T11:12:33"
domains: []
dependencies: []
related: []
tags:
  - "#FEAT-0092"
files: []
# parent: <EPIC-ID>   # 可选：父级 Issue ID
# solution: null      # 关闭状态（已实现、已取消等）必填
---

## FEAT-0092: Governance Maturity Checks

## 目标 (Objective)

<!-- 清晰描述 “为什么” 和 “是什么”。专注于价值。 -->

实现自动化的治理成熟度检查，确保项目在规模增长时保持结构化。

## 验收标准 (Acceptance Criteria)

<!-- 定义成功的二进制条件。 -->

- [ ] 检查 frontmatter 中是否包含 `domains` 字段。
- [ ] 检查文档语言是否与项目定义的语言匹配。

## 技术任务 (Technical Tasks)

<!-- 分解为原子步骤。对子任务使用嵌套列表。 -->

- [ ] 在 `validator.py` 中添加成熟度检查逻辑。
- [ ] 更新 `monoco issue lint --fix` 支持自动添加缺失的字段。

## 评审评论 (Review Comments)

<!-- Review/Done 阶段必填。在此记录评审反馈。 -->
