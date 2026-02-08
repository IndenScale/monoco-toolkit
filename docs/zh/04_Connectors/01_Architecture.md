# Connectors 架构设计

**Version**: 2.1.0
**Status**: Implemented
**Related**: FEAT-0191, FEAT-0189, EPIC-0035, FEAT-0172

---

## 1. 架构概述

Connectors 是 Monoco 与外部通信的基础设施，采用**去中心化设计**：

- **Courier**: 用户级别全局服务 - 接收外部连续消息流，聚合成 Mail 写入全局 inbox
- **Mailbox**: 每个 Workspace 独立 - 通过本地规则主动筛选、拉取 Mail

### 核心概念：Mail

**Mail** 是连续消息聚合的原子单位：
- 外部连续到达的消息（如飞书群聊的连续发言）被聚合成一个 Mail
- Mail 是消费的原子单位，不是单条消息
- 一个 Mail 可以被**多个 Workspace 同时消费**（可能涉及多个模块都需要修改）

### 1.1 设计哲学

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           User Device                                        │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    Courier Service (Single Instance)                 │   │
│   │                     职责: 接收外部消息流 → 聚合 → 写入全局 inbox      │   │
│   │                                                                      │   │
│   │   外部消息流 ──▶ 聚合 ──▶ ~/.monoco/mailbox/{source}/inbound/         │   │
│   │                     (按 source 分目录)                               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      │ 文件系统事件                           │
│                                      ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         Workspace 层 (去中心化)                       │   │
│   │                                                                      │   │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │   │
│   │   │  ~/Proj  │    │ ~/Work/  │    │/Vol/ext/ │    │ 其他分散  │     │   │
│   │   │   A/     │    │   B/     │    │   C/     │    │ 目录     │     │   │
│   │   │          │    │          │    │          │    │          │     │   │
│   │   │.monoco/  │    │.monoco/  │    │.monoco/  │    │.monoco/  │     │   │
│   │   │mailbox/  │    │mailbox/  │    │mailbox/  │    │mailbox/  │     │   │
│   │   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │   │
│   │                                                                      │   │
│   │   每个 Workspace:                                                    │   │
│   │   - 本地规则定义关注什么 Mail                                         │   │
│   │   - 主动 CRUD 全局 inbox 获取感兴趣内容                              │   │
│   │   - 不感知其他 Workspace 存在                                        │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**核心原则**:

1. **用户级单实例 Courier**: 一个用户设备上只运行一个 Courier 进程，避免端口冲突
2. **Mail 原子性**: 连续消息聚合成 Mail，Mail 是消费的原子单位
3. **多 Workspace 消费**: 同一个 Mail 可以被多个 Workspace 同时消费（多模块协作）
4. **全局 inbox**: Courier 仅负责接收和聚合写入，不做路由决策
5. **去中心化分发**: 各 Workspace 自主决定关注哪些 Mail
6. **无注册机制**: 用户目录不维护 workspace 列表，各 workspace 独立运行

---

## 2. 目录结构

### 2.1 全局层（用户目录）

```
~/.monoco/
├── mailbox/                        # 全局 Mail 池（Courier 写入）
│   ├── inbound/                    # 新 Mail（外部输入）
│   │   ├── lark/                   # 按 provider 分目录
│   │   ├── email/
│   │   ├── slack/
│   │   └── dingtalk/
│   ├── outbound/                   # 出站 Mail（待推送）
│   │   ├── lark/
│   │   ├── email/
│   │   └── dingtalk/
│   ├── archive/                    # 已归档
│   │   ├── lark/
│   │   ├── email/
│   │   └── dingtalk/
│   └── .state/                     # 状态目录（锁、重试计数等）
│       └── locks.json              # 消息锁状态
├── run/
│   ├── courier.pid                 # 进程标识
│   ├── courier.json                # 运行时状态
│   └── courier.lock                # 单实例锁文件
└── log/
    └── courier.log                 # 服务日志
```

**关键设计**:
- **按 provider/status 二级目录**: 文件直接存放在 provider 目录下，不按日期嵌套
- **状态集中管理**: 所有锁状态统一存储在 `.state/locks.json`
- **死信队列**: 失败消息移动到 `.deadletter/{provider}/`

### 2.2 Workspace 层（分散在各处）

