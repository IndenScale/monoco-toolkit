# Connectors 文档

Monoco Connectors 文档集，定义 Mailbox 和 Courier 两个独立 Feature 的架构、协议和 CLI 设计。

## 文档结构

```
04_Connectors/
├── README.md                   # 本文档
├── 01_Architecture.md          # 整体架构设计
├── 02_Mailbox_Protocol.md      # Mail 协议 Schema 规范
├── 03_Mailbox_CLI.md           # Mailbox CLI 命令设计
├── 04_Courier_Service.md       # Courier 服务架构设计
└── 05_Courier_CLI.md           # Courier CLI 命令设计
```

## 快速导航

### 如果你是架构师
1. 先读 [01_Architecture](01_Architecture.md) 了解整体设计
2. 然后读 [02_Mailbox_Protocol](02_Mailbox_Protocol.md) 了解 Mail 格式

### 如果你是开发者
1. 根据职责选择：
   - 负责数据层 → [02_Mailbox_Protocol](02_Mailbox_Protocol.md) + [03_Mailbox_CLI](03_Mailbox_CLI.md)
   - 负责传输层 → [04_Courier_Service](04_Courier_Service.md) + [05_Courier_CLI](05_Courier_CLI.md)

### 如果你是用户
1. 查询 Mail → [03_Mailbox_CLI](03_Mailbox_CLI.md)
2. 管理服务 → [05_Courier_CLI](05_Courier_CLI.md)

## 核心概念

### Mailbox vs Courier

| 特性 | Mailbox | Courier |
|------|---------|---------|
| **职责** | 本地 Mail 管理（拉取、查询、消费） | 全局 Mail 聚合（接收、合并、存储） |
| **形态** | 每个 Workspace 独立 | 用户级别单实例 |
| **CLI** | `monoco mailbox` | `monoco courier` |
| **写入权限** | 本地只写，全局通过 API | 全局 inbox 唯一写入者 |
| **典型操作** | sync, list, read, claim, done | start, stop, status |

### 关键设计决策

1. **分离而非合并**: Mailbox 和 Courier 是两个独立的 Feature，不是统一的 Connector
2. **受保护空间**: `.monoco/mailbox/` 对 Agent 只读，防止意外修改
3. **kill 不优雅**: `courier kill` 强制停止，不考虑内存进度，用于紧急恢复

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-02-07 | 初始版本，从 mailbox-protocol-schema.md 重构拆分 |

## 相关 Issue

- FEAT-0191: Refactor Connector System
- FEAT-0189: Mailbox Protocol Implementation
- EPIC-0035: Monoco Communication Layer
