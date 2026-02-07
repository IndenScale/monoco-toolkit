---
id: FEAT-0170
uid: 7d8a2c
type: feature
status: open
stage: doing
title: IM Agent 工作流：实时会话与流式响应
created_at: '2026-02-03T23:23:35'
updated_at: '2026-02-07T23:22:26'
parent: EPIC-0033
dependencies:
- FEAT-0167
- FEAT-0168
- FEAT-0169
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0033'
- '#FEAT-0167'
- '#FEAT-0168'
- '#FEAT-0169'
- '#FEAT-0170'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T23:23:35'
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

- [ ] 实现 `IMAgentSession` 管理 Agent 会话生命周期
- [ ] 实现命令解析器（/role 命令）
- [ ] 实现上下文窗口管理（保留最近 N 条消息）
- [ ] 实现会话超时和清理机制
- [ ] 支持 Agent 主动发送消息（非被动响应）

## Technical Tasks

- [ ] 创建 `monoco/features/im/session.py`
  - [ ] `IMAgentSession` 类
  - [ ] 会话状态管理 (idle / processing / streaming / completed / error)
  - [ ] 上下文窗口管理
  - [ ] 流式输出回调
- [ ] 创建 `monoco/features/im/handlers.py`
  - [ ] `IMMessageHandler` - 消息路由
  - [ ] `IMCommandHandler` - 命令解析
    - `/architect [prompt]` - 启动 Architect Agent
    - `/engineer [issue_id]` - 启动 Engineer Agent
    - `/reviewer [pr_url]` - 启动 Reviewer Agent
    - `/memo [content]` - 归档到 Memo
    - `/issue [title]` - 创建 Issue
    - `/status` - 查看当前会话状态
    - `/stop` - 停止当前 Agent
- [ ] 实现流式响应机制
  - [ ] Agent 输出分片
  - [ ] 消息更新（编辑已发送消息）
  - [ ] 打字指示器
- [ ] 实现 `IMWatcher` 与 AgentScheduler 集成
  - [ ] 订阅 `IM_AGENT_TRIGGER` 事件
  - [ ] 调度 AgentTask 到 LocalProcessScheduler
  - [ ] 处理 Agent 输出流
- [ ] 创建 Agent 输出适配器
  - [ ] 将 Agent stdout 转换为 IM 消息
  - [ ] 代码块格式化
  - [ ] 长文本分片
- [ ] 实现会话持久化
  - [ ] 保存会话历史到 `.monoco/im/sessions/`
  - [ ] 支持会话恢复（可选）

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
