---
id: CHORE-0009
uid: c750b2
type: chore
status: closed
stage: done
title: 增强 Agent 的 Issue 工作流指南
created_at: '2026-01-19T00:41:10'
opened_at: '2026-01-19T00:41:10'
updated_at: '2026-01-19T00:42:03'
closed_at: '2026-01-19T00:42:03'
parent: EPIC-0017
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0009'
- '#EPIC-0017'
---

## CHORE-0009: 增强 Agent 的 Issue 工作流指南

## 目标

<!-- 清晰地描述“为什么”和“是什么”。关注价值。 -->
更新 Agent 技能文档，明确要求在开始 Issue 时使用 `--branch`，以提高自动化效率。

## 验收标准

<!-- 定义成功的二进制条件。 -->

- [x] Agent 技能文档明确强制要求使用 `--branch`
- [x] CLI `monoco issue start --help` 包含针对 Agent 的建议

## 技术任务

<!-- 分解为原子步骤。使用嵌套列表表示子任务。 -->

- [x] 更新 `monoco/features/issue/resources/en/SKILL.md`
- [x] 更新 `monoco/features/issue/commands.py` 的帮助字符串

## Review Comments

- [x] Self-Review
