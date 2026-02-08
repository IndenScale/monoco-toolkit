# Mailbox CLI 设计

**Version**: 2.1.0
**Status**: Implemented
**Related**: FEAT-0191, FEAT-0172

---

## 1. 概述

Mailbox CLI 是 Workspace 与 Mail 交互的接口。每个 Workspace 独立维护自己的 Mail 存储和消费进度，通过**拉取模式**从全局 inbox 获取 Mail。

### 1.1 设计原则

1. **去中心化**: 各 Workspace 独立运行，不感知彼此存在
2. **本地优先**: 查询类命令直接操作本地文件，无需服务
3. **自主筛选**: 本地规则决定关注哪些 Mail
4. **独立进度**: 每个 Workspace 维护自己的消费 cursor

---

## 2. 命令概览

```
monoco mailbox
├── list          # 列出本地 Mail（直接读取 ~/.monoco/mailbox/）
├── read          # 读取 Mail 内容
├── send          # 创建出站草稿（写入 outbound/）
├── claim         # 认领 Mail（调用 Courier API，默认 300s 超时）
├── done          # 标记完成（调用 Courier API）
└── fail          # 标记失败（调用 Courier API，支持重试）
```

**设计说明**:
- **本地优先**: `list`, `read` 直接操作文件系统，无需 Courier 运行
- **API 交互**: `claim`, `done`, `fail` 通过 HTTP API 与 Courier 通信
- **全局存储**: Mailbox 直接读取 `~/.monoco/mailbox/`（全局 inbox），无需 sync 命令

---

## 3. 本地查询命令

### 3.1 `mailbox list`

列出 Mail（直接读取 `~/.monoco/mailbox/`）。

```bash
# 基本用法
monoco mailbox list                           # 列出所有 Mail
monoco mailbox list --all                     # 包含已归档

# 过滤选项
monoco mailbox list --status new              # 按状态: new, claimed
monoco mailbox list --provider lark           # 按来源: lark, email, slack, dingtalk
monoco mailbox list --since "2h"              # 最近2小时 (支持: 30m, 1h, 1d)
monoco mailbox list --correlation "bug_123"   # 按关联 ID

# 输出格式
monoco mailbox list --format table            # 表格（默认）
monoco mailbox list --format json             # JSON
monoco mailbox list --format compact          # 紧凑格式
monoco mailbox list --format id               # 仅 ID（用于管道）
```

**状态颜色**:
- 🟢 `new` - 新消息
- 🟡 `claimed` - 已认领
- ⚪ `completed` - 已完成（dim 显示）
- 🔴 `failed` - 失败

**输出示例**:

```
Messages (2)
┌───────────────────────┬──────────┬─────────────┬─────────┬─────────────────────┬──────────────────────────────────────┐
│ ID                    │ Provider │ From        │ Status  │ Time                │ Preview                              │
├───────────────────────┼──────────┼─────────────┼─────────┼─────────────────────┼──────────────────────────────────────┤
│ lark_om_abc123        │ lark     │ IndenScale  │ new     │ 2025-02-08 14:30    │ @monoco::alpha 帮我分析...            │
│ email_a1b2c3d4        │ email    │ John Doe    │ claimed │ 2025-02-08 14:15    │ [Project Alpha] API 设计...           │
└───────────────────────┴──────────┴─────────────┴─────────┴─────────────────────┴──────────────────────────────────────┘
```

### 3.2 `mailbox read`

读取 Mail 内容。

```bash
# 基本用法
monoco mailbox read lark_om_abc123            # 读取详细内容
monoco mailbox read lark_om_abc123 --raw      # 显示原始文件
monoco mailbox read lark_om_abc123 --content  # 仅显示正文

# 管道用法
monoco mailbox list --format id | head -1 | monoco mailbox read -
```

**显示内容**:
- Provider, From, To, Time, Type, Status
- Correlation ID, Reply To, Thread Root
- Content, Mentions, Artifacts

---

## 4. 状态流转命令

这些命令通过 HTTP API (`http://localhost:8644`) 与 Courier 通信。

### 4.1 `mailbox claim`

认领 Mail，表示当前 Agent 将处理该消息。

```bash
# 基本用法
monoco mailbox claim lark_om_abc123           # 认领单条
monoco mailbox claim lark_om_abc123 lark_def  # 批量认领
monoco mailbox claim -                          # 从管道读取

# 选项
monoco mailbox claim lark_om_abc123 --timeout 600  # 自定义超时（默认 300s）
```

**Courier 行为**:
1. 验证 Mail 存在于全局 inbox
2. 在 `.state/locks.json` 中记录认领状态
3. 设置超时时间（默认 300s）
4. 返回确认

**错误码**:
- `1`: 消息不存在
- `2`: 已被其他 Agent 认领
- `3`: Courier 未运行
- `4`: Courier 错误

### 4.2 `mailbox done`

标记 Mail 处理完成。

```bash
monoco mailbox done lark_om_abc123            # 标记完成
monoco mailbox list --status claimed --format id | monoco mailbox done -
```

