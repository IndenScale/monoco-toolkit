---
id: FEAT-0169
uid: 75ef5b
type: feature
status: open
stage: draft
title: 钉钉平台适配器：Webhook 与卡片消息
created_at: '2026-02-03T23:23:34'
updated_at: '2026-02-03T23:23:34'
parent: EPIC-0033
dependencies:
- FEAT-0167
domains:
- CollaborationBus
tags:
- '#EPIC-0033'
- '#FEAT-0167'
- '#FEAT-0169'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T23:23:34'
---

## FEAT-0169: 钉钉平台适配器：Webhook 与卡片消息

## Objective
实现钉钉平台的完整适配器，支持 Stream 模式事件接收、机器人消息发送和卡片交互。

### 集成范围
- **Stream 模式**: 使用钉钉 Stream Client 实时接收消息
- **Webhook 模式**: 支持 HTTP Webhook 作为备选
- **消息发送**: 支持文本、Markdown、ActionCard、InteractiveCard
- **群机器人**: 支持 Incoming Webhook 和 Outgoing 机器人

## Acceptance Criteria
- [ ] 实现钉钉 Stream Client 连接
- [ ] 实现消息接收与解析
- [ ] 实现消息发送（文本、Markdown、卡片）
- [ ] 实现卡片交互回调处理
- [ ] 支持企业内部应用和群机器人两种模式
- [ ] 支持加密签名验证

## Technical Tasks
- [ ] 创建 `monoco/features/im/platforms/dingtalk.py`
  - [ ] `DingtalkAdapter` 实现
  - [ ] Stream Client 封装
  - [ ] Webhook 模式支持
  - [ ] 消息格式转换（钉钉 → IMMessage）
- [ ] 实现钉钉 Stream 连接
  - [ ] Card 消息接收
  - [ ] 自动重连机制
  - [ ] 多 Worker 支持
- [ ] 创建 Webhook 端点 `/api/v1/im/webhook/dingtalk`
  - [ ] 签名验证
  - [ ] 事件分发
- [ ] 实现钉钉 API 客户端
  - [ ] 获取 AccessToken
  - [ ] 发送工作通知
  - [ ] 发送群消息
  - [ ] 更新卡片消息
- [ ] 钉钉特有功能
  - [ ] ActionCard（整体跳转、独立跳转）
  - [ ] InteractiveCard（交互式卡片）
  - [ ] Markdown 消息
  - [ ] @用户高亮

## API 集成清单
- [ ] **Stream 模式**
  - 使用 `dingtalk-stream-sdk` 建立长连接
  - 处理 `chat.chat_message_received` 事件
- [ ] **机器人 API**
  - `POST /robot/send` - 群机器人发送
  - `POST /message/workNotification` - 工作通知
- [ ] **卡片交互**
  - 处理 `interactive_card_callback` 事件

## Configuration
```yaml
# project.yaml
im:
  dingtalk:
    app_key: "ding_xxxxxxxx"
    app_secret: "encrypted:..."
    client_id: "..."
    client_secret: "encrypted:..."
    mode: "stream"  # stream 或 webhook
    robot_code: "..."  # 群机器人
```

## Review Comments
