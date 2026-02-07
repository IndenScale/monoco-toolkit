# Mailbox CLI 设计

**Version**: 1.1.0
**Status**: Draft
**Related**: FEAT-0191

---

## 1. 概述

Mailbox CLI 是 Agent 与消息数据交互的接口。它提供消息查询、状态流转控制和发送功能。状态管理命令（`claim`, `done`, `fail`）通过与 Courier 服务通信实现。

### 1.1 设计原则

1. **统一入口**: Agent 通过 Mailbox CLI 完成所有消息操作
2. **本地优先**: 查询类命令直接操作文件系统，无需服务
3. **状态集中**: 消息状态由 Courier 统一管理，通过 API 交互
4. **管道友好**: 输出支持 JSON/表格/简洁模式，便于脚本处理

---

## 2. 命令概览

```
monoco mailbox
├── list          # 列出消息（本地查询）
├── read          # 读取消息内容（本地读取）
├── send          # 发送消息（创建草稿，通知 Courier）
├── claim         # 认领消息（调用 Courier API）
├── done          # 标记完成（调用 Courier API，触发归档）
└── fail          # 标记失败（调用 Courier API，触发重试）
```

---

## 3. 本地命令（直接操作文件系统）

### 3.1 `mailbox list`

列出 inbox 中的消息。

```bash
# 基本用法
monoco mailbox list                           # 列出所有未处理消息
monoco mailbox list --all                     # 列出所有消息
monoco mailbox list --provider lark           # 仅列出飞书消息

# 过滤选项
monoco mailbox list --status new              # 新消息（默认）
monoco mailbox list --status claimed          # 已认领消息
monoco mailbox list --provider email          # 仅列出邮件
monoco mailbox list --since "2h"              # 最近2小时
monoco mailbox list --correlation "bug_123"   # 关联特定业务

# 输出格式
monoco mailbox list --format table            # 表格格式（默认）
monoco mailbox list --format json             # JSON 格式
monoco mailbox list --format compact          # 紧凑格式: "id | from | preview"
monoco mailbox list --format id               # 仅输出 ID，便于管道
```

**输出示例（table 格式）**:

```
ID                        Provider    From                Status      Time        Preview
─────────────────────────────────────────────────────────────────────────────────────────────
lark_om_abc123            lark        IndenScale          new         2 min ago   "@Prime 帮我分析..."
email_a1b2c3d4            email       John Doe            claimed     15 min ago  "请查看附件中的 API..."
lark_om_def456            lark        Prime               new         1 hour ago  "收到，请提供错误日志..."
```

---

### 3.2 `mailbox read`

读取消息内容。

```bash
# 基本用法
monoco mailbox read lark_om_abc123            # 读取消息内容
monoco mailbox read lark_om_abc123 --raw      # 显示原始文件内容
monoco mailbox read lark_om_abc123 --content  # 仅显示正文（不含 frontmatter）

# 管道用法
monoco mailbox list --format id | head -1 | monoco mailbox read -
```

**输出示例**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Message: lark_om_abc123                                          │
├─────────────────────────────────────────────────────────────────┤
│ Provider:    lark                                                │
│ From:        IndenScale (ou_user123)                             │
│ To:          Monoco Dev Group (oc_123456)                        │
│ Time:        2026-02-06 20:45:00 UTC (2 minutes ago)             │
│ Type:        text                                                │
│ Status:      new                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Content:                                                         │
│ @Prime 帮我分析一下这个 Bug                                      │
├─────────────────────────────────────────────────────────────────┤
│ Mentions:                                                        │
│   - @Prime (ou_prime456)                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.3 `mailbox send`

创建出站消息草稿。

```bash
# 从文件创建草稿
monoco mailbox send draft.md                  # 创建草稿，通知 Courier 发送

# 快速发送
monoco mailbox send --provider lark --to "oc_123456" --text "Hello"

# 选项
monoco mailbox send draft.md --correlation "bug_123"  # 关联业务ID
```

**行为**:
1. 创建草稿文件到 `.monoco/mailbox/outbound/{provider}/`
2. 通知 Courier 服务有新消息待发送（如果服务运行）
3. 返回草稿 ID

**草稿文件格式**:

```markdown
---
id: "out_lark_abc123"
to: "oc_123456"
provider: lark
reply_to: "lark_om_abc123"
thread_key: "om_abc123"
type: text
status: pending
created_at: "2026-02-06T20:45:00Z"
content:
  text: "消息正文"
---
```

---

## 4. 状态流转命令（与 Courier 通信）

这些命令通过 HTTP API 与 Courier 服务交互，由 Courier 维护状态并执行后续操作。

### 4.1 `mailbox claim`

认领消息，表示当前 Agent 将处理该消息。

```bash
# 基本用法
monoco mailbox claim lark_om_abc123           # 认领单条消息
monoco mailbox claim lark_om_abc123 lark_om_def456  # 批量认领

# 管道用法
monoco mailbox list --status new --format id | monoco mailbox claim -
```

**Courier 行为**:
1. 检查消息是否已被认领
2. 记录认领者（Agent ID）和认领时间
3. 更新消息状态为 `claimed`
4. 返回认领结果

