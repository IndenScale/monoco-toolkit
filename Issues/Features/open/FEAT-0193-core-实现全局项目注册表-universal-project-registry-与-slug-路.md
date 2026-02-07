---
id: FEAT-0193
uid: fc43a7
type: feature
status: open
stage: review
title: 'Core: 实现全局项目注册表 (Universal Project Registry) 与 Slug 路由解耦'
created_at: '2026-02-07T17:14:03'
updated_at: '2026-02-07T17:32:38'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0193'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Features/closed/FEAT-0192-courier-实现基于-url-slug-的钉钉多项目-webhook-路由与映射机制.md
- Issues/Features/open/FEAT-0192-courier-实现基于-url-slug-的钉钉多项目-webhook-路由与映射机制.md
- pyproject.toml
- src/monoco/cli/project.py
- src/monoco/cli/workspace.py
- src/monoco/core/registry.py
- src/monoco/features/courier/api.py
- src/monoco/features/courier/commands.py
- src/monoco/features/courier/constants.py
- src/monoco/features/courier/daemon.py
- src/monoco/features/courier/registry.py
- src/monoco/main.py
- uv.lock
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T17:14:03'
isolation:
  type: branch
  ref: FEAT-0193-core-实现全局项目注册表-universal-project-registry-与-slug-路
  created_at: '2026-02-07T17:14:26'
---

## FEAT-0193: Core: 实现全局项目注册表 (Universal Project Registry) 与 Slug 路由解耦

## Objective

将项目映射（Slug 路由）逻辑从 `monoco-courier` 移动到 `monoco.core`。建立一个全局统一的项目资产盘点（Universal Project Inventory），支持在全局范围内通过唯一 Slug 或目录路径对 Monoco 项目进行定位与寻址。

## Acceptance Criteria

- [x] **逻辑上移**：核心 `ProjectInventory` 逻辑位于 `monoco.core`，不再耦合于 `courier`。
- [x] **全局持久化**：注册表存储于 `~/.monoco/inventory.json`。
- [x] **原子寻址**：提供统一 API，支持根据 Slug 获取项目根目录、Mailbox 路径及配置。
- [x] **CLI 统一**：`monoco project register/list` 命令支持全局 Slugs 的操作。

## Technical Tasks

- [x] **Core 注册表设计**
  - [x] 在 `monoco.core.registry` 中实现 `ProjectInventory` 管理类。
  - [x] 定义 `~/.monoco/inventory.json` 存储结构。
- [x] **CLI 重构**
  - [x] 迁移并重写 `monoco project register` 命令，支持 `--slug` 与 `--path`。
  - [x] 迁移并重写 `monoco project list`，显示全局映射。
- [x] **Feature 解耦**
  - [x] 修改 `Courier` 以通过 Core API 消费全局注册表。
  - [x] 删除 `courier` feature 下的私有 `registry.py`。
  - [x] 移除 `monoco courier project` redundant commands.

## Review Comments

- **2026-02-07**: IndenScale 指出项目管理应是全局概念，启动重构解耦任务。
