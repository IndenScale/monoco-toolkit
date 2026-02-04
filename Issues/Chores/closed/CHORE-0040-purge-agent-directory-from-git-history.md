---
id: CHORE-0040
uid: ef68d5
type: chore
status: closed
stage: done
title: Purge .agent directory from git history
created_at: '2026-02-04T22:33:33'
updated_at: '2026-02-04T22:33:33'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0040'
- '#EPIC-0000'
files: []
criticality: low
solution: implemented # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T22:33:33'
---

## CHORE-0040: Purge .agent directory from git history

## Objective
从 Git 历史中彻底删除 `.agent` 目录及其内容。虽然该目录已加入 `.gitignore`，但之前的部分文件已被追踪，需要通过重写历史的方式将其完全抹除，以保持仓库整洁并符合隐私要求。

## Acceptance Criteria
- [x] .agent 目录已从当前索引中移除。
- [x] Git 历史中不再包含任何 .agent 相关的提交记录（使用 git filter-repo）。
- [x] .gitignore 中的配置保持正确（已确保包含 .agent）。

## Technical Tasks
- [x] 创建并确认 Issue。
- [x] 备份当前未提交的变更。
- [x] 使用 git filter-repo 执行历史清理：git filter-repo --path .agent --invert-paths。
- [x] 验证清理结果。
- [x] 更新 Issue 状态并闭环。

## Review Comments
- [x] 已通过 `git filter-repo` 彻底移除历史提交记录。
- [x] 本地目录已清理并备份至 `.agent_backup`。
- [x] Stash 已恢复，未提交变更安全。

