---
id: CHORE-0020
type: chore
status: closed
stage: done
title: 为 Monoco Memo 添加 Agent Skill
parent: EPIC-0000
solution: implemented
domains: []
files:
- .claude/skills/monoco_memo/SKILL.md
- AGENTS.md
tags:
- '#CHORE-0020'
- '#EPIC-0000'
---

## CHORE-0020: 为 Monoco Memo 添加 Agent Skill

创建一个 Agent Skill (`monoco-memo`)，教导代理如何正确使用轻量级备忘录系统，将其与正式的 Issue 系统区分开来。

### 背景

代理目前缺乏关于 `monoco memo` 的知识，导致误用（例如尝试将其用于工单）或忽视该功能。

### 任务

- [x] **创建 Skill 文件**: `Toolkit/monoco/skills/monoco-memo/SKILL.md`
    - 描述用途：快速记录、想法捕捉。
    - 记录命令：`monoco memo add`、`monoco memo list`。
    - 与 Issue 区分："使用 Memos 记录想法；使用 Issues 处理可执行任务。"
- [x] **更新文档**:
    - 在 `Toolkit/GEMINI.md` 或 `AGENTS.md` 中添加对 `monoco-memo` skill 的引用。

### R e

- [x] 新的 `SKILL.md` 存在且有效。
- [x] 代理指令明确定义何时使用 Memo 与 Issue。

## Review Comments

- [x] Verified by Agent.
