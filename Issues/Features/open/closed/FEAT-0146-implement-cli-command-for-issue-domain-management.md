---
id: FEAT-0146
uid: 6913df
type: feature
status: closed
stage: done
title: 实现 Issue 域管理 CLI 命令
created_at: '2026-02-01T20:57:08'
updated_at: '2026-02-02T15:55:31'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0146'
files:
- monoco/features/issue/domain_commands.md
closed_at: '2026-02-02T15:55:31'
solution: implemented
criticality: medium
opened_at: '2026-02-01T20:57:08'
---

## FEAT-0146: 实现 Issue 域管理 CLI 命令

## 背景与目标

实现 Issue 域 (Domain) 管理 CLI 命令组，提供对域的增删改查操作。当前管理域需要通过手动编辑 Markdown 文件或配置文件完成，操作繁琐且容易出错。本功能需求源自备忘录记录，需要提供便捷的命令行工具来列出、创建和管理域定义，确保正确更新 `Issues/Domains/*.md` 文件，并支持与现有 Issue 系统的无缝集成。

## 目标
实现 `monoco issue domain` 命令组，用于管理域（CRUD 操作）。

**上下文**:
- 需求来自备忘录 [02f30a]。
- 需要一种简单的列表、添加和管理域的方法，而无需手动编辑 Markdown 文件或配置。

## 验收标准
- [x] `monoco issue domain list` 列出所有域。
- [x] `monoco issue domain create <name>` 创建新的域定义。
- [x] `monoco issue domain show <name>` 显示域详情。

## 技术任务
- [x] 实现 `monoco.cli.issue_domain` 命令组。
- [x] 实现 `list`、`create`、`show` 命令。
- [x] 确保正确更新 `Issues/Domains/*.md` 文件。

## Review Comments

### 实现总结

1. **list 命令**: 已增强，现在同时显示配置文件中的域和 `Issues/Domains/*.md` 文件中的域，展示域名称、描述、别名和文件路径。

2. **create 命令**: 已实现，支持以下功能：
   - 创建 `Issues/Domains/{name}.md` 文件，包含标准格式（定义、职责、边界、原则）
   - 自动更新 `.monoco/workspace.yaml` 配置
   - 支持 `--description`、`-alias` 等参数

3. **show 命令**: 已实现，支持：
   - 显示域的配置信息和文件路径
   - 解析并显示域文件中的各个章节
   - `--raw` 参数显示原始文件内容

### 代码变更
- 修改文件: `monoco/features/issue/domain_commands.py`
- 添加功能: `create_domain()` 和 `show_domain()` 函数
- 改进功能: `list_domains()` 和 `check_domain()` 函数