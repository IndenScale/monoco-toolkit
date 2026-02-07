---
id: FEAT-0192
uid: 909a4f
type: feature
status: open
stage: review
title: 'Courier: 实现基于 URL Slug 的钉钉多项目 Webhook 路由与映射机制'
created_at: '2026-02-07T16:56:57'
updated_at: '2026-02-07T17:07:09'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0192'
files:
- src/monoco/features/courier/adapters/dingtalk.py
- src/monoco/features/courier/api.py
- src/monoco/features/courier/commands.py
- src/monoco/features/courier/constants.py
- src/monoco/features/courier/daemon.py
- src/monoco/features/courier/registry.py
- src/monoco/features/courier/service.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T16:56:57'
isolation:
  type: branch
  ref: FEAT-0192-courier-实现基于-url-slug-的钉钉多项目-webhook-路由与映射机制
  created_at: '2026-02-07T16:57:07'
---

## FEAT-0192: Courier: 实现基于 URL Slug 的钉钉多项目 Webhook 路由与映射机制

## Objective

实现 Monoco Courier 全局单例模式下的多项目支持。通过 URL Slug 机制将钉钉 Webhook 流量分发到正确的 Workspace，并确保凭证（AppSecret）的隔离与安全校验。

## Acceptance Criteria

- [x] **多路分发 (Routing)**：支持 `/api/v1/courier/webhook/dingtalk/{project_slug}` 路由。
- [x] **凭证隔离 (Credential Isolation)**：Courier 能够根据 Slug 动态加载对应项目的 `.env` 或配置进行签名校验。
- [x] **项目投影 (Project Projection)**：接收到的消息必须原子化地写入对应项目的 `.monoco/mailbox/inbound/dingtalk/`。
- [x] **自动注册 (Auto-registration)**：Courier 启动时能扫描 Workspace 并建立 Slug 到路径的内存映射表。

## Technical Tasks

- [x] **路由注册表设计**
  - [x] 在 `CourierDaemon` 中引入 `ProjectRegistry` 模块，管理 `slug -> (path, credentials)`。
  - [x] 实现并集成 `ProjectRegistry` 持久化机制。
- [x] **Webhook 处理器重构**
  - [x] 修改 `api.py` 中的 `CourierAPIHandler`，支持动态路径参数提取。
  - [x] 实现针对 `dingtalk` 的多租户签名验证逻辑。
- [x] **CLI 管理能力**
  - [x] 增加 `monoco courier project register/list` 命令。
  - [x] 实现全局单例状态持久化在 `~/.monoco`。
- [x] **集成测试**
  - [x] 验证多项目路由与凭证隔离逻辑。

## Review Comments

- **2026-02-07**: IndenScale 提议采用 URL Path-based Multi-tenancy 方案，由 Agent 执行实现。
