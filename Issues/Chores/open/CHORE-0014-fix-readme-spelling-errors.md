---
id: CHORE-0014
uid: f8fd18
type: chore
status: open
stage: review
title: Fix README spelling errors
created_at: '2026-01-24T19:37:33'
opened_at: '2026-01-24T19:37:33'
updated_at: '2026-01-25T22:58:14'
isolation:
  type: branch
  ref: feat/chore-0014-fix-readme-spelling-errors
  created_at: '2026-01-25T22:56:27'
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0014'
files: []
---

## CHORE-0014: Fix README spelling errors

## 目标
确保所有项目文档 (READMEs) 均达到专业水准，格式正确，且无拼写或结构性错误。此任务专注于打磨面向外部的文档，以维持高标准的交付质量。

## 验收标准
- [x] 根目录 `README.md` 和 `README_ZH.md` 中无拼写或语法错误。
- [x] 移除 `README_ZH.md` “快速开始”部分的冗余格式。
- [x] 验证主要 README 中的所有内部和外部链接。
- [x] 确保所有文档中术语（如 "Agentic Engineering"、"Issue as Code"）的一致性。

## 技术任务
- [x] 扫描并修复根目录 README 的拼写/语法。
  - [x] 识别 `README_ZH.md` 中的冗余内容。
  - [x] 对 `README.md` 进行全面审查。
  - [x] 对 `README_ZH.md` 进行全面审查。
- [x] 验证 `Kanban/README.md` 和 `Kanban/README_ZH.md`。
- [x] 验证 `extensions/vscode/README.md`。
- [x] 检查这 5 个文件中的所有链接。

## Review Comments
- 已修复 `README_ZH.md` 中的代码块冗余问题。
- 已验证 `Toolkit` 及子模块 `Kanban`, `extensions/vscode` 的 README 文档链接有效性。
- 拼写检查通过。