```
{任意目录}/.monoco/mailbox/         # 每个 workspace 独立
├── inbox/                          # 从全局拉取的 Mail 副本
├── cursor.json                     # 消费进度指针（各 workspace 独立）
└── config.yaml                     # 本地筛选规则
```

---

## 3. Mail 流转框架

### 3.1 接收阶段（Courier 负责）

```
External Provider
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Courier Service                                      │
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │   Adapter    │───▶│   Debounce   │───▶│   Validate   │                 │
│   │  (DingTalk)  │    │   Handler    │    │   & Enrich   │                 │
│   └──────────────┘    └──────────────┘    └──────────────┘                 │
│                                                 │                           │
│                                                 ▼                           │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      State Management                                │  │
│   │  ┌─────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │  │
│   │  │ LockManager │  │ MessageStateManager │  │   Outbound Queue    │ │  │
│   │  │ (claim/done)│  │ (archive/deadletter)│  │  (pending/send)     │ │  │
│   │  └─────────────┘  └─────────────────────┘  └─────────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                 │                           │
│                                                 ▼                           │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      Global Inbox (~/.monoco/mailbox/)               │  │
│   │  ├── inbound/{provider}/         # 新消息                            │  │
│   │  ├── outbound/{provider}/        # 待发送                            │  │
│   │  ├── archive/{provider}/         # 已完成                            │  │
│   │  └── .deadletter/{provider}/     # 失败消息                          │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**核心组件**:

| 组件 | 职责 | 关键配置 |
|------|------|----------|
| **Adapter** | 接收外部消息流 | 钉钉 Stream、Webhook |
| **Debounce Handler** | 防抖聚合连续消息 | window_ms=5000, max_wait_ms=30000 |
| **LockManager** | 管理消息认领锁 | CLAIM_TIMEOUT=300s |
| **MessageStateManager** | 归档/死信处理 | ARCHIVE_RETENTION=30天 |
| **Outbound Processor** | 处理出站消息队列 | 定时轮询 outbound/ |

**Courier 职责**:
- 接收外部消息流（webhook、钉钉 Stream 等）
- **防抖聚合**: 5 秒窗口内同一 session 的消息合并
- 验证格式、补充元数据
- 写入 `mailbox/inbound/{provider}/`
- **状态管理**: 维护锁、重试计数、归档
- **出站处理**: 轮询 outbound/ 并发送
- **不做路由，不感知 workspace**

### 3.2 分发阶段（去中心化拉取）

```
各 Workspace 自主执行（通过 Mailbox CLI）:

┌─────────────────────────────────────────────────────────────────┐
│  Workspace A (~/Projects/alpha/)                                │
│                                                                 │
│  1. 读取全局 mailbox/{source}/inbound/                              │
│  2. 按本地规则筛选: @monoco::alpha 或 binding==alpha           │
│  3. 硬链接/复制到本地 .monoco/mailbox/inbox/                    │
│  4. 更新本地 cursor.json                                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Workspace B (~/work/beta/)                                     │
│                                                                 │
│  1. 读取全局 mailbox/{source}/inbound/                              │
│  2. 按本地规则筛选: @monoco::beta 或 from=github.com            │
│  3. 硬链接/复制到本地 .monoco/mailbox/inbox/                    │
│  4. 更新本地 cursor.json                                        │
└─────────────────────────────────────────────────────────────────┘
```

**关键特性**:
- 无中心协调，各 workspace 独立运行
- **同一个 Mail 可以被多个 Workspace 消费**（多模块协作场景）
- 筛选规则本地化，Courier 不知情
- cursor 独立维护，互不影响

### 3.3 消息状态流转

```
                              claim (via API)
    ┌────────────────────────────────────────────────────────────┐
    │                                                            │
    ▼                                                            │
┌────────┐    expire/     ┌──────────┐     fail (retryable)    ┌────────┐
│  NEW   │──timeout──────▶│ CLAIMED  │────────────────────────▶│  NEW   │
└───┬────┘                └────┬─────┘                         └────────┘
    │                          │
    │                          │ complete (via API)
    │                          ▼
    │                    ┌──────────┐
    │                    │COMPLETED │
    │                    └────┬─────┘
    │                         │
    │ archive                 │
    │                         │
    ▼                         ▼
