---
id: FEAT-0116
uid: a2ad0f
type: feature
status: open
stage: draft
title: Display available domains and governance tips on issue creation
created_at: '2026-01-30T08:55:14'
updated_at: '2026-01-30T08:55:14'
parent: EPIC-0001
dependencies: []
related:
- FIX-0020
domains: []
tags:
- '#EPIC-0001'
- '#FEAT-0116'
- '#FIX-0020'
files: []
opened_at: '2026-01-30T08:55:14'
---

## FEAT-0116: Display available domains and governance tips on issue creation

## Objective
在通过 `monoco issue create` 创建新任务成功后，CLI 应自动列出当前项目中所有可用的 Domain，并向开发者（Agent）发出明确提示。

这旨在强化项目的“领域治理”意识，确保每个任务在创建之初就被分配到正确的业务板块，避免架构混乱和任务堆叠。

## Acceptance Criteria
- [ ] **信息展示**：在创建成功的反馈信息后面，列出 `Issues/Domains/` 下所有已定义的 Domain 名称。
- [ ] **治理提示**：打印一段 Agent Hint，强调正确指派 `domains` 字段的重要性。
- [ ] **空值处理**：若项目中尚未定义任何 Domain，提示开发者可以如何创建第一个 Domain。
- [ ] **交互优化**：信息展示应清晰、美观（使用 Rich 库库进行样式化）。

## Technical Tasks

### 1. 逻辑实现
- [ ] 在 `monoco.features.issue.cli.create` 命令的成功收尾处，增加扫描 `Issues/Domains/` 目录的逻辑。
- [ ] 提取所有 Markdown 文件的 stem（文件名）。

### 2. UI/UX 增强
- [ ] 格式化输出列表，例如：`Available Domains: [cyan]DomainA[/cyan], [cyan]DomainB[/cyan]`。
- [ ] 加入提示文字：`💡 Agent Hint: Ensure this issue is assigned to a proper domain in the frontmatter to maintain project health.`

### 3. 文档与规范
- [ ] 确保此行为符合 `AGENTS.md` 中关于领域创建指南的描述。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
