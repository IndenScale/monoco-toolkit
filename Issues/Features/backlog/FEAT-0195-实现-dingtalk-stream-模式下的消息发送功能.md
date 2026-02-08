---
id: FEAT-0195
uid: 9941e7
type: feature
status: backlog
stage: freezed
title: 实现 DingTalk Stream 模式下的消息发送功能
created_at: '2026-02-08T00:04:23'
updated_at: '2026-02-08T09:27:56'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0195'
files: []
criticality: medium
solution: wontfix
opened_at: '2026-02-08T00:04:23'
---

## FEAT-0195: 实现 DingTalk Stream 模式下的消息发送功能

## Objective
在 Flow 模式下，DingTalk 应该通过 Stream 连接发送消息，而不是依赖 Webhook。当前 `DingTalkStreamAdapter.send()` 方法返回 "not implemented" 错误，导致 outbound 消息无法发送。

## Acceptance Criteria
- [ ] DingTalk Stream Adapter 能够发送消息到指定的 conversation
- [ ] Outbound 消息自动通过 Stream 连接发送
- [ ] 消息发送成功后自动归档
- [ ] 发送失败时正确进入重试/死信流程

## Technical Tasks
- [ ] 调研钉钉官方 SDK 的 OpenAPI 客户端发送消息方式
- [ ] 实现 `DingTalkStreamAdapter.send()` 方法
- [ ] 支持发送到群聊 (conversation_id)
- [ ] 支持发送到私聊 (user_id)
- [ ] 测试发送文本和 Markdown 消息
- [ ] 更新文档说明 Flow 模式下的发送机制

## 技术细节
当前代码位置：`src/monoco/features/courier/adapters/dingtalk_stream.py`

钉钉官方 SDK 提供了 `OpenAPI` 客户端，可以通过 `send_message` 或 `send_message_to_conversation` 方法发送消息。需要在 Stream Adapter 中：

1. 初始化 OpenAPI 客户端（使用 Client ID/Secret 获取 access_token）
2. 在 `send()` 方法中根据 message.to 判断是群聊还是私聊
3. 调用对应的发送 API
4. 处理发送结果

参考文档：https://open.dingtalk.com/document/isvapp-server/send-a-single-message

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