**Courier 行为**:
1. 验证由当前 Agent 认领
2. 移动到 `archive/{provider}/`
3. 更新 locks.json 状态为 completed

### 4.3 `mailbox fail`

标记 Mail 处理失败。

```bash
monoco mailbox fail lark_om_abc123                      # 标记失败（默认可重试）
monoco mailbox fail lark_om_abc123 --reason "API 超时"   # 附带原因
monoco mailbox fail lark_om_abc123 --no-retryable       # 不可重试，直接进入死信
```

**重试逻辑**:
- 默认可重试，回到 `NEW` 状态
- 最多重试 3 次，指数退避 (1s, 2s, 4s)
- 超过次数或 `--no-retryable` 进入 `.deadletter/`

---

## 5. 发送命令

### 5.1 `mailbox send`

创建出站 Mail 草稿。

```bash
# 快速发送（创建草稿）
monoco mailbox send --provider lark --to "oc_123456" --text "Hello"
monoco mailbox send --provider dingtalk --to "chat_xxx" --text "通知内容"

# 回复消息
monoco mailbox send --provider lark --to "oc_123456" --text "收到" --reply-to "lark_om_abc123"

# 关联业务
monoco mailbox send --provider lark --to "oc_123456" --text "Done" --correlation "bug_123"

# 从文件创建（预留）
monoco mailbox send draft.md
```

**草稿位置**: `.monoco/mailbox/outbound/{provider}/{timestamp}_{provider}_{uid}.md`

**行为**:
1. 在 `outbound/` 创建草稿文件
2. 尝试通知 Courier（如运行中）
3. Courier 轮询 outbound/ 并发送

---

## 6. 完整工作流

### 6.1 日常处理流程

```bash
# 1. 查看新消息（直接读取全局 inbox）
$ monoco mailbox list --status new

# 2. 读取详情
$ monoco mailbox read lark_om_abc123

# 3. 认领消息
$ monoco mailbox claim lark_om_abc123

# 4. ... Agent 处理逻辑 ...

# 5. 标记完成
$ monoco mailbox done lark_om_abc123

# 6. 如需回复
$ monoco mailbox send --provider lark --to "oc_123456" --text "已完成" --reply-to "lark_om_abc123"
```

### 6.2 批量处理

```bash
# 批量认领所有新消息
$ monoco mailbox list --status new --format id | monoco mailbox claim -

# 批量标记完成
$ monoco mailbox list --status claimed --format id | monoco mailbox done -

# 批量标记失败
$ monoco mailbox list --status claimed --format id | monoco mailbox fail --reason "处理超时" -
```

---

## 7. 状态流转图

```
Courier Service                    Mailbox CLI
┌─────────────────┐                ┌──────────────┐
│ ~/.monoco/      │                │ monoco       │
│ └── mailbox/    │                │ mailbox      │
│     ├── inbound │◀── list/read──▶│              │
│     │   /lark/  │                │              │
│     ├── .state/ │◀── claim ─────▶│ claim        │
│     │   locks.  │◀── done ──────▶│ done         │
│     │   json    │◀── fail ──────▶│ fail         │
│     └── outbound│◀── send ──────▶│ send         │
│         /lark/  │                │              │
└─────────────────┘                └──────────────┘
         │                                │
         │ HTTP API (:8644)               │
         └────────────────────────────────┘

Message Lifecycle (inbound/)
────────────────────────────
NEW ──claim──▶ CLAIMED ──done──▶ [archived]
  │               │
  │               │ fail (retryable)
  │               ▼
  │◄───────── NEW (retry)
  │
  │               │ fail (max retries)
  │               ▼
  └────────► .deadletter/
```

---

## 8. 错误处理

| 错误场景 | 命令 | 返回码 | 说明 |
|----------|------|--------|------|
| 消息不存在 | `read` | 1 | Message not found |
| 初始化失败 | 任意 | 1 | Failed to initialize mailbox |
| 消息不存在 | `claim`/`done`/`fail` | 1 | Message not found |
| 已被认领 | `claim` | 2 | Already claimed by another agent |
| Courier 未运行 | `claim`/`done`/`fail` | 3 | Courier service not running |
| Courier 错误 | `claim`/`done`/`fail` | 4 | API error |
| 参数无效 | `list` | 1 | Invalid status/provider/format |
| 缺少参数 | `send` | 1 | Must provide --provider, --to, --text |

---

## 9. API 端点

Mailbox CLI 通过以下 Courier API 端点操作状态：

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/v1/messages/{id}/claim` | POST | 认领消息 |
| `/api/v1/messages/{id}/complete` | POST | 标记完成 |
| `/api/v1/messages/{id}/fail` | POST | 标记失败 |
| `/health` | GET | 健康检查 |

默认地址: `http://localhost:8644`

---

## 相关文档

- [01_Architecture](01_Architecture.md) - 整体架构设计
- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - Mail 协议 Schema 规范
- [04_Courier_Service](04_Courier_Service.md) - Courier 服务架构设计
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
