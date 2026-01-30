---
id: CHORE-0021
uid: 797c31
type: chore
status: open
stage: review
title: 清理冗余的 Skills 模块并整合 monoco-flow 技能
created_at: '2026-01-30T14:38:17'
updated_at: '2026-01-30T14:39:53'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0021'
- '#EPIC-0000'
files:
- monoco/features/issue/resources/en/SKILL.md
- monoco/features/issue/resources/zh/SKILL.md
- monoco/features/skills/__init__.py
- monoco/features/skills/core.py
- monoco/skills/monoco-flow/SKILL.md
criticality: low
opened_at: '2026-01-30T14:38:17'
isolation:
  type: branch
  ref: feat/chore-0021-cleanup-redundant-skills-module-and-consolidate-mo
  created_at: '2026-01-30T14:38:23'
---

## CHORE-0021: 清理冗余的 Skills 模块并整合 monoco-flow 技能

## Objective
清理项目中的遗留冗余模块 `monoco/features/skills`，并将其功能与 `monoco-flow` 技能整合到现有的 `monoco-issue` 系统中，以符合当前的 Workspace 架构。

## Acceptance Criteria
- [ ] `monoco/features/skills` 目录及其内容完全删除。
- [ ] `monoco/skills/monoco-flow` 的核心内容（流程图与核心概念）已合并至 `monoco/features/issue/resources/{lang}/SKILL.md`。
- [ ] `monoco/skills` 目录清理干净。
- [ ] 运行 `uv run monoco issue lint` 无报错。

## Technical Tasks
- [x] 删除冗余模块
    - [x] 删除 `monoco/features/skills/` 目录
- [x] 整合 Skill 内容
    - [x] 将 `monoco/skills/monoco-flow/SKILL.md` 的内容合并到 `monoco/features/issue/resources/en/SKILL.md`
    - [x] 如果存在对应中文版本，同步合并至 `monoco/features/issue/resources/zh/SKILL.md`
- [x] 清理遗留目录
    - [x] 删除 `monoco/skills/` 目录
- [x] 验证
    - [x] 运行 `monoco issue sync-files`
    - [x] 运行 `monoco issue lint`

## Review Comments
- 删除了孤儿模块 `monoco/features/skills`，该模块原先包含硬编码逻辑且未被注册，与当前 Discovery 架构冲突。
- 整合了 `monoco-flow` 到 `monoco-issue` 技能中，并在英、中两个版本的技能文档中添加了“标准化工作流”章节，包含 Mermaid 状态机图示。
- 清理了根目录下的 `monoco/skills` 遗留目录。
