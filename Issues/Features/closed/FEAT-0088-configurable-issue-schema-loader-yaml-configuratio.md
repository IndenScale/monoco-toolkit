---
id: FEAT-0088
uid: b8e9d2
type: feature
status: closed
stage: done
title: 可配置 Issue Schema 加载器 (YAML 配置)
created_at: '2026-01-17T08:26:47'
opened_at: '2026-01-17T08:26:47'
updated_at: '2026-01-17T09:12:28'
closed_at: '2026-01-17T09:12:28'
parent: EPIC-0015
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0015'
- '#FEAT-0088'
path: /Users/indenscale/Documents/Projects/Monoco/Toolkit/Issues/Features/open/FEAT-0088-configurable-issue-schema-loader-yaml-configuratio.md
---

## FEAT-0088: 可配置 Issue Schema 加载器 (YAML 配置)

## 目标 (Objective)

允许用户通过 `monoco.yaml` 定义自定义的 Issue 类型、状态和工作流。
本功能将用户配置文件连接到由 `FEAT-0087` 构建的动态引擎上，真正实现系统的可配置化。

## 验收标准 (Acceptance Criteria)

- [x] **Schema 定义**: 制定 `issue.types`, `issue.statuses`, `issue.workflows` 的 YAML Schema。
- [x] **加载器实现**: 实现 `SchemaLoader`，解析并校验 `monoco.yaml`。
- [x] **覆盖机制 (Overlay)**: 支持策略加载: 默认预设 + 用户覆盖。
- [x] **集成**: 引擎启动时自动加载用户配置。
- [x] **文档**: 更新文档，提供配置示例。

## 技术任务 (Technical Tasks)

- [x] 定义配置 Schema 的 Pydantic 模型 (`monoco/features/issue/schema.py`)。
- [x] 实现 `load_issue_config(project_root)` 函数。
- [x] 实现合并策略 (Deep Merge vs Replacement)。
- [x] 更新 `commands.py` 和 `server.ts` 以尊重加载的配置（处理动态 Enum）。
- [x] 添加 `ARCH` 类型支持作为测试用例 (验证自定义类型)。

## Review Comments

- [x] Self-Review

## Delivery

<!-- Monoco Auto Generated -->

**Commits (1)**:

- `ef32197` feat(config): implement configurable issue schema loader

**Touched Files (3)**:

- `monoco/core/config.py`
- `monoco/features/issue/engine/__init__.py`
- `tests/features/issue/test_config_integration.py`
