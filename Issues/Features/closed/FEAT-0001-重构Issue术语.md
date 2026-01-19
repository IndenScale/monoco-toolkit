---
id: FEAT-0001
type: feature
status: closed
stage: Done
title: 重构 Issue 术语为原生代理语义 (Refactor Issue Terminology)
created_at: 2026-01-09
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0003'
- '#FEAT-0001'
- agent-native
- refactor
parent: EPIC-0003
uid: '063766'
---

## FEAT-0001: 重构 Issue 术语为原生代理语义 (Refactor Issue Terminology)

## 目标 (Objective)

将 Monoco Issue 系统从基于 Scrum/Jira 的行话 (Epic/Story/Task/Bug) 过渡到原生代理语义 (Goal/Feature/Chore/Fix)，以减少认知负荷并改善意图与执行之间的一致性。

## 背景 (Background)

正如讨论的那样，“Story”强加了一种通常不必要的叙事负担（“作为用户……”），而对于代理与人类的协作来说，直接的功能定义（“Feature”）更有效。“Task”过于通用，而“Chore”清楚地定义了维护工作。“Epic”太过于文学化；“Goal”则更直接。

## 术语映射 (Terminology Mapping)

| 旧术语 | 新术语      | ID 前缀  | 目录        |
| :----- | :---------- | :------- | :---------- |
| Epic   | **Epic**    | `EPIC-`  | `Epics/`    |
| Story  | **Feature** | `FEAT-`  | `Features/` |
| Task   | **Chore**   | `CHORE-` | `Chores/`   |
| Bug    | **Fix**     | `FIX-`   | `Fixes/`    |

## 验收标准 (Acceptance Criteria)

1. 当前代码库 (`monoco` CLI) 支持新术语。
2. 现有 Issue 迁移到新的目录结构和文件名。
3. 内部文件内容（Frontmatter `type`, 链接 `[[ID]]`）已更新。
4. 文档 (`SKILL.md`) 已更新。

## 技术任务 (Technical Tasks)

- [x] **重构代码库** (核心逻辑)
  - [x] 更新 `toolkit/monoco/features/issue/models.py` 中的 `IssueType` 和 `IssueStatus`。
  - [x] 更新 `toolkit/monoco/features/issue/commands.py` 中的 CLI 命令以接受新类型。
  - [x] 更新 Lint 逻辑以识别新目录结构。
- [x] **数据迁移**
  - [x] 重命名目录: `Epics`->`Goals`, `Stories`->`Features`, `Tasks`->`Chores`, `Bugs`->`Fixes`。
  - [x] 重命名文件: 更改前缀（例如 `FEAT-` -> `FEAT-`）。
  - [x] 批量更新文件内容: 将 `type: feature` 替换为 `type: feature` 等。
  - [x] 批量更新引用: 更新双括号链接 `[[FEAT-xx]]` -> `[[FEAT-xx]]`。
- [x] **文档**
  - [x] 重写 `Toolkit/skills/issues-management/SKILL.md` 以反映新本体论。

## Review Comments

- [x] Self-Review
