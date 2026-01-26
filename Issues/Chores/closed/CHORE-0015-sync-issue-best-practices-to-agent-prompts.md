---
id: CHORE-0015
uid: df018a
type: chore
status: closed
stage: done
title: 同步 Issue 最佳实践到 Agent 提示词
created_at: '2026-01-26T00:51:15'
opened_at: '2026-01-26T00:51:15'
updated_at: 2026-01-26 00:55:25
closed_at: '2026-01-26T00:54:36'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0015'
files:
- Issues/Chores/open/CHORE-0015-sync-issue-best-practices-to-agent-prompts.md
- monoco/features/issue/resources/en/AGENTS.md
- monoco/features/issue/resources/zh/AGENTS.md
---

## CHORE-0015: 同步 Issue 最佳实践到 Agent 提示词

## 目标 (Objective)
确保英汉双语的 Agent 指南 (AGENTS.md) 准确反映严格的 Issue 驱动开发最佳实践，特别是 "Issue First" 规则和环境清理的精确时机。

## 验收标准 (Acceptance Criteria)
- [x] 英文 AGENTS.md 包含 "Issue First" 规则。
- [x] 英文 AGENTS.md 包含正确的 prune 时机 (仅 close 时)。
- [x] 中文 AGENTS.md 包含 "Issue First" 规则。
- [x] 中文 AGENTS.md 包含正确的 prune 时机 (仅 close 时)。

## 技术任务 (Technical Tasks)

- [x] 更新 `monoco/features/issue/resources/en/AGENTS.md`
- [x] 更新 `monoco/features/issue/resources/zh/AGENTS.md`

## 评审备注 (Review Comments)
<!-- Required for Review/Done stage. Record review feedback here. -->
Self-reviewed. Changes align with GEMINI.md core principles.
