---
id: EPIC-0005
type: epic
status: closed
stage: done
title: Monoco 服务运行时 (Monoco Server Runtime)
created_at: '2026-01-12T00:00:00'
updated_at: '2026-01-15T13:42:54'
closed_at: '2026-01-15T13:42:54'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0005'
- daemon
- infrastructure
- server
- sse
progress: 3/3
files_count: 0
uid: 598eba
---

## EPIC-0005: Monoco 服务运行时 (Monoco Server Runtime)

## 目标 (Objective)

构建常驻的 **Monoco Daemon (`monoco serve`)**，不仅作为 API Server，更是文件系统的高性能**实时视图 (Real-time View)**。它是连接底层文件系统 (FS) 与上层交互界面 (Web/TUI) 的桥梁。

## 核心职责 (Core Responsibilities)

1. **高性能缓存 (Watcher & Cache)**: 实时监听文件系统变更 (`watchdog`)，维护内存中的领域模型缓存，避免每次 API 调用都重读磁盘 IO。
2. **实时推送 (Real-time Push)**: 通过 Server-Sent Events (SSE) 或 WebSocket 向前端推送变更事件 (e.g., `issue_updated`, `spike_added`)。
3. **API 网关 (API Gateway)**: 聚合各个 Feature (Issue, Spike) 的 API 路由，提供统一的 RESTful/RPC 接口。

## 关键交付 (Key Deliverables)

1. **Daemon 宿主**: 基于 FastAPI 的服务脚手架。
2. **文件监听器 (File Watcher)**: 统一的 Watcher 服务，支持多 Feature 订阅。
3. **SSE 通道**: 稳定的事件推送机制。
4. **CORS & Security**: 前后端分离的基础安全配置。

## 子功能 (Child Features)

- [x] [[FEAT-0014]]: 实现 Issue 管理 API (Implemented core Daemon/API foundation)
- [x] [[FEAT-0012]]: 增强 CLI 与 Server 的多工作区支持 (Implemented)
- [x] **SSE 事件推送实现**: 已在 `monoco.daemon.services.Broadcaster` 与 `/api/v1/events` 中实现。
- [x] **统一文件监听服务 (Watcher Service)**: 已在 `monoco.daemon.services.IssueMonitor` 中实现，基于 `watchdog`。
- [~] FEAT-XXXX: 运行时远程交互 (Deferred: 范围与 Chassis 项目重叠，延期处理)

## Review Comments

- [x] Self-Review
