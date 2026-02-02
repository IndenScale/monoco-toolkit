---
id: FEAT-0146
uid: 6913df
type: feature
status: open
stage: draft
title: 实现 Issue 域管理 CLI 命令
created_at: '2026-02-01T20:57:08'
updated_at: '2026-02-01T20:57:08'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0146'
files: []
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
- [ ] `monoco issue domain list` 列出所有域。
- [ ] `monoco issue domain create <name>` 创建新的域定义。
- [ ] `monoco issue domain show <name>` 显示域详情。

## 技术任务
- [ ] 实现 `monoco.cli.issue_domain` 命令组。
- [ ] 实现 `list`、`create`、`show` 命令。
- [ ] 确保正确更新 `Issues/Domains/*.md` 文件。

## Review Comments