# Connectors 架构设计

**Version**: 1.1.0
**Status**: Draft
**Related**: FEAT-0191, FEAT-0189, EPIC-0035

---

## 1. 架构概述

Connectors 是 Monoco 与外部通信的基础设施，由两个独立的 Feature 组成：

- **Mailbox**: 协议与数据管理层 - 负责消息存储、查询、归档
- **Courier**: 传输与服务管理层 - 负责消息收发、服务生命周期管理

### 1.1 设计哲学

```
┌─────────────────────────────────────────────────────────────┐
│                        Monoco Agent                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐           ┌──────────────┐               │
│   │   Mailbox    │           │   Courier    │               │
│   │   (Data)     │◄─────────►│  (Service)   │               │
│   └──────┬───────┘           └──────┬───────┘               │
│          │                          │                        │
│          ▼                          ▼                        │
│   ┌──────────────┐           ┌──────────────┐               │
│   │  .monoco/    │           │   Process    │               │
│   │  mailbox/    │           │  Management  │               │
│   └──────────────┘           └──────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     External Providers                       │
│         (Lark / Email / Slack / Discord / ...)              │
└─────────────────────────────────────────────────────────────┘
```

**核心原则**:

1. **关注点分离**: Mailbox 管数据，Courier 管传输
2. **独立演进**: 两者通过协议松耦合，可独立升级
3. **物理隔离**: Mailbox 是只读的受保护空间，Courier 是唯一写入者
4. **CLI 分离**: 两个独立的命令组 `monoco mailbox` 和 `monoco courier`

---

## 2. 目录结构

### 2.1 代码结构

```
src/monoco/features/
├── mailbox/                      # Mailbox Feature (数据层 + CLI)
│   ├── __init__.py
│   ├── commands.py              # CLI: list, read, send, claim, done, fail
│   ├── models.py                # 数据模型定义
│   ├── store.py                 # 文件系统操作
│   ├── queries.py               # 查询引擎
│   ├── client.py                # Courier HTTP API 客户端
│   └── constants.py             # 路径、枚举等常量
│
└── courier/                      # Courier Feature (服务层)
    ├── __init__.py
    ├── commands.py              # CLI: start, stop, restart, kill, status, logs
    ├── service.py               # 服务生命周期管理
    ├── daemon.py                # 后台进程实现
    ├── api.py                   # HTTP API 服务 (claim/done/fail)
    ├── state.py                 # 消息状态管理 (锁、归档、重试)
    ├── adapters/                # 各平台适配器
    │   ├── __init__.py
    │   ├── base.py
    │   ├── lark.py
    │   └── email.py
    ├── protocol/                # 协议层 (共享 Schema)
    │   ├── __init__.py
    │   ├── schema.py            # 统一 Schema 定义
    │   ├── constants.py
    │   └── validators.py
    └── debounce.py              # 防抖合并逻辑
```

### 2.2 物理存储结构

```
.monoco/mailbox/                      # 受保护空间 (Agent 只读)
├── inbound/                          # 外部消息输入
│   ├── lark/
│   ├── email/
│   └── slack/
├── outbound/                         # 内部消息输出（草稿）
│   ├── lark/
│   ├── email/
│   └── slack/
├── archive/                          # 已处理消息存档（30天）
│   ├── lark/
│   ├── email/
│   └── slack/
├── .state/                           # 状态存储（由 Courier 管理）
│   ├── locks.json                    # 消息锁状态
│   └── index.jsonl                   # 消息索引
├── .deadletter/                      # 死信队列（超过重试次数）
│   ├── lark/
│   └── email/
└── .tmp/                             # 临时工作目录
```

---

## 3. 交互流程

### 3.1 消息接收流程 (Inbound)

```
External Provider
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Courier    │────►│   Debounce   │────►│   Mailbox    │
│   Adapter    │     │   Handler    │     │   Store      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  ▼
                                           .monoco/mailbox/
                                           inbound/{provider}/
```

