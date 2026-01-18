---
id: FEAT-0005
type: feature
status: closed
stage: Done
title: 实现 i18n 扫描能力 (Implement i18n scan)
created_at: '2026-01-08'
solution: implemented
parent: EPIC-0004
tags:
- '#EPIC-0004'
- '#FEAT-0005'
uid: baf2ce
---

## FEAT-0005: 实现 i18n 扫描能力 (Implement i18n scan)

## 目标 (Objective)

实现 `Toolkit/skills/i18n/SKILL.md` 中定义的 i18n 质量控制能力。核心是通过 `monoco i18n scan` 命令，确保项目文档（"第一类公民"）维持多语言同步。

## 验收标准 (Acceptance Criteria)

1. **命令行入口**: 实现 `monoco i18n scan` 子命令。
2. **规则一致性**: 严格遵循系统定义的 i18n 目录与文件后缀规范。
3. **自动化检查**: 自动扫描并识别缺失翻译的源文件。
4. **忽略规则**:
   - 自动读取 `.gitignore` 排除文件。
   - 强制排除系统内定的非文档目录。
5. **输出报告**: 以权威的 `i18n` 格式输出覆盖率报告。

## 技术任务 (Technical Tasks)

- [x] **Scaffold i18n Feature**: 在 `monoco/features/` 下创建 `i18n` 模块。
- [x] **Implement File Discovery**: 实现高性能文件扫描器。
- [x] **Implement i18n Logic**:
  - [x] 实现 Suffix 模式与 Subdir 模式检测逻辑。
- [x] **CLI Integration**: 注册 `monoco i18n scan` 命令。
- [x] **Reporting**: 实现符合 Monoco 标准的 i18n 状态输出。

## Review Comments

- [x] Self-Review
