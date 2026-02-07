---
id: FEAT-0172
uid: 2c8ce7
type: feature
status: closed
stage: done
title: Courier Outbound 消息处理器与自动归档
created_at: '2026-02-07T23:17:20'
updated_at: '2026-02-08T00:58:33'
parent: EPIC-0035
dependencies: []
related: []
domains:
- CollaborationBus
tags:
- '#courier'
- '#outbound'
- '#daemon'
- '#EPIC-0035'
- '#FEAT-0172'
files:
- Issues/Features/closed/FEAT-0172-优化-issue-close-时的文件合并策略-直接覆盖主线-issue-ticket.md
- Issues/Features/open/FEAT-0195-实现-dingtalk-stream-模式下的消息发送功能.md
- Issues/Fixes/open/FIX-0023-修复-monoco-courier-无法接收-dingtalk-消息的问题.md
- src/monoco/features/channel/models.py
- src/monoco/features/courier/adapters/__init__.py
- src/monoco/features/courier/adapters/dingtalk_outbound.py
- src/monoco/features/courier/adapters/dingtalk_stream.py
- src/monoco/features/courier/adapters/stub.py
- src/monoco/features/courier/daemon.py
- src/monoco/features/courier/outbound_dispatcher.py
- src/monoco/features/courier/outbound_processor.py
- src/monoco/features/courier/outbound_watcher.py
- tests/features/courier/test_outbound_dispatcher.py
- tests/features/courier/test_outbound_processor.py
- tests/features/courier/test_outbound_watcher.py
criticality: high
solution: implemented
opened_at: '2026-02-07T23:17:20'
closed_at: '2026-02-08T00:58:33'
isolation:
  type: branch
  ref: FEAT-0172-courier-outbound-消息处理器与自动归档
  created_at: '2026-02-07T23:39:54'
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
- [x] 实现 Outbound 目录轮询检测机制
- [x] 实现多适配器路由 (dingtalk, lark, email, slack, teams, wecom)
- [x] 实现消息发送成功后的自动归档
- [x] 支持发送失败的重试机制 (指数退避)
- [x] 支持死信队列 (多次失败后移入 .deadletter)
- [x] 发送状态更新到消息文件的 frontmatter

## Technical Tasks

### 1. Outbound 消息检测
- [x] 创建 `OutboundWatcher` 类
  - [x] 定期扫描 `mailbox/outbound/{provider}/*.md` 文件
  - [x] 解析消息 frontmatter 获取发送配置
  - [x] 过滤已处理/锁定中的消息
  - [x] 检测文件变化 (支持文件系统事件或轮询)

### 2. 消息发送调度器
- [x] 创建 `OutboundDispatcher` 类
  - [x] 根据 `provider` 字段路由到对应适配器
  - [x] 支持适配器: dingtalk, lark, email, slack, teams, wecom
  - [x] 调用适配器的 `send()` 方法发送消息
  - [x] 处理发送结果 (成功/失败)

### 3. 适配器接口完善
- [x] 确保各适配器实现 `send()` 方法
  - [x] DingTalk 适配器 (`adapters/dingtalk_outbound.py`)
  - [x] Lark 适配器 (stub)
  - [x] 其他适配器基类实现 (stub)

### 4. 发送后处理
- [x] 成功时:
  - [x] 更新消息状态为 `sent`
  - [x] 记录 `sent_at` 时间戳
  - [x] 移动到 `mailbox/archive/{provider}/`
- [x] 失败时:
  - [x] 更新 `retry_count`
  - [x] 计算下次重试时间 (`next_retry_at`)
  - [x] 超过最大重试次数后移入 `.deadletter/{provider}/`

### 5. Daemon 集成
- [x] 在 `daemon.py` 的 main loop 中集成 Outbound 处理
  - [x] 替换现有的 `# TODO: Process outbound queue` 注释
  - [x] 配置轮询间隔 (默认 5 秒)
  - [x] 确保与现有 API server 共存

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

### 2026-02-08 - 代码审查完成

**实现状态**: ✅ 已完成并测试通过

**主要完成内容**:
1. ✅ OutboundWatcher - 定期扫描待发送消息
2. ✅ OutboundDispatcher - 路由消息到适配器
3. ✅ OutboundProcessor - 发送后归档/重试/死信处理
4. ✅ DingTalkStreamAdapter - Flow 模式发送 + Webhook 回退
5. ✅ Channel 统一配置 - 支持 Flow + Webhook 双模式

**测试结果**:
- Lark 消息发送成功并归档 ✅
- DingTalk OpenAPI 群聊发送失败（robot 不存在）⚠️
- DingTalk Webhook 回退发送成功 ✅
- 自动归档到 `archive/` 目录 ✅

**已知限制**:
- 钉钉 OpenAPI 群聊发送需要额外的权限配置（已开通但仍报错）
- Webhook 回退机制已作为可靠备选方案

**建议**: 已满足生产使用要求，可合并至主线。