### 3.2 消息发送流程 (Outbound)

```
Agent Workflow
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Agent      │────►│   Courier    │────►│   Mailbox    │
│   CLI Send   │     │   Validate   │     │   Draft      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
       ┌──────────────────────────────────────────┘
       ▼
.monoco/mailbox/outbound/{provider}/
       │
       ▼
┌──────────────┐     ┌──────────────┐
│   Courier    │────►│   External   │
│   Process    │     │   Provider   │
└──────────────┘     └──────────────┘
```

### 3.3 消息消费流程 (Agent 处理)

```
Agent 通过 Mailbox CLI 处理消息

# 1. 查询
$ monoco mailbox list --provider lark --status new
$ monoco mailbox read <msg-id>

# 2. 认领（调用 Courier API）
$ monoco mailbox claim <msg-id>

# 3. 处理完成后（调用 Courier API，触发归档）
$ monoco mailbox done <msg-id>

# 或标记失败（调用 Courier API，触发重试）
$ monoco mailbox fail <msg-id> --reason "API timeout"
```

### 3.4 状态流转与 API 交互

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Mailbox CLI                                  │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   list   │  │   read   │  │   send   │  │   claim  │──┐          │
│  │  (本地)   │  │  (本地)   │  │ (写文件) │  │ (API调用)│  │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │          │
│                                             ┌──────────┤          │
│                                             │   done   │──┤          │
│                                             │ (API调用)│  │          │
│                                             ├──────────┤  │          │
│                                             │   fail   │──┘          │
│                                             │ (API调用)│             │
│                                             └──────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP API
┌─────────────────────────────────────────────────────────────────────┐
│                      Courier Service                                 │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Lock Mgr   │  │   Archive    │  │    Retry     │               │
│  │  (claim/done)│  │  (done触发)   │  │  (fail触发)   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 边界与约束

### 4.1 Mailbox 边界

**负责**:
- 消息文件的 CRUD 操作
- 查询与过滤
- 归档与清理
- 索引与缓存

**不负责**:
- 网络通信
- 服务生命周期
- 外部 API 调用

### 4.2 Courier 边界

**负责**:
- 服务启动/停止/重启
- 消息收发传输
- 适配器管理
- 防抖合并

**不负责**:
- 消息内容解析 (由 Agent 完成)
- 长期存储管理 (由 Mailbox 完成)
- 消息查询 (由 Mailbox 完成)

### 4.3 访问控制

| 操作 | 命令 | Mailbox CLI | Courier Service | Agent |
|------|------|-------------|-----------------|-------|
| 查询消息 | `mailbox list` | ✓ | ✗ | ✓ |
| 读取内容 | `mailbox read` | ✓ | ✗ | ✓ |
| 创建草稿 | `mailbox send` | ✓ | ✗ | ✓ |
| 认领消息 | `mailbox claim` | ✓ API | ✓ 维护锁 | ✓ |
| 标记完成 | `mailbox done` | ✓ API | ✓ 归档 | ✓ |
| 标记失败 | `mailbox fail` | ✓ API | ✓ 重试 | ✓ |
| 写入 inbox | - | ✗ | ✓ (Webhook) | ✗ |
| 服务管理 | `courier start/stop` | ✗ | ✓ | ✓ |

---

## 5. 版本策略

### 5.1 协议版本

```yaml
# 在消息 metadata 中声明
metadata:
  schema_version: "1.0.0"
  protocol_version: "1.0.0"
```

### 5.2 向后兼容

- **新增字段**: 可选字段，旧版本忽略
- **废弃字段**: 保留字段但标记 deprecated
- **破坏性变更**: 主版本号升级，提供迁移脚本

---

## 相关文档

- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - 消息协议 Schema 规范
- [03_Mailbox_CLI](03_Mailbox_CLI.md) - Mailbox CLI 命令设计
- [04_Courier_Service](04_Courier_Service.md) - Courier 服务架构设计
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
