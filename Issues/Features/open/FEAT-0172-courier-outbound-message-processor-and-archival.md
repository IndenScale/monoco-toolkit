---
id: FEAT-0172
uid: 2c8ce7
type: feature
status: open
stage: doing
title: Courier Outbound 消息处理器与自动归档
created_at: '2026-02-07T23:17:20'
updated_at: '2026-02-07T23:39:54'
parent: EPIC-0035
dependencies: []
related: []
domains:
- CollaborationBus
tags:
- '#courier'
- '#outbound'
- '#daemon'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T23:17:20'
---

## FEAT-0172: Courier Outbound 消息处理器与自动归档

## Objective
完善 Courier 守护进程的 Outbound 消息处理功能，实现自动发现待发送消息、调用对应适配器发送、成功后归档的完整流程。

### 功能范围
- **轮询检测**: 定期扫描 `.monoco/mailbox/outbound/` 目录下的待发送消息
- **消息发送**: 根据消息 provider (dingtalk/lark/email 等) 调用对应适配器
- **成功归档**: 发送成功后自动将消息移动到 archive 目录
- **失败重试**: 支持失败消息的重试机制和死信队列

## Acceptance Criteria
- [ ] 实现 Outbound 目录轮询检测机制
- [ ] 实现多适配器路由 (dingtalk, lark, email, slack, teams, wecom)
- [ ] 实现消息发送成功后的自动归档
- [ ] 支持发送失败的重试机制 (指数退避)
- [ ] 支持死信队列 (多次失败后移入 .deadletter)
- [ ] 发送状态更新到消息文件的 frontmatter

## Technical Tasks

### 1. Outbound 消息检测
- [ ] 创建 `OutboundWatcher` 类
  - [ ] 定期扫描 `mailbox/outbound/{provider}/*.md` 文件
  - [ ] 解析消息 frontmatter 获取发送配置
  - [ ] 过滤已处理/锁定中的消息
  - [ ] 检测文件变化 (支持文件系统事件或轮询)

### 2. 消息发送调度器
- [ ] 创建 `OutboundDispatcher` 类
  - [ ] 根据 `provider` 字段路由到对应适配器
  - [ ] 支持适配器: dingtalk, lark, email, slack, teams, wecom
  - [ ] 调用适配器的 `send()` 方法发送消息
  - [ ] 处理发送结果 (成功/失败)

### 3. 适配器接口完善
- [ ] 确保各适配器实现 `send()` 方法
  - [ ] DingTalk 适配器 (`adapters/dingtalk.py`)
  - [ ] Lark 适配器 (`adapters/lark.py`)
  - [ ] 其他适配器基类实现

### 4. 发送后处理
- [ ] 成功时:
  - [ ] 更新消息状态为 `sent`
  - [ ] 记录 `sent_at` 时间戳
  - [ ] 移动到 `mailbox/archive/{provider}/`
- [ ] 失败时:
  - [ ] 更新 `retry_count`
  - [ ] 计算下次重试时间 (`next_retry_at`)
  - [ ] 超过最大重试次数后移入 `.deadletter/{provider}/`

### 5. Daemon 集成
- [ ] 在 `daemon.py` 的 main loop 中集成 Outbound 处理
  - [ ] 替换现有的 `# TODO: Process outbound queue` 注释
  - [ ] 配置轮询间隔 (默认 5 秒)
  - [ ] 确保与现有 API server 共存

## 消息文件格式

```yaml
---
id: out_dingtalk_xxx
to: user_id or chat_id
provider: dingtalk
reply_to: in_dingtalk_xxx  # 可选：回复的消息
thread_key: thread_xxx     # 可选：会话线程
content_type: text|markdown|card
status: pending|sending|sent|failed
created_at: '2026-02-07T15:02:32'
sent_at: null              # 发送成功后填充
retry_count: 0
next_retry_at: null
error_message: null        # 失败时填充
---
消息内容...
```

## 目录结构

```
.monoco/mailbox/
├── outbound/               # 待发送消息
│   ├── dingtalk/
│   │   └── 20260207T150232_out_dingtalk_64bf0586.md
│   ├── lark/
│   ├── email/
│   └── ...
├── archive/                # 已发送归档
│   ├── dingtalk/
│   ├── lark/
│   └── ...
└── .deadletter/            # 发送失败多次
    ├── dingtalk/
    └── ...
```

## API 扩展 (可选)

- `POST /api/v1/courier/outbound/send` - 手动触发发送
- `GET /api/v1/courier/outbound/queue` - 查看发送队列
- `POST /api/v1/courier/outbound/retry/{message_id}` - 重试失败消息

## 相关代码

- `src/monoco/features/courier/daemon.py` - 守护进程主循环
- `src/monoco/features/courier/state.py` - 消息状态管理
- `src/monoco/features/courier/adapters/base.py` - 适配器基类
- `src/monoco/features/courier/adapters/dingtalk.py` - 钉钉适配器

## Review Comments
