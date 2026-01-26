---
id: CHORE-0017
uid: eb92ec
type: chore
status: closed
stage: done
title: 更新 README 工作流为 Agent 优先
created_at: '2026-01-26T01:05:52'
opened_at: '2026-01-26T01:05:52'
updated_at: '2026-01-26T01:06:42'
closed_at: '2026-01-26T01:06:42'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0017'
files: []
---

## CHORE-0017: 更新 README 工作流为 Agent 优先

## 目标 (Objective)
更新 README 中的 "工程闭环" 章节，以反映 Agent 优先的工作流 (Chat -> Plan -> Build -> Ship)，而非手动 CLI 使用。用户不应需要为日常工作学习 CLI API。

## 验收标准 (Acceptance Criteria)
- [x] README.md 步骤 4 简化为 Agent 交互。
- [x] README_ZH.md 步骤 4 简化为 Agent 交互。
- [x] 从执行循环描述中移除了 CLI 命令。

## 技术任务 (Technical Tasks)
- [x] 重写 `Toolkit/README.md` 中的 "The Engineering Loop"。
- [x] 重写 `Toolkit/README_ZH.md` 中的 "工程闭环"。

## 评审备注 (Review Comments)
- 更新了文档以强调 Agent 充当 DevOps 工程师，处理底层 CLI 命令。
- 流程现在是：Chat -> Plan (Ticket) -> Review -> Build (Branch/Code) -> Ship (Merge/Close)。
