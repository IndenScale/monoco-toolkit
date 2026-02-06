---
id: FEAT-0190
uid: 229f5e
type: feature
status: open
stage: doing
title: 实现 Monoco Courier 钉钉适配器：基于受保护 Mailbox 的防抖分拣逻辑
created_at: '2026-02-06T22:24:06'
updated_at: '2026-02-06T22:24:44'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0190'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-06T22:24:06'
---

## FEAT-0190: 实现 Monoco Courier 钉钉适配器：基于受保护 Mailbox 的防抖分拣逻辑

## Objective

在 Monoco Courier 中实现钉钉适配器，采用 Sidecar 模式处理外部信号。
核心逻辑：

1. **Webhook 接入**：启动 FastAPI 服务接收钉钉事件。
2. **防抖分拣 (Debouncing)**：针对 IM 的流式输入，在内存或轻量缓存中进行窗口聚合（默认 30s）。
3. **标准化落地**：聚合后的消息转化为 ADR-003 规范的 Markdown 格式并写入受保护的 `.monoco/mailbox/inbound/dingtalk/`。

## Acceptance Criteria

- [ ] **服务启动**：Courier 能够独立或作为 Sidecar 启动钉钉 Webhook 监听服务。
- [ ] **签名验证**：正确处理钉钉 Webhook 的加密与签名校验。
- [ ] **防抖逻辑**：连续发送的 IM 消息在 30s 内被聚合为同一个“Mail”文件。
- [ ] **Schema 遵循**：生成的 MD 文件符合 `InboundMessage` Pydantic 模型。
- [ ] **原子写入**：使用重命名机制确保写入 `inbound` 目录的动作是原子的。

## Technical Tasks

- [ ] **基础框架搭建**
  - [ ] 实现 `DingtalkAdapter` 基础类。
  - [ ] 集成 FastAPI 接收 `/api/v1/courier/webhook/dingtalk`。
- [ ] **防抖缓冲引擎**
  - [ ] 设计基于 `session.id` 的内存队列缓存。
  - [ ] 实现定时器逻辑：当 `session.id` 超过 30s 无新消息时触发 Flash 动作。
- [ ] **格式化与持久化**
  - [ ] 调用 `monoco.mailbox.schema` 构造标准消息对象。
  - [ ] 实现 `.monoco/mailbox/inbound/dingtalk/` 的目录自动创建与写入逻辑。
- [ ] **集成测试**
  - [ ] 模拟钉钉并发 Webhook 请求，验证防抖合并效果。

## Review Comments

- **2026-02-06**: 由 IndenScale 确认，废弃旧的 FEAT-0168/0169，采用全新的 Mailbox 架构实现。
