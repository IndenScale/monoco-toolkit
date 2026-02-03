---
id: FEAT-0167
uid: 68dadf
type: feature
status: open
stage: draft
title: IM 基础设施：核心数据模型与存储
created_at: '2026-02-03T23:23:32'
updated_at: '2026-02-03T23:23:32'
parent: EPIC-0033
dependencies: []
related:
- FEAT-0168
- FEAT-0169
- FEAT-0170
- FEAT-0171
domains:
- Foundation
tags:
- '#EPIC-0033'
- '#FEAT-0167'
- '#FEAT-0168'
- '#FEAT-0169'
- '#FEAT-0170'
- '#FEAT-0171'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T23:23:32'
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
- [ ] 定义 IMChannel、IMMessage、IMParticipant 核心模型
- [ ] 实现 IM 独立存储目录结构 (.monoco/im/)
- [ ] 实现消息持久化存储 (JSONL 格式)
- [ ] 实现频道注册与会话管理
- [ ] 定义 AgentEventType.IM_* 事件类型
- [ ] 实现 IMWatcher 监控消息流入

## Technical Tasks
- [ ] 创建 `monoco/features/im/models.py`
  - [ ] `PlatformType` 枚举 (feishu, dingtalk, slack)
  - [ ] `IMChannel` 模型 - 频道/群聊信息
  - [ ] `IMMessage` 模型 - 消息内容
  - [ ] `IMParticipant` 模型 - 参与者信息
  - [ ] `MessageContent` 模型 - 支持富媒体
  - [ ] `IMAgentSession` 模型 - Agent 会话绑定
- [ ] 创建 `monoco/features/im/core.py`
  - [ ] `IMChannelManager` - 频道管理
  - [ ] `MessageStore` - 消息存储
  - [ ] `IMRouter` - 消息路由决策
- [ ] 创建 `monoco/core/watcher/im.py`
  - [ ] `IMWatcher` - 消息事件监控
  - [ ] 发布 `IM_MESSAGE_RECEIVED` 事件
- [ ] 扩展 `monoco/core/scheduler/events.py`
  - [ ] `IM_MESSAGE_RECEIVED`
  - [ ] `IM_MESSAGE_REPLIED`
  - [ ] `IM_AGENT_TRIGGER`
  - [ ] `IM_SESSION_STARTED`
  - [ ] `IM_SESSION_CLOSED`
- [ ] 创建 `.monoco/im/` 目录结构
  - [ ] `channels.jsonl` - 频道注册表
  - [ ] `messages/` - 消息历史
  - [ ] `sessions/` - Agent 会话
  - [ ] `webhooks/` - 平台配置

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
