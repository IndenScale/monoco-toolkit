---
id: EPIC-0005
type: epic
status: open
stage: doing
title: Monoco 服务运行时 (Monoco Server Runtime)
created_at: 2026-01-12
tags:
  - server
  - daemon
  - sse
  - infrastructure
progress: 1/3
files_count: 0
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

## 子故事 (Child Features)

- [x] [[FEAT-0018]]: 运行时基础 (Daemon/RPC) (Done)
- [ ] [[FEAT-0006]]: SSE 事件推送实现 (In Progress)
- [ ] [[FEAT-0038]]: 统一文件监听与事件分发服务 (Watcher Service)
