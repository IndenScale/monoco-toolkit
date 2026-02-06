# ADR-003: Mailbox Protocol Schema Specification

**Status**: Draft
**Date**: 2026-02-06
**Author**: Monoco Team
**Related**: EPIC-0035, FEAT-0189

## 1. 概述 (Overview)

Mailbox Protocol 是 Monoco Courier 与内核之间的**受保护物理接口**，采用基于文件的 Maildir 模式，实现外部消息（IM、Email 等）的标准化接入。

### 1.1 设计原则

- **受保护访问**：`.monoco/mailbox/` 对 Agent 只读，写入必须通过 CLI
- **物理-逻辑分离**：物理目录按 provider 分箱，逻辑关系封锁在 YAML 中
- **原子操作**：利用文件系统原子性实现无锁并发
- **人类可读**：Markdown + YAML Frontmatter 格式

---

## 2. 物理架构 (Physical Structure)

### 2.1 目录布局

```
.monoco/
├── mailbox/                    # 受保护目录 (CLI/Courier 可写)
│   ├── inbound/               # 外部消息入口
│   │   ├── lark/             # 飞书消息
│   │   ├── email/            # 邮件
│   │   ├── discord/          # Discord
│   │   └── ...
│   ├── outbound/              # 待发送消息
│   │   ├── lark/
│   │   ├── email/
│   │   └── ...
│   └── archive/               # 已完成消息存档
│       ├── lark/
│       ├── email/
│       └── ...
└── dropzone/                  # 附件投递区 (Mailroom 处理)
```

### 2.2 文件命名规范

```
{ISO8601}_{Provider}_{UID}.md

# 示例
20260206T204530_lark_abc123.md
20260206T204531_email_thread_xyz789.md
```

---

## 3. Schema 规范 (Schema Specification)

### 3.1 参与者结构 (Participants)

支持 Email 风格（from/to/cc）和 IM 风格（sender/mentions）的多态统一：

```yaml
participants:
  sender:
    id: "u_123"                    # 唯一标识
    name: "张三"                    # 显示名称
    platform_id: "ou_abc"          # 平台特定 ID
    email: "zhangsan@example.com"  # 邮箱（可选）
    role: "owner"                  # owner|admin|member|guest|bot
    metadata: {}                   # 扩展字段

  recipients: []                   # 主收件人（Email 风格）
  cc: []                          # 抄送（Email 风格）
  bcc: []                         # 密送（Email 风格）

  mentions:                       # @提及（IM 风格）
    - "@Prime"
    - "@engineer"

  reply_to:                       # 回复目标
    id: "u_456"
    name: "李四"
```

### 3.2 Session 与 Thread 映射

**双键策略**：物理聚合 + 逻辑话题

```yaml
session:
  id: "chat_888"                  # 物理会话 ID（频道/聊天室）
  type: "group"                   # direct|group|thread|channel
  name: "Monoco Dev Group"        # 会话名称

  # --- Thread 关联逻辑 ---
  thread_key: "thread_abc123"     # 逻辑话题标识
  parent_id: "msg_001"            # 父消息 ID（嵌套回复）
  root_id: "msg_root"             # 根消息 ID（线程重建）
```

#### Thread 映射规则

| 源类型 | session.id | session.thread_key | parent_id | root_id |
|--------|-----------|-------------------|-----------|---------|
| **Lark 群聊** | chat_id | thread_id (话题 ID) | - | - |
| **Lark 回复** | chat_id | thread_id | parent_message_id | root_message_id |
| **Email** | mailbox_folder_hash | In-Reply-To/References Hash | - | Thread-Topic Hash |
| **Discord** | channel_id | thread_id | - | - |

### 3.3 Inbound Message Schema

外部消息进入 Monoco 的标准格式：

```yaml
---
# === 核心标识 ===
id: "msg_lark_001"               # 消息唯一 ID
provider: "lark"                 # lark|email|discord|...

# === 会话上下文 ===
session:
  id: "chat_888"
  type: "group"
  name: "Monoco Dev Group"
  thread_key: "thread_001"

# === 参与者 ===
participants:
  sender:
    id: "u_1"
    name: "IndenScale"
    role: "owner"
  mentions:
    - "@Prime"

# === 元数据 ===
timestamp: "2026-02-06T20:45:00+08:00"
type: "text"                     # text|image|file|audio|video|card

# === 附件 ===
artifacts:
  - hash: "sha256:abc123..."
    name: "error.log"
    mime_type: "text/plain"
    size: 1024

# === 关联追踪 ===
correlation:
  correlation_id: "corr_xyz789"   # 任务链追踪 ID
  request_id: "req_001"           # 幂等性标识
  ref_issue: "FEAT-0189"          # 关联 Issue
  ref_agent: "PrimeEngineer"      # 处理 Agent
  chain:                          # 消息链
    - "msg_prev_001"
    - "msg_prev_002"

# === 原始数据 ===
raw_metadata: {}                 # 平台原始数据（调试用）
---

消息正文内容（Markdown 格式）...
```

### 3.4 Outbound Message Schema

Monoco 发往外部的消息格式：

```yaml
---
# === 回复引用 ===
reply_to: "msg_lark_001"         # 回复的目标消息
thread_to: "thread_001"          # 继续的话题

# === 目标 ===
provider: "lark"
delivery_method: "reply"         # reply|direct|broadcast

# === 会话 ===
session:
  id: "chat_888"
  type: "group"

# === 内容 ===
timestamp: "2026-02-06T20:50:00+08:00"
type: "markdown"

# === 附件 ===
artifacts:
  - hash: "sha256:def456..."

# === 卡片模板（可选）===
template: "issue_card_v1"
template_data:
  issue_id: "FEAT-0189"
  status: "in_progress"
---

Prime Engineer 已定位问题：
- **原因**: 内存溢出
- **建议**: 合并 PR #45
```

