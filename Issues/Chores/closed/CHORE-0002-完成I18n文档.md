---
id: CHORE-0002
type: chore
status: closed
stage: done
title: 完善 monoco i18n 命令文档 (Complete i18n Docs)
created_at: '2026-01-09'
solution: implemented
domains: []
tags:
- '#CHORE-0002'
- '#EPIC-0001'
- cli
- documentation
- i18n
parent: EPIC-0001
uid: 7e54fe
---

## CHORE-0002: 完善 monoco i18n 命令文档 (Complete i18n Docs)

## 目标 (Objective)

完善 `monoco i18n` 命令的文档体系，包括 CLI 内建帮助信息和用户手册。确保用户能够清晰理解和使用 i18n 扫描能力，维护项目文档的多语言质量。

## 验收标准 (Acceptance Criteria)

1.  **CLI Help 增强**:
    - `monoco i18n --help` 提供清晰的命令描述。
    - `monoco i18n scan --help` 详细说明参数（如 `--root`）和输出含义。
2.  **用户手册**:
    - 创建 `Toolkit/docs/zh/i18n/manual.md`，详细介绍 i18n 系统规范、命令使用方法及常见问题。
    - 手册内容需包含 `Suffix 模式` 和 `Subdir 模式` 的示例说明。
3.  **文档索引**:
    - 在 `Toolkit/README.md` 或相关索引页添加 i18n 手册的链接。

## 技术任务 (Technical Tasks)

- [x] **增强 CLI 文档字符串**: 优化 `Toolkit/monoco/features/i18n/commands.py` 中的 help 文本。
- [x] **创建用户手册**: 撰写 `Toolkit/docs/zh/i18n/manual.md`。
- [x] **更新索引**: 更新项目文档索引，纳入 i18n 手册。

## Review Comments

- [x] Self-Review
