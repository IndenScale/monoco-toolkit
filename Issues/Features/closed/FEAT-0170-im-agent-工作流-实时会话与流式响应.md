---
id: FEAT-0170
uid: 7d8a2c
type: feature
status: closed
stage: done
title: IM Agent 工作流：实时会话与流式响应
created_at: '2026-02-03T23:23:35'
updated_at: '2026-02-07T23:36:46'
parent: EPIC-0033
dependencies:
- FEAT-0167
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0033'
- '#FEAT-0167'
- '#FEAT-0170'
files:
- Issues/Epics/open/EPIC-0033-im-系统集成-实时通信与-agent-编排.md
- Issues/Features/open/FEAT-0172-courier-outbound-message-processor-and-archival.md
- src/monoco/features/courier/daemon.py
- src/monoco/features/courier/im_integration.py
- src/monoco/features/im/__init__.py
- src/monoco/features/im/handlers.py
- src/monoco/features/im/session.py
- tests/features/im/test_session.py
criticality: high
solution: implemented
opened_at: '2026-02-03T23:23:35'
closed_at: '2026-02-07T23:36:46'
isolation:
  type: branch
  ref: FEAT-0170-im-agent-工作流-实时会话与流式响应
  created_at: '2026-02-07T23:22:28'
---

## FEAT-0170: IM Agent 工作流：实时会话与流式响应

## Objective

实现 IM 与 Agent 的实时双向通信，支持流式响应、多轮对话和上下文管理。

### 核心特性

- **流式响应**: Agent 输出实时推送到 IM，而非等待完成
- **上下文管理**: 维护会话历史，支持多轮对话
- **并行会话**: 同一频道支持多个并行的 Agent 会话
- **命令触发**: 支持 `/architect`、`/engineer` 等命令

## Acceptance Criteria

- [x] 实现 `IMAgentSession` 管理 Agent 会话生命周期
- [x] 实现命令解析器（/role 命令）
- [x] 实现上下文窗口管理（保留最近 N 条消息）
- [x] 实现会话超时和清理机制
- [x] 支持 Agent 主动发送消息（非被动响应）

## Technical Tasks

- [x] 创建 `monoco/features/im/session.py`
  - [x] `IMAgentSession` 类
  - [x] 会话状态管理 (idle / processing / streaming / completed / error)
  - [x] 上下文窗口管理
  - [x] 流式输出回调
- [x] 创建 `monoco/features/im/handlers.py`
  - [x] `IMMessageHandler` - 消息路由
  - [x] `IMCommandHandler` - 命令解析
    - `/architect [prompt]` - 启动 Architect Agent
    - `/engineer [issue_id]` - 启动 Engineer Agent
    - `/reviewer [pr_url]` - 启动 Reviewer Agent
    - `/memo [content]` - 归档到 Memo
    - `/issue [title]` - 创建 Issue
    - `/status` - 查看当前会话状态
    - `/stop` - 停止当前 Agent
- [x] 实现流式响应机制
  - [x] Agent 输出分片
  - [x] 消息更新（编辑已发送消息）
- [x] 实现 `IMWatcher` 与 AgentScheduler 集成
  - [x] 订阅 `IM_AGENT_TRIGGER` 事件
  - [x] 调度 AgentTask 到 LocalProcessScheduler
  - [x] 处理 Agent 输出流
- [x] 创建 Agent 输出适配器
  - [x] 将 Agent stdout 转换为 IM 消息
  - [x] 代码块格式化
  - [x] 长文本分片
- [x] 实现会话持久化
  - [x] 保存会话历史到 `.monoco/im/sessions/"

## Agent 触发策略

```python
class IMAgentTrigger:
    """决定何时触发 Agent"""

    def should_trigger(self, message: IMMessage) -> bool:
        # 1. 命令模式
        if message.content.text.startswith('/'):
            return True

        # 2. @提及机器人
        if bot_mentioned(message):
            return True

        # 3. 关键字触发（可配置）
        if matches_trigger_keywords(message):
            return True

        return False
```

## 流式响应流程

```
用户发送消息
    ↓
IMWatcher 捕获
    ↓
触发 IM_AGENT_TRIGGER 事件
    ↓
IMAgentSession 创建
    ↓
LocalProcessScheduler 调度 Agent
    ↓
Agent 输出 → 分片 → 更新 IM 消息
    ↓
完成 / 超时 / 错误
```

## Review Comments

### Implementation Notes

1. **Session State Machine**: Implemented full state transitions (IDLE -> PROCESSING -> STREAMING -> COMPLETED/ERROR)
2. **Command Parser**: Supports all planned commands: /architect, /engineer, /reviewer, /planner, /memo, /issue, /status, /stop, /help
3. **Context Window**: Sliding window implementation with configurable size (default 10 messages)
4. **AgentScheduler Integration**: CourierIMAdapter subscribes to Agent events and updates IM sessions accordingly
5. **Testing**: 22 comprehensive tests covering command parsing, session lifecycle, and manager operations

### Architecture Decisions

- Used asyncio for async session management
- Separated concerns: SessionController (business logic), SessionManager (lifecycle), Handlers (routing)
- Stream output uses callback pattern for platform-agnostic integration
- Session persistence uses JSON files for simplicity
