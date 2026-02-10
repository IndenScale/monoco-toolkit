---
id: FEAT-0167
uid: 68dadf
type: feature
status: closed
stage: done
title: IM 基础设施：核心数据模型与存储
created_at: '2026-02-03T23:23:32'
updated_at: '2026-02-03T23:58:00'
parent: EPIC-0033
dependencies: []
related:
- FEAT-0170
domains:
- Foundation
tags:
- '#EPIC-0033'
- '#FEAT-0167'
- '#FEAT-0170'
files: []
criticality: high
solution: implemented
opened_at: '2026-02-03T23:23:32'
isolation:
  type: branch
  ref: feat/feat-0167-im-基础设施-核心数据模型与存储
  path: null
  created_at: '2026-02-03T23:44:33'
---

## FEAT-0167: IM 基础设施：核心数据模型与存储

## Objective
定义 IM 系统的核心数据模型，建立独立于 Memo 的存储架构，为平台适配和 Agent 集成提供基础。

### 关键设计决策
- IMMessage 与 Memo 完全独立，不继承、不转换
- 存储结构独立于 .monoco/memos/，使用 .monoco/im/
- 支持富媒体内容（图片、卡片、文件）
- 内置会话上下文窗口管理

## Acceptance Criteria
- [x] 定义 IMChannel、IMMessage、IMParticipant 核心模型
- [x] 实现 IM 独立存储目录结构 (.monoco/im/)
- [x] 实现消息持久化存储 (JSONL 格式)
- [x] 实现频道注册与会话管理
- [x] 定义 AgentEventType.IM_* 事件类型
- [x] 实现 IMWatcher 监控消息流入

## Technical Tasks
- [x] 创建 `monoco/features/im/models.py`
  - [x] `PlatformType` 枚举 (feishu, dingtalk, slack)
  - [x] `IMChannel` 模型 - 频道/群聊信息
  - [x] `IMMessage` 模型 - 消息内容
  - [x] `IMParticipant` 模型 - 参与者信息
  - [x] `MessageContent` 模型 - 支持富媒体
  - [x] `IMAgentSession` 模型 - Agent 会话绑定
- [x] 创建 `monoco/features/im/core.py`
  - [x] `IMChannelManager` - 频道管理
  - [x] `MessageStore` - 消息存储
  - [x] `IMRouter` - 消息路由决策
- [x] 创建 `monoco/core/watcher/im.py`
  - [x] `IMWatcher` - 消息事件监控
  - [x] 发布 `IM_MESSAGE_RECEIVED` 事件
- [x] 扩展 `monoco/core/scheduler/events.py`
  - [x] `IM_MESSAGE_RECEIVED`
  - [x] `IM_MESSAGE_REPLIED`
  - [x] `IM_AGENT_TRIGGER`
  - [x] `IM_SESSION_STARTED`
  - [x] `IM_SESSION_CLOSED`
- [x] 创建 `.monoco/im/` 目录结构
  - [x] `channels.jsonl` - 频道注册表
  - [x] `messages/` - 消息历史
  - [x] `sessions/` - Agent 会话
  - [x] `webhooks/` - 平台配置

## Data Model Design

```python
class IMChannel(BaseModel):
    channel_id: str
    platform: PlatformType
    channel_type: str  # group, private, thread
    name: Optional[str]
    project_binding: Optional[str]
    context_window: int = 10
    participants: List[IMParticipant]
    auto_reply: bool = True
    default_agent: Optional[str]
    require_mention: bool = True

class IMMessage(BaseModel):
    message_id: str
    channel_id: str
    platform: PlatformType
    sender: IMParticipant
    content: MessageContent
    timestamp: datetime
    reply_to: Optional[str]
    thread_id: Optional[str]
    mentions: List[str]
    status: MessageStatus  # received / routing / agent_processing / replied / error
    processing_log: List[ProcessingStep]
    # 可选关联（非必须）
    linked_memo_id: Optional[str]
    linked_issue_id: Optional[str]

class MessageContent(BaseModel):
    type: Literal["text", "image", "card", "file", "mixed"]
    text: Optional[str]
    attachments: List[Attachment]
    platform_raw: dict
```

## Review Comments

### 实现总结

本次实现完成了 IM 系统的基础设施层，建立了独立于 Memo 的数据模型和存储架构。

#### 已完成的工作

1. **核心数据模型** (`monoco/features/im/models.py`):
   - 定义了 6 个枚举类型: PlatformType, ChannelType, MessageStatus, ParticipantType, ContentType
   - 实现了 8 个核心模型: IMParticipant, Attachment, MessageContent, ProcessingStep, IMMessage, IMChannel, IMAgentSession, IMWebhookConfig, IMStats
   - 支持富媒体内容 (text/image/card/file/mixed)
   - 内置处理状态追踪和处理日志

2. **核心管理类** (`monoco/features/im/core.py`):
   - IMChannelManager: 频道 CRUD、参与者管理、项目绑定
   - MessageStore: JSONL 格式消息存储、上下文窗口查询
   - IMRouter: 基于 mentions/keywords 的消息路由决策
   - IMAgentSessionManager: Agent 会话生命周期管理、超时清理
   - IMManager: 统一入口点，自动初始化存储目录

3. **IMWatcher** (`monoco/core/watcher/im.py`):
   - IMWatcher: 基础消息监控，支持自定义触发条件
   - IMInboundWatcher: 入站消息专用监控，过滤 agent/bot 消息
   - IMWebhookWatcher: Webhook 配置变更监控

4. **事件系统扩展**:
   - 添加了 6 个 IM 事件类型到 AgentEventType
   - 事件自动发布到 EventBus

5. **存储目录结构**:
   - `.monoco/im/channels.jsonl`: 频道注册表
   - `.monoco/im/messages/`: 按频道分片的 JSONL 消息文件
   - `.monoco/im/sessions/`: Agent 会话状态
   - `.monoco/im/webhooks/`: 平台 Webhook 配置

#### 设计决策验证

- ✅ IMMessage 与 Memo 完全独立，无继承关系
- ✅ 存储结构独立于 `.monoco/memos/`
- ✅ 支持富媒体内容
- ✅ 内置上下文窗口管理 (sliding/summarized/full)

#### 后续依赖

本 Issue 完成后，FEAT-0170 (Agent 集成) 可以继续开发。
