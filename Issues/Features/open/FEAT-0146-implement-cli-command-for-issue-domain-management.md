---
id: FEAT-0146
uid: 6913df
type: feature
status: open
stage: draft
title: Implement CLI Command for Issue Domain Management
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

## FEAT-0146: Implement CLI Command for Issue Domain Management

## 背景与目标

实现 Issue 域管理 CLI 命令组，提供对域的增删改查操作。当前管理域需要通过手动编辑 Markdown 文件或配置文件完成，操作繁琐且容易出错。本功能需求源自备忘录记录，需要提供便捷的命令行工具来列出、创建和管理域定义，确保正确更新 `Issues/Domains/*.md` 文件，并支持与现有 Issue 系统的无缝集成。

## Objective
Implement a CLI command group `monoco issue domain` to manage Domains (CRUD operations).

**Context**:
- Feature request from memo [02f30a].
- Need easy way to list, add, and manage domains without manually editing Markdown files or config.

## Acceptance Criteria
- [ ] `monoco issue domain list` lists all domains.
- [ ] `monoco issue domain create <name>` creates a new domain definition.
- [ ] `monoco issue domain show <name>` shows domain details.

## Technical Tasks
- [ ] Implement `monoco.cli.issue_domain` group.
- [ ] Implement `list`, `create`, `show` commands.
- [ ] Ensure it updates `Issues/Domains/*.md` correctly.

## Review Comments