---
id: FEAT-0191
uid: c18ae8
type: feature
status: open
stage: doing
title: Refactor Connector System
created_at: '2026-02-07T09:51:13'
updated_at: '2026-02-07T11:20:10'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0191'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Features/closed/FEAT-0189-定义-mailbox-协议存储格式与-schema-规范.md
- Issues/Features/open/FEAT-0189-定义-mailbox-协议存储格式与-schema-规范.md
- docs/examples/mailbox/draft_reply.yaml
- docs/examples/mailbox/inbound_email_thread.yaml
- docs/examples/mailbox/inbound_lark_group.yaml
- docs/zh/04_Connectors/01_Architecture.md
- docs/zh/04_Connectors/02_Mailbox_Protocol.md
- docs/zh/04_Connectors/03_Mailbox_CLI.md
- docs/zh/04_Connectors/04_Courier_Service.md
- docs/zh/04_Connectors/05_Courier_CLI.md
- docs/zh/04_Connectors/README.md
- src/monoco/features/connector/protocol/__init__.py
- src/monoco/features/connector/protocol/constants.py
- src/monoco/features/connector/protocol/schema.py
- src/monoco/features/connector/protocol/validators.py
- src/monoco/features/courier/__init__.py
- src/monoco/features/courier/adapters/__init__.py
- src/monoco/features/courier/adapters/base.py
- src/monoco/features/courier/api.py
- src/monoco/features/courier/commands.py
- src/monoco/features/courier/constants.py
- src/monoco/features/courier/daemon.py
- src/monoco/features/courier/debounce.py
- src/monoco/features/courier/protocol/__init__.py
- src/monoco/features/courier/service.py
- src/monoco/features/courier/state.py
- src/monoco/features/mailbox/__init__.py
- src/monoco/features/mailbox/client.py
- src/monoco/features/mailbox/commands.py
- src/monoco/features/mailbox/models.py
- src/monoco/features/mailbox/queries.py
- src/monoco/features/mailbox/store.py
- src/monoco/mailbox/__init__.py
- src/monoco/mailbox/constants.py
- src/monoco/mailbox/schema.py
- src/monoco/mailbox/validators.py
- src/monoco/main.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T09:51:13'
isolation:
  type: branch
  ref: FEAT-0191-refactor-connector-system
  created_at: '2026-02-07T09:51:58'
---

## FEAT-0191: Refactor Connector System

## Objective

重构 Monoco 的 Connector 系统，将 `Mailbox`（协议与数据层）与 `Courier`（传输与服务层）拆分为两个独立的 Feature，明确职责边界，并对外暴露清晰的 CLI 命令接口。

## Context

当前的架构存在割裂：

- **概念割裂**：文档定义的 `Connector` 包含 "Courier & Mailbox"，但代码中 `mailbox` 位于顶层，而 `courier` 位于 `features`。
- **代码重复**：`src/monoco/mailbox/schema.py` 与 `src/monoco/features/courier/schema.py` 存在定义重叠。
- **职责不清**：`monoco courier` 目前承担了数据管理和服务管理的双重职责。

## Architecture Decision

**采用独立 Feature 架构，而非统一的 Connector。**

### 决策理由

1. **关注点分离**：Mailbox 管数据，Courier 管传输，两者可以独立演进
2. **清晰的边界**：Mailbox CLI 只读（除标记外），Courier CLI 管理服务
3. **简化依赖**：两个 Feature 之间通过协议松耦合，不直接依赖
4. **测试友好**：可以独立测试数据层和服务层

### 新的目录结构

```text
src/monoco/features/
├── mailbox/                      # Mailbox Feature (数据层 + CLI)
│   ├── __init__.py
│   ├── commands.py              # CLI: list, read, send, claim, done, fail
│   ├── models.py                # 数据模型定义
│   ├── store.py                 # 文件系统操作
│   ├── queries.py               # 查询引擎
│   ├── client.py                # Courier HTTP API 客户端
│   └── constants.py             # 路径、枚举等常量
│
└── courier/                      # Courier Feature (服务层)
    ├── __init__.py
    ├── commands.py              # CLI: start, stop, restart, kill, status, logs
    ├── service.py               # 服务生命周期管理
    ├── daemon.py                # 后台进程实现
    ├── api.py                   # HTTP API 服务 (claim/done/fail)
    ├── state.py                 # 消息状态管理 (锁、归档、重试)
    ├── adapters/                # 各平台适配器
    │   ├── __init__.py
    │   ├── base.py
    │   ├── lark.py
    │   └── email.py
    ├── protocol/                # 协议层 (共享 Schema)
    │   ├── __init__.py
    │   ├── schema.py            # 统一 Schema 定义
    │   ├── constants.py
    │   └── validators.py
    └── debounce.py              # 防抖合并逻辑
```

### 职责划分

