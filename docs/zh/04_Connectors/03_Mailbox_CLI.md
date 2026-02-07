# Mailbox CLI 设计

**Version**: 2.0.0
**Status**: Draft
**Related**: FEAT-0191, FEAT-XXXX

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
├── sync          # 从全局 inbox 拉取 Mail（核心命令）
├── list          # 列出本地 Mail
├── read          # 读取 Mail 内容
├── send          # 发送 Mail（创建出站草稿）
├── claim         # 认领 Mail（调用 Courier API）
├── done          # 标记完成（调用 Courier API）
└── fail          # 标记失败（调用 Courier API）
```

---

## 3. 核心命令：同步

### 3.1 `mailbox sync`

从全局 inbox 拉取 Mail 到本地 Workspace。

```bash
# 基本用法
monoco mailbox sync                           # 增量拉取
monoco mailbox sync --full                    # 全量同步

# 筛选选项
monoco mailbox sync --since "1h"              # 最近1小时
monoco mailbox sync --provider lark           # 仅飞书

# 交互模式
monoco mailbox sync --interactive             # 逐条确认
```

**行为**:
1. 读取全局 inbox: `~/.monoco/mailbox/{source}/inbound/`
2. 按本地规则筛选感兴趣的 Mail
3. 硬链接/复制到本地 `.monoco/workspace/inbox/`
4. 更新本地 `cursor.json`

**本地规则配置** (`.monoco/mailbox/config.yaml`):

```yaml
mailbox:
  filters:
    # 按项目标识（如 @monoco::alpha）
    - type: mention
      pattern: "@monoco::alpha"

    # 按绑定的群聊
    - type: chat_binding
      chat_id: "slack:proj-alpha"

    # 按发送者域名
    - type: from_domain
      domain: "github.com"

    # 组合条件
    - type: all
      conditions:
        - type: provider
          value: email
        - type: subject_contains
          value: "[Project Alpha]"
```

**Cursor 文件** (`.monoco/mailbox/cursor.json`):

```json
{
  "last_sync": "2024-01-15T10:30:00Z",
  "processed_files": ["20240115-103022-a7f3e8d2"],
  "last_timestamp": "20240115-104511"
}
```

---

## 4. 本地命令

### 4.1 `mailbox list`

列出本地 Mail。

```bash
# 基本用法
monoco mailbox list                           # 列出所有本地 Mail
monoco mailbox list --unread                  # 仅未读

# 过滤选项
monoco mailbox list --provider lark           # 仅飞书
monoco mailbox list --today                   # 今天
monoco mailbox list --correlation "bug_123"   # 关联业务

# 输出格式
monoco mailbox list --format table            # 表格（默认）
monoco mailbox list --format json             # JSON
monoco mailbox list --format id               # 仅 ID
```

**输出示例**:

```
ID                        Provider    From                Status      Time        Preview
─────────────────────────────────────────────────────────────────────────────────────────────
lark_om_abc123            lark        IndenScale          new         2 min ago   "@monoco::alpha 帮我分析..."
email_a1b2c3d4            email       John Doe            synced      15 min ago  "[Project Alpha] API 设计..."
```

### 4.2 `mailbox read`

读取本地 Mail 内容。

```bash
# 基本用法
monoco mailbox read lark_om_abc123            # 读取 Mail
monoco mailbox read lark_om_abc123 --raw      # 显示原始文件

# 管道用法
monoco mailbox list --format id | head -1 | monoco mailbox read -
```

---

## 5. 状态流转命令

这些命令通过 HTTP API 与 Courier 通信，更新全局 Mail 状态。

### 5.1 `mailbox claim`

认领 Mail，表示当前 Workspace 将处理该 Mail。

```bash
# 基本用法
monoco mailbox claim lark_om_abc123           # 认领单条
monoco mailbox claim lark_om_abc123 lark_def  # 批量认领

# 管道用法
monoco mailbox list --status new --format id | monoco mailbox claim -
```

**Courier 行为**:
1. 验证 Mail 存在于全局 inbox
2. 从 `mailbox/{source}/inbound/` 移动到 `mailbox/{source}/processing/`
3. 记录认领 Workspace 路径
4. 返回确认

### 5.2 `mailbox done`

标记 Mail 处理完成。

```bash
monoco mailbox done lark_om_abc123            # 标记完成
monoco mailbox list --claimed --format id | monoco mailbox done -
```

**Courier 行为**:
1. 验证 Mail 由当前 Workspace 认领
2. 从 `mailbox/{source}/processing/` 移动到 `mailbox/{source}/archive/`
3. 清理状态

### 5.3 `mailbox fail`

标记 Mail 处理失败。

```bash
monoco mailbox fail lark_om_abc123                      # 标记失败
monoco mailbox fail lark_om_abc123 --reason "API 超时"   # 附带原因
```

---

## 6. 发送命令

### 6.1 `mailbox send`

创建出站 Mail 草稿。

```bash
# 从文件创建
monoco mailbox send draft.md

# 快速发送
monoco mailbox send --provider lark --to "oc_123456" --text "Hello"

# 关联业务
monoco mailbox send draft.md --correlation "bug_123"
```

**草稿位置**: `.monoco/mailbox/outbound/{provider}/`

---

## 7. 完整工作流

### 7.1 日常处理流程

```bash
# 1. 拉取新 Mail
$ monoco mailbox sync

# 2. 查看本地 Mail
$ monoco mailbox list

# 3. 读取 Mail 详情
$ monoco mailbox read lark_om_abc123

# 4. 认领 Mail（多 WS 可同时 claim）
$ monoco mailbox claim lark_om_abc123

# 5. ... Agent 处理逻辑 ...

# 6. 标记完成（更新全局状态）
$ monoco mailbox done lark_om_abc123
```

### 7.2 多 Workspace 协作

```bash
# Workspace A (~/Projects/alpha/)
$ cd ~/Projects/alpha
$ monoco mailbox sync
# 拉取 @monoco::alpha 相关 Mail

# Workspace B (~/work/beta/)
$ cd ~/work/beta
$ monoco mailbox sync
# 拉取 @monoco::beta 相关 Mail

# 同一 Mail 可同时存在于多个 workspace 的本地 inbox
# 多个 WS 可同时 claim 同一个 Mail（多模块协作）
```

---

## 8. 状态流转图

```
Global Inbox              Local Workspace
    │                            │
    │  sync                      │
    │────────────────────────────▶
    │                            │
    ▼                            ▼
┌────────┐                  ┌──────────┐
│  new   │                  │  local   │
│        │◀──── claim ──────│  inbox   │
└───┬────┘                  └────┬─────┘
    │                            │
    ▼                            ▼
┌────────┐                  ┌──────────┐
│processing│◀─── done ──────│ claimed  │
│        │   or fail        │          │
└───┬────┘                  └──────────┘
    │
    ▼
┌────────┐
│archive │
└────────┘
```

---

## 9. 错误处理

| 错误场景 | 命令 | 返回码 | 提示信息 |
|----------|------|--------|----------|
| 本地 Mail 不存在 | `read` | 1 | `Error: Mail not found in local inbox` |
| 全局 Mail 不存在 | `claim` | 2 | `Error: Mail not found in global inbox` |
| Courier 未运行 | `claim`/`done`/`fail` | 3 | `Error: Courier service not running` |

---

## 相关文档

- [01_Architecture](01_Architecture.md) - 整体架构设计
- [02_Mailbox_Protocol](02_Mailbox_Protocol.md) - Mail 协议 Schema 规范
- [04_Courier_Service](04_Courier_Service.md) - Courier 服务架构设计（用户级单例）
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