### 3.5 Draft Message Schema (Agent 工作区)

Agent 在 Feature 分支工作目录撰写的草稿：

```yaml
---
# === 目标（CLI 可解析或交互确认）===
to: "@IndenScale"                # @user, email, 或 channel
reply_to: "msg_lark_001"         # 回复引用
correlation_id: "corr_xyz789"    # 延续关联

# === 内容提示 ===
provider: "lark"                 # 目标平台提示
msg_type: "text"                 # text|markdown|card
artifacts:                       # 附件 hash 列表
  - "sha256:abc123..."

# === 元数据 ===
priority: "normal"               # low|normal|high|urgent
ref_issue: "FEAT-0189"           # 关联 Issue
ref_agent: "PrimeEngineer"       # 创建 Agent
draft_version: "1.0"
---

这是 Agent 撰写的回复内容...
```

**存储位置建议**：`Issues/Features/work/drafts/`

---

## 4. CLI 投递契约 (CLI Delivery Contract)

### 4.1 `monoco courier send <file>` 规范

**入参**：

```bash
monoco courier send <draft_file> [options]

Options:
  --dry-run          # 验证不投递
  --force            # 跳过确认
  --provider <name>  # 覆盖目标平台
  --to <recipient>   # 覆盖接收者
```

**校验逻辑**：

1. **Schema 校验**：验证 YAML Frontmatter 符合 DraftMessage 规范
2. **Provider 解析**：根据 `--provider` 或 draft 中的 provider 确定目标
3. **目标解析**：将 `to` 字段解析为平台特定 ID
4. **correlation_id 继承**：如 draft 未指定，从 `reply_to` 关联的 inbound 消息继承
5. **原子投递**：校验通过后，原子写入 `.monoco/mailbox/outbound/{provider}/`

### 4.2 状态转换流程

```
Agent Workspace          CLI Validation          Outbound Queue         Courier
     |                        |                        |                   |
     | write draft.md         |                        |                   |
     |----------------------->|                        |                   |
     |                        |                        |                   |
     |                        | monoco courier send    |                   |
     |                        | draft.md               |                   |
     |                       --> 1. Validate Schema    |                   |
     |                       |  2. Resolve Provider    |                   |
     |                       |  3. Resolve Recipients  |                   |
     |                       |  4. Enrich metadata     |                   |
     |                       |                        |                   |
     |                       | atomic write           |                   |
     |                       |----------------------->|                   |
     |                       |                        | detect file       |
     |                       |                        |------------------>|
     |                       |                        |                   |
     |                       |                        | move to archive   |
     |                       |                        |<------------------|
```

---

## 5. Correlation ID 消费逻辑

### 5.1 生成规则

- **新任务**：Courier 生成新的 `correlation_id` (uuid 或 nanoid)
- **上下文延续**：Agent 回复时继承 `reply_to` 消息的 `correlation_id`

### 5.2 Agent 回溯策略

Agent 收到消息后，可通过 `correlation_id` 查询历史上下文：

```python
# 伪代码示例
async def get_correlation_context(corr_id: str) -> list[Message]:
    """获取关联链上的所有消息"""
    # 1. 查询 archive/{provider}/ 中 correlation.correlation_id = corr_id 的消息
    # 2. 按 timestamp 排序
    # 3. 返回消息链
    pass
```

### 5.3 Issue/Memo 关联

- `ref_issue`: Agent 可将消息关联到特定 Issue，便于后续归档
- `ref_memo`: 与 Memo 系统的临时笔记关联

---

## 6. 示例 (Examples)

### 6.1 飞书群聊消息

```yaml
---
id: "msg_lark_abc123"
provider: "lark"
session:
  id: "oc_123456"
  type: "group"
  name: "Engineering Team"
participants:
  sender:
    id: "ou_user123"
    name: "张三"
    platform_id: "ou_user123"
    role: "member"
  mentions:
    - "@Prime"
timestamp: "2026-02-06T14:30:00+08:00"
type: "text"
correlation:
  correlation_id: "corr_20260206_001"
---

@Prime 帮我看看这个报错是什么意思？
```

### 6.2 邮件线程

```yaml
---
id: "msg_email_xyz789"
provider: "email"
session:
  id: "inbox_work"
  type: "direct"
  thread_key: "sha256:thread_hash_abc..."
participants:
  sender:
    id: "alice@example.com"
    name: "Alice"
    email: "alice@example.com"
  recipients:
    - id: "team@company.com"
      name: "Engineering Team"
      email: "team@company.com"
  cc:
    - id: "bob@example.com"
      name: "Bob"
      email: "bob@example.com"
timestamp: "2026-02-06T10:00:00Z"
type: "text"
correlation:
  correlation_id: "corr_email_456"
  chain:
    - "msg_email_prev_111"
---

关于项目进度的讨论...
```

### 6.3 Agent 草稿

```yaml
---
to: "@张三"
reply_to: "msg_lark_abc123"
provider: "lark"
msg_type: "markdown"
ref_issue: "FEAT-0189"
ref_agent: "PrimeEngineer"
correlation_id: "corr_20260206_001"
priority: "normal"
draft_version: "1.0"
---

这是一个内存溢出问题。建议：
1. 检查第 45 行的循环
2. 增加内存限制配置
3. 参考 [文档链接]
```

---

## 7. 版本与演进

**Protocol Version**: 1.0.0

### 7.1 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-02-06 | 初始版本定义 |

### 7.2 向后兼容策略

- 新增字段必须为 Optional
- 废弃字段保留至少 2 个 minor 版本
- Provider 扩展通过 `raw_metadata` 字段实现
