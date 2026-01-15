---
id: FEAT-0009
type: feature
status: closed
title: 建立 Spike 系统使用文档体系 (Establish Spike Docs)
created_at: '2026-01-09'
dependencies: []
related: []
solution: implemented
tags: []
parent: EPIC-0003
uid: e6fd0b
---

## FEAT-0009: 建立 Spike 系统使用文档体系

## 目标 (Objective)

为 Monoco Toolkit 的 `spike` 模块建立标准化的使用文档体系。该 Feature 旨在将分散的知识（如 `skills/git-repo-spike`）整合进统一的 `docs/` 目录，并提供中英文双语支持。

## 背景 (Context)

`monoco spike` 是用于管理临时研究性代码（Git Repo Spikes）的工具，能够方便地将外部代码库引入项目进行参考分析，同时避免污染主仓库（通过 `.gitignore` 管理）。目前相关文档散落在 `skills/` 目录中，缺乏系统性手册。

## 验收标准 (Acceptance Criteria)

1. **文档架构**: 在 `Toolkit/docs` 下建立标准的多语言目录结构（`zh/spike/`, `en/spike/`）。
2. **核心内容**: 完成 Spike System 的用户手册，涵盖：
   - 核心概念 (Spike, Repo Management)
   - 命令详解 (`init`, `add`, `remove`, `sync`, `list`)
   - 最佳实践
3. **i18n 同步**: 确保中英文文档内容的一致性。
4. **可发现性**: 更新索引文件。

## 技术任务 (Technical Tasks)

- [x] **编写文档**: 撰写 `Toolkit/docs/zh/spike/manual.md`，内容应基于但扩充于 `skills/` 中的定义。
- [x] **保留并同步 Skill**: 确保 `Toolkit/skills/git-repo-spike/zh/SKILL.md` 作为 Agent 的核心技能定义被保留，并与用户手册保持概念一致。
- [x] **翻译英文**: 撰写对应的英文手册 `Toolkit/docs/en/spike/manual.md`。
- [x] **更新索引**: 在 `README.md` 和 `README_ZH.md` 中添加指向该文档的链接。
- [x] **验证**: 使用 `monoco i18n scan` 验证。
