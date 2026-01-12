---
id: FEAT-0008
type: feature
status: closed
title: 建立 Issue 系统使用文档体系 (Establish Issue Docs)
created_at: "2026-01-09"
dependencies: []
related: []
solution: implemented
tags: [docs, i18n, issue]
parent: EPIC-0002
---

## FEAT-0008: 建立 Issue 系统使用文档体系

## 目标 (Objective)

为 Monoco Toolkit 的核心模块——Issue System——建立标准化的使用文档体系。该 Feature 不涉及 CLI 工具的开发，而是专注于内容的创作、架构的搭建以及多语言（i18n）版本的同步。

## 背景 (Context)

Issue System 功能日益完善（包含 Create, Open, Close, Backlog, Scope, Lint 等命令），但缺乏系统性的用户文档。为了降低使用门槛并规范团队协作，我们需要产出一套高质量、双语（中文/英文）的使用手册，并将其集成到项目的 `docs/` 目录架构中。

## 验收标准 (Acceptance Criteria)

1. **文档架构**: 在 `Toolkit/docs` 下建立标准的多语言目录结构（`zh/`, `en/`）。
2. **核心内容**: 完成 Issue System 的用户手册，包含：
   - 快速开始 (Quick Start)
   - 命令详解 (Command Reference)
   - 最佳实践 (Best Practices, 结合 SKILL.md)
3. **i18n 同步**: 确保中英文文档内容的一致性。
4. **可发现性**: 用户能通过项目根目录的 README 或索引文件轻松找到该文档。

## 技术任务 (Technical Tasks)

- [x] **初始化 Docs 结构**: 创建 `Toolkit/docs/{zh,en}/issue/` 目录。
- [x] **编写中文手册**: 基于 `issues-management/SKILL.md` 和现有代码，撰写详细的中文使用指南。
- [x] **翻译英文手册**: 将中文手册翻译为英文，确保术语准确（如 Epic, Feature, Chore）。
- [x] **更新索引**: 在 `README.md` 或顶层索引中添加指向该文档的链接。
- [x] **验证**: 使用 `monoco i18n scan` 验证文档的多语言覆盖率（如果适用）。