**错误处理**:
- 消息不存在 → 返回码 1
- 消息已被认领 → 返回码 2，显示当前认领者
- Courier 未运行 → 返回码 3，提示启动服务

---

### 4.2 `mailbox done`

标记消息处理完成，Courier 将执行归档。

```bash
# 基本用法
monoco mailbox done lark_om_abc123            # 标记完成

# 管道用法
monoco mailbox list --status claimed --format id | monoco mailbox done -
```

**Courier 行为**:
1. 验证消息是否由当前 Agent 认领
2. 更新状态为 `completed`
3. 移动到 `.monoco/mailbox/archive/`
4. 清理锁状态

**错误处理**:
- 消息未被当前 Agent 认领 → 返回码 2，提示先 claim

---

### 4.3 `mailbox fail`

标记消息处理失败，Courier 将执行重试策略。

```bash
# 基本用法
monoco mailbox fail lark_om_abc123                      # 标记失败
monoco mailbox fail lark_om_abc123 --reason "API 超时"   # 附带原因

# 管道用法
monoco mailbox list --status claimed --format id | monoco mailbox fail -
```

**Courier 行为**:
1. 验证消息是否由当前 Agent 认领
2. 更新状态为 `failed`，记录失败原因
3. 根据重试策略决定是否：
   - 重新放入队列（可重试）
   - 移入死信队列（超过重试次数）
4. 释放锁

**重试策略**:
- 最多重试 3 次
- 指数退避：1s, 2s, 4s
- 超过次数进入 `.monoco/mailbox/.deadletter/`

---

## 5. 状态流转图

```
                    ┌─────────────┐
         ┌─────────►│    new      │◄────────────────┐
         │          │   (新消息)   │                 │
         │          └──────┬──────┘                 │
         │                 │ claim                   │
         │                 ▼                         │ fail
         │          ┌─────────────┐   done          │ (retry)
         │          │   claimed   │─────────┐       │
         └──────────┤  (处理中)    │         │       │
    (timeout/steal) └─────────────┘         ▼       │
                                      ┌─────────────┐│
                                      │  completed  ││
                                      └──────┬──────┘│
                                             │        │
                                             ▼        │
                                       ┌─────────────┐│
                                       │  archived   │┘
                                       └─────────────┘

         ┌─────────────┐
         │   failed    │─────► 重试次数用尽 ───► deadletter
         │  (重试中)    │
         └─────────────┘
```

---

## 6. Courier API 规范

Mailbox CLI 通过以下 API 与 Courier 通信：

### 6.1 认领消息

```http
POST /api/v1/messages/{id}/claim
Content-Type: application/json

{
    "agent_id": "agent_001",
    "timeout": 300
}
```

**响应**:
```json
{
    "success": true,
    "message_id": "lark_om_abc123",
    "status": "claimed",
    "claimed_by": "agent_001",
    "claimed_at": "2026-02-06T20:45:00Z",
    "expires_at": "2026-02-06T20:50:00Z"
}
```

### 6.2 标记完成

```http
POST /api/v1/messages/{id}/complete
Content-Type: application/json

{
    "agent_id": "agent_001"
}
```

### 6.3 标记失败

```http
POST /api/v1/messages/{id}/fail
Content-Type: application/json

{
    "agent_id": "agent_001",
    "reason": "API 超时",
    "retryable": true
}
```

---

## 7. 典型工作流

### 7.1 消息处理流程

```bash
# 1. 查看新消息
monoco mailbox list

# 2. 读取消息详情
monoco mailbox read lark_om_abc123

# 3. 认领消息
monoco mailbox claim lark_om_abc123

# 4. ... Agent 处理逻辑 ...

# 5. 处理完成，触发归档
monoco mailbox done lark_om_abc123
```

### 7.2 批量处理

```bash
# 批量认领今日飞书消息
monoco mailbox list --provider lark --today --format id | monoco mailbox claim -

# 批量标记完成
monoco mailbox list --status claimed --format id | monoco mailbox done -
```

### 7.3 发送回复

```bash
# 1. 创建回复草稿
monoco mailbox send reply.md

# 2. 或直接快速发送
monoco mailbox send --provider lark --to "oc_123456" --text "问题已修复"
```

---

## 8. 错误处理

| 错误场景 | 命令 | 返回码 | 提示信息 |
|----------|------|--------|----------|
| 消息不存在 | 所有 | 1 | `Error: Message 'xxx' not found` |
| 消息已被认领 | `claim` | 2 | `Error: Message already claimed by agent_002` |
| 未认领就 done/fail | `done`/`fail` | 2 | `Error: Message not claimed by current agent` |
| Courier 未运行 | `claim`/`done`/`fail` | 3 | `Error: Courier service not running` |
| 认领超时 | `claim` | 4 | `Error: Claim request timeout` |

---

## 相关文档

- [01_Architecture](01_Architecture.md) - 整体架构设计
- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - 消息协议 Schema 规范
- [04_Courier_Service](04_Courier_Service.md) - Courier 服务架构设计
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