┌──────────┐           ┌──────────┐
│ ARCHIVED │           │DEADLETTER│  ← fail (non-retryable)
└──────────┘           └──────────┘      or max retries exceeded
```

**状态说明**:

| 状态 | 说明 | 转移条件 |
|------|------|----------|
| `NEW` | 新消息，等待认领 | 初始状态，或 claim 超时/失败重试 |
| `CLAIMED` | 已被认领，处理中 | 通过 API 认领，带 5 分钟超时 |
| `COMPLETED` | 处理完成 | 调用 done API |
| `FAILED` | 处理失败 | 调用 fail API，可重试 |
| `ARCHIVED` | 已归档 | 完成或过期后归档 |
| `DEADLETTER` | 死信队列 | 超过最大重试次数 |

**锁机制**:
- 认领时创建锁，默认超时 **300 秒 (5 分钟)**
- 锁过期后消息回到 `NEW` 状态
- 支持最大 **3 次重试**，指数退避 (1s, 2s, 4s...)

**关键设计**:
- **多 Workspace 消费**: 同一个 Mail 可被多个 Workspace claim（各自独立锁）
- **超时释放**: claim 超时的消息自动回到 NEW 状态
- **死信处理**: 多次失败的消息进入死信队列，需人工干预

---

## 4. 交互流程

### 4.1 Mail 接收与聚合流程

```
External Provider (连续消息流)
       │
       ▼
┌──────────────┐
│   Courier    │──► 接收连续消息流
│   Adapter    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Debounce   │──► 防抖聚合（如 5 秒内同一 session 的消息合并）
│   Aggregate  │    输出：Mail（原子消费单位）
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Validate   │──► Schema 校验
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Write to    │──► 写入 ~/.monoco/mailbox/{source}/inbound/
│ Global Inbox │    文件名: {timestamp}-{hash}.jsonl
└──────────────┘
       │
       ▼
  (多个 Workspace 可拉取同一个 Mail)
```

### 4.2 Mail 消费流程

```bash
# 1. Workspace 同步（本地命令）
$ monoco mailbox sync

# 2. 查看本地 Mail
$ monoco mailbox list

# 3. 读取 Mail 内容
$ monoco mailbox read <mail-id>

# 4. 认领 Mail（多个 WS 可同时 claim）
$ monoco mailbox claim <mail-id>

# 5. 处理完成后标记（各 WS 独立）
$ monoco mailbox done <mail-id>
```

---

## 5. 边界与约束

### 5.1 Courier 边界

**负责**:
- 服务生命周期管理（启动/停止）
- 接收外部消息流
- 防抖聚合成 Mail（原子消费单位）
- 验证和写入全局 inbox
- 维护 Mail 状态（通过 API）

**不负责**:
- Mail 路由到 workspace
- 维护 workspace 列表
- 感知 workspace 存在

### 5.2 Mailbox 边界

**负责**:
- 从全局 inbox 拉取 Mail
- 本地 Mail 存储和查询
- 本地筛选规则执行
- 维护本地消费进度

**不负责**:
- 直接接收外部消息流
- 维护全局 Mail 状态（通过 API 请求 Courier）

### 5.3 访问控制

| 操作 | 执行位置 | 说明 |
|------|----------|------|
| 查询全局 inbox | Mailbox CLI | 本地读取 `~/.monoco/mailbox/` |
| 拉取到本地 | Mailbox CLI | 硬链接/复制到 workspace |
| 认领 Mail | Mailbox CLI → Courier API | 多个 WS 可同时 claim |
| 写入 inbox | Courier Service | 唯一写入者 |

---

## 6. 去中心化设计优势

| 场景 | 传统推送模型 | 去中心化拉取模型 |
|------|-------------|-----------------|
| Workspace 发现 | 需要注册表 | 无需注册，自主拉取 |
| Workspace 离线 | Courier 需要队列 | Mail 在全局 inbox 等待 |
| 外置存储 | 复杂的状态同步 | 重新插拔后自动同步 |
| 扩展性 | Courier 成为瓶颈 | 各 workspace 独立 |
| 法律效力 | Mail 位置不确定 | 明确跟随 workspace |

---

## 相关文档

- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - Mail 协议 Schema 规范
- [03_Mailbox_CLI](03_Mailbox_CLI.md) - Mailbox CLI 命令设计（拉取模式）
- [04_Courier_Service](04_Courier_Service.md) - Courier 服务架构设计（用户级单例）
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
