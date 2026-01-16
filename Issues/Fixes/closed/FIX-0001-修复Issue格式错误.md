---
id: FIX-0001
type: fix
status: closed
stage: Done
title: 修复 Issue 格式错误 (Fix Issue Formatting Errors)
created_at: '2026-01-09'
dependencies: []
related:
- FEAT-0009
solution: implemented
tags: []
parent: EPIC-0002
uid: dca954
---

## FIX-0001: 修复 Issue 格式错误 (Fix Issue Formatting Errors)

## 目标 (Objective)

修复 `monoco issue` 命令输出中的格式错误，以确保干净、有效的 Markdown 和文件名。

近期使用（例如 `FEAT-0009`）生成的文件存在以下问题：

1. **文件名中的重复连字符**: (例如 `FEAT-0009--spike-.md`)。
2. **生成的正文中缺少标题内容**: 。
3. **错误的转义序列**: 插入 `\n` 字面量而不是实际的换行符。
4. **Frontmatter 中的日期引用问题**: (例如不一致或错误的引号使用)。

## 验收标准 (Acceptance Criteria)

- [x] Issue 文件名被清晰地 Slug 化（无双连字符，无尾随连字符）。
- [x] 生成的 Markdown 内容具有正确的格式（标题、间距）。
- [x] 模板或用户输入中的换行符被正确渲染，而不是作为转义字面量。
- [x] Frontmatter 中的日期字段格式一致（标准化为单引号/双引号或无引号）。

## 技术任务 (Technical Tasks)

- [x] 调试 `Toolkit` 中的 `monoco issue create` 命令实现。
- [x] 修复标题处理/Slug 化逻辑。
- [x] 修复模板渲染引擎以正确处理转义序列。
- [x] 通过创建一个带有特殊字符和空格的测试 Issue 来验证修复。
- [x] Frontmatter 中的日期字段格式一致（标准化为单引号/双引号或无引号）。

## Review Comments

- [x] Self-Review
