---
id: FEAT-0190
uid: 229f5e
type: feature
status: open
stage: review
title: 实现 Monoco Courier 钉钉适配器：基于受保护 Mailbox 的防抖分拣逻辑
created_at: '2026-02-06T22:24:06'
updated_at: '2026-02-07T17:55:41'
parent: EPIC-0000
dependencies:
- FEAT-0191
- FEAT-0192
- FEAT-0193
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0190'
- '#FEAT-0191'
- '#FEAT-0192'
- '#FEAT-0193'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Features/closed/FEAT-0193-core-实现全局项目注册表-universal-project-registry-与-slug-路.md
- Issues/Features/open/FEAT-0193-core-实现全局项目注册表-universal-project-registry-与-slug-路.md
- src/monoco/features/courier/adapters/dingtalk.py
- src/monoco/features/courier/api.py
- src/monoco/features/mailbox/store.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-06T22:24:06'
isolation:
  type: branch
  ref: FEAT-0190-实现-monoco-courier-钉钉适配器-基于受保护-mailbox-的防抖分拣逻辑
  created_at: '2026-02-07T17:49:23'
---

## FEAT-0190: 实现 Monoco Courier 钉钉适配器：基于受保护 Mailbox 的防抖分拣逻辑

## Objective

在 Monoco Courier 中完整实现钉钉适配器，采用 Sidecar 模式处理外部信号。基于 FEAT-0192 与 FEAT-0193 建立的多项目路由架构，确保适配器能够支持多租户分发。

核心逻辑：

1. **多租户 Webhook 接入**：通过路由 `/api/v1/courier/webhook/dingtalk/{project_slug}` 接收事件。
2. **凭证动态检索**：从 `ProjectInventory` 检索各项目的 `AppSecret` 进行签名验证。
3. **防抖分拣 (Debouncing)**：针对 IM 的流式输入，利用 `DebounceHandler` 在内存中进行窗口聚合（默认 5s 窗口，30s 最大延迟）。
4. **标准化落地**：聚合后的消息转化为 `InboundMessage` 规范并写入该项目所属的 `.monoco/mailbox/inbound/dingtalk/`。

## Acceptance Criteria

- [x] **签名验证**：`DingtalkSigner` 已实现，支持基于时间戳 and Secret 的 SHA256 签名校验。
- [x] **防抖引擎**：`DebounceHandler` 已实现，支持基于 `session_id` 的消息流合并。
- [x] **适配器封装**：完成 `DingtalkAdapter` 包装类，整合签名校验、防抖逻辑与存储逻辑。
- [x] **集成分发**：FastAPI 服务通过 `project_slug` 正确分发到对应项目的存储路径。
- [x] **Schema 遵循**：生成的 MD 文件符合 `monoco.features.connector.protocol.schema.InboundMessage` 模型。
- [x] **原子写入**：使用 `MailboxStore` 或重命名机制确保写入 `inbound` 目录的动作是原子的。

## Technical Tasks

- [x] **适配器核心实现** (`src/monoco/features/courier/adapters/dingtalk.py`)
  - [x] 补全 `DingtalkAdapter` 类。
  - [x] 实现 `handle_webhook(slug, payload, sign, timestamp)` 方法。
- [x] **API 路由桥接** (`src/monoco/features/courier/api.py`)
  - [x] 在 `CourierAPIHandler` 中注入 `DingtalkAdapter`。
  - [x] 补全 `POST /api/v1/courier/webhook/dingtalk/{project_slug}` 的逻辑。
- [x] **分发与持久化**
  - [x] 调用 `ProjectInventory` 获取项目的根路径。
  - [x] 使用 `src/monoco/features/mailbox/store.py` 将消息写入对应项目的 `inbound` 目录。
- [x] **集成验证**
  - [x] 模拟钉钉并发 Webhook 请求，验证多项目隔离写入效果。

## Review Comments

- **2026-02-06**: 由 IndenScale 确认，废弃旧的 FEAT-0168/0169，采用全新的 Mailbox 架构实现。
- **2026-02-07**: IndenScale 提出更新：因 FEAT-0191/192/193 已重构底层架构，FEAT-0190 需适配全局项目注册表与多租户路由。
- **2026-02-07**: 实现完成。包括：`DingtalkAdapter` 类、`MailboxStore.create_inbound_message()` 原子写入、`CourierAPIHandler` 集成。
