---
id: CHORE-0016
uid: 751c88
type: chore
status: closed
stage: done
title: 重构 Toolkit README 以提升清晰度与影响力
created_at: '2026-01-26T01:01:01'
opened_at: '2026-01-26T01:01:01'
updated_at: '2026-01-26T01:02:38'
closed_at: '2026-01-26T01:02:38'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0016'
files: []
---

## CHORE-0016: 重构 Toolkit README 以提升清晰度与影响力

## 目标 (Objective)
改进 Toolkit 文档，以清晰传达 "Agentic Engineering" 与 "Chat" 的价值主张差异，并正确记录 `monoco init` 和 `monoco sync` 命令，以避免关于其冗余性的歧义。

## 验收标准 (Acceptance Criteria)
- [x] README.md 已更新，价值主张清晰。
- [x] README_ZH.md 已更新，价值主张清晰。
- [x] `monoco init` 和 `monoco sync` 已在快速开始中正确记录上下文。

## 技术任务 (Technical Tasks)
- [x] 分析当前 README 和代码库以验证命令用法。
- [x] 更新 `Toolkit/README.md`。
- [x] 更新 `Toolkit/README_ZH.md`。

## 评审备注 (Review Comments)
- 验证了 `monoco init` 引导工作区，`monoco sync` 注入 agent prompts/skills。它们是独特且必要的步骤。
- 文档现在强调 "Engineering" 方面而非 "Chat"。