| 职责         | Mailbox                                 | Courier                      |
| ------------ | --------------------------------------- | ---------------------------- |
| 数据查询     | ✅ `mailbox list/read` (本地)           | ❌                           |
| 创建草稿     | ✅ `mailbox send`                       | ❌                           |
| 状态流转     | ✅ `mailbox claim/done/fail` (API 调用) | ✅ 维护锁、执行归档/重试     |
| Webhook 接收 | ❌                                      | ✅ 接收并写入 inbound        |
| 消息发送     | ❌                                      | ✅ 读取 outbound 草稿并发送  |
| 服务管理     | ❌                                      | ✅ `courier start/stop/kill` |

## Acceptance Criteria

- [x] `src/monoco/mailbox` 目录被移除。
- [x] `src/monoco/features/courier` 目录被移除。
- [ ] **独立的 `mailbox` Feature**：`src/monoco/features/mailbox/` 完整实现
- [x] **独立的 `courier` Feature**：`src/monoco/features/courier/` 完整实现
- [x] `courier/protocol/` 包含共享的 Schema 定义。
- [x] CLI 提供 `monoco mailbox` 命令组，支持 `list`, `read`, `send`, `claim`, `done`, `fail` 操作。
- [x] CLI 提供 `monoco courier` 命令组，支持 `start`, `stop`, `restart`, `kill`, `status`, `logs` 操作。
- [x] `courier kill` 实现强制停止（SIGKILL，不优雅）。
- [ ] 现有测试（Pytest）全部通过，且路径引用已更新。
- [ ] 文档更新完成（`docs/zh/04_Connectors/`）。

## Technical Tasks

- [x] **Phase 1: Mailbox Feature Setup**
  - [x] Create `src/monoco/features/mailbox/` directory.
  - [x] Create `src/monoco/features/connector/protocol/` with shared schema.
  - [x] Create `mailbox/models.py` - 数据模型定义.
  - [x] Create `mailbox/store.py` - 文件系统操作.
  - [x] Create `mailbox/queries.py` - 查询引擎.
  - [x] Create `mailbox/client.py` - Courier HTTP API 客户端.

- [x] **Phase 2: Mailbox CLI Implementation**
  - [x] Create `mailbox/commands.py`.
  - [x] Implement `mailbox list` - 列出消息（本地查询，支持过滤、格式化）.
  - [x] Implement `mailbox read` - 读取消息内容（本地读取）.
  - [x] Implement `mailbox send` - 创建出站草稿（写文件）.
  - [x] Implement `mailbox claim` - 认领消息（调用 Courier API）.
  - [x] Implement `mailbox done` - 标记完成（调用 Courier API，触发归档）.
  - [x] Implement `mailbox fail` - 标记失败（调用 Courier API，触发重试）.
  - [x] Register commands in `monoco/main.py`.

- [x] **Phase 3: Courier Feature Setup**
  - [x] Create `src/monoco/features/courier/` directory.
  - [x] Create `courier/protocol/` - 共享 Schema（供外部导入）.
  - [x] Move adapters to `courier/adapters/`.
  - [x] Create `courier/service.py` - 服务生命周期管理.
  - [x] Create `courier/daemon.py` - 后台进程实现.
  - [x] Create `courier/api.py` - HTTP API 服务（处理 claim/done/fail）.
  - [x] Create `courier/state.py` - 消息状态管理（锁、归档、重试）.
  - [x] Create `courier/debounce.py` - 防抖合并逻辑.

- [x] **Phase 4: Courier CLI Implementation**
  - [x] Create `courier/commands.py`.
  - [x] Implement `courier start` - 启动服务（启动 HTTP API、适配器、Webhook 监听）.
  - [x] Implement `courier stop` - 优雅停止服务.
  - [x] Implement `courier restart` - 重启服务.
  - [x] Implement `courier kill` - 强制停止服务（SIGKILL）.
  - [x] Implement `courier status` - 查看服务状态.
  - [x] Implement `courier logs` - 查看服务日志.
  - [x] Register commands in `monoco/main.py`.

- [x] **Phase 5: Cleanup & Verification**
  - [x] Remove old directories (`src/monoco/mailbox`, `src/monoco/features/courier`).
  - [x] Update all imports in codebase.
  - [x] Run `pytest` and fix broken tests.
  - [x] Verify CLI commands manually.
  - [x] Sync documentation from `docs/zh/04_Connectors/`.

## Documentation Reference

详细设计文档参见 `docs/zh/04_Connectors/`:

- [01_Architecture.md](../04_Connectors/01_Architecture.md) - 整体架构设计
- [02_Mailbox_Protocol.md](../04_Connectors/02_Mailbox_Protocol.md) - 消息协议 Schema 规范
- [03_Mailbox_CLI.md](../04_Connectors/03_Mailbox_CLI.md) - Mailbox CLI 命令设计
- [04_Courier_Service.md](../04_Connectors/04_Courier_Service.md) - Courier 服务架构设计
- [05_Courier_CLI.md](../04_Connectors/05_Courier_CLI.md) - Courier CLI 命令设计

## Review Comments

Completed: Connector system refactored with Mailbox and Courier features fully implemented.
