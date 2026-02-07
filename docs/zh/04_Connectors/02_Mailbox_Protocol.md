# Mailbox 协议规范

**Version**: 1.0.0
**Status**: Draft
**Related**: FEAT-0189, EPIC-0035

---

## 1. 概述

本文档定义 Monoco Mailbox 协议的完整 Schema 规范，作为 Courier 与 Monoco 内核之间的**受保护物理接口**。

### 1.1 设计原则

1. **受保护空间 (Protected Space)**: `.monoco/mailbox/` 对 Agent 是只读的，所有写操作必须通过 Courier 服务完成
2. **物理分桶 + 逻辑建模**: 按 `provider` 分目录，复杂元数据封锁在 YAML Frontmatter 中
3. **多源兼容**: 统一 Schema 支持 IM (飞书/Lark) 和 Email 两种主要形态
4. **人类可读**: Markdown + YAML Frontmatter 格式，便于调试和审计

---

## 2. 物理存储结构

### 2.1 目录布局

```
.monoco/mailbox/
├── inbound/                    # 外部消息输入 (Courier 写入，Agent 只读)
│   ├── lark/                   # 飞书消息
│   ├── email/                  # 邮件消息
│   └── slack/                  # 其他适配器
├── outbound/                   # 内部消息输出 (Agent 通过 CLI 投递)
│   ├── lark/
│   ├── email/
│   └── slack/
├── archive/                    # 已完成闭环的消息存档
│   ├── lark/
│   ├── email/
│   └── slack/
└── .tmp/                       # 临时工作目录 (防抖合并用)
```

### 2.2 文件名规范

```
{ISO8601}_{Provider}_{UID}.md
```

- **ISO8601**: 时间戳，格式 `YYYYMMDDTHHMMSS` (UTC)
- **Provider**: 消息来源标识，如 `lark`, `email`, `slack`
- **UID**: 消息唯一标识，由 Provider 提供或 Courier 生成

**示例**:
- `20260206T204500_lark_msg_abc123.md`
- `20260206T204512_email_thread_xyz789.md`

---

## 3. Schema 规范

### 3.1 通用字段定义

所有消息文件必须包含以下 YAML Frontmatter:

```yaml
---
# ========== 核心标识 (Core Identity) ==========
id: string                    # 消息全局唯一标识 (格式: {provider}_{uid})
provider: enum                # 消息来源: lark | email | slack | discord | ...
direction: enum               # 消息方向: inbound | outbound

# ========== 会话上下文 (Session Context) ==========
session:
  id: string                  # 物理聚合标识符 (Channel/Chat ID 或邮箱地址)
  type: enum                  # 会话类型: direct | group | thread
  name: string                # 会话显示名称 (群名或联系人名)
  thread_key: string | null   # 逻辑话题标识 (IM: root_msg_id, Email: In-Reply-To/Thread-Topic)

# ========== 参与者 (Participants) ==========
participants:
  from: Participant           # 发送者信息
  to: Participant[]           # 主收件人列表
  cc: Participant[]           # 抄送人列表 (Email 专用，IM 为空)
  bcc: Participant[]          # 密送人列表 (Email 专用)
  mentions: Mention[]         # @提及列表 (IM 专用，Email 为空)

# ========== 时间戳 (Timestamps) ==========
timestamp: ISO8601            # 消息原始发送时间 (UTC)
received_at: ISO8601          # Courier 接收时间 (UTC)
processed_at: ISO8601 | null  # 处理完成时间 (Agent 写入)

# ========== 内容类型 (Content) ==========
type: enum                    # 内容类型: text | image | file | audio | video | card | mixed
content:
  text: string | null         # 纯文本内容 (提取后的文字)
  html: string | null         # HTML 格式内容 (Email 专用)
  markdown: string | null     # Markdown 格式内容

# ========== 附件与产物 (Artifacts) ==========
artifacts:                    # 附件列表，引用 dropzone 中的文件
  - id: string                # Artifact ID (SHA256 或 UUID)
    name: string              # 原始文件名
    type: enum                # 文件类型: image | document | audio | video | archive
    mime_type: string         # MIME 类型
    size: integer             # 文件大小 (bytes)
    path: string              # 相对于 .monoco/dropzone/ 的路径

# ========== 关联与追踪 (Correlation) ==========
correlation_id: string | null # 业务关联 ID (用于追踪特定任务闭环)
reply_to: string | null       # 回复目标消息 ID
thread_root: string | null    # 话题根消息 ID (用于深层嵌套回复)

# ========== 扩展字段 (Extensions) ==========
metadata:                     # 来源特定的原始元数据
  provider_raw: object        # Provider 原始消息结构 (保留字段，用于调试)
  extra: object               # 扩展字段
---
```

### 3.2 Participants 结构详解

#### 3.2.1 Participant 对象 (发送者/收件人)

```yaml
Participant:
  type: object
  required: [id, name]
  properties:
    id:                       # 平台用户唯一标识
      type: string
      description: Provider 级别的用户 ID

    name:                     # 显示名称
      type: string

    email:                    # 邮箱地址 (Email 必需，IM 可选)
      type: string
      format: email

    platform_id:              # 平台特定标识
      type: string
      description: 如飞书的 open_id, email 的 address

    role:                     # 在会话中的角色
      type: enum
      enum: [owner, admin, member, guest, external]
      default: member

    avatar:                   # 头像 URL
      type: string
      format: uri
```

#### 3.2.2 Mention 对象 (IM @提及)

```yaml
Mention:
  type: object
  required: [type, target]
  properties:
    type:                     # 提及类型
      type: enum
      enum: [user, all, channel, role]
      description: user=个人, all=@所有人, channel=@频道, role=@角色

    target:                   # 提及目标
      type: string
      description: 用户 ID 或特殊标识 (如 "all")

    name:                     # 显示文本
      type: string
      description: 如 "@IndenScale" 中的 "IndenScale"

    offset:                   # 在文本中的位置
      type: integer
      description: 用于高亮显示
```

### 3.3 Session 结构详解

```yaml
Session:
  type: object
  required: [id, type]
  properties:
    id:                       # 物理聚合标识符
      type: string
      description: |
        - IM: chat_id, channel_id, group_id
        - Email: 收件人邮箱地址或 Thread-Topic Hash

    type:                     # 会话类型
      type: enum
      enum: [direct, group, thread]
      description: |
        - direct: 单聊 (1对1)
        - group: 群聊 (多对多)
        - thread: 话题/线程模式

    name:                     # 会话显示名称
      type: string

    thread_key:               # 逻辑话题标识
      type: string | null
      description: |
        用于将同一物理会话中的不同话题区分开：
        - IM: root_message_id 或 thread_id
        - Email: In-Reply-To 链的 Root Message-ID
        - 新话题: null
```

### 3.4 Thread 关联逻辑

#### 3.4.1 IM Thread 映射 (Lark/Slack)

| 概念 | 映射到 Schema | 说明 |
|------|--------------|------|
| Chat/Channel | `session.id` | 物理聚合标识 |
| Thread/Topic | `session.thread_key` | 逻辑话题标识 |
| Root Message | `thread_root` | 话题根消息 ID |
| Parent Message | `reply_to` | 直接回复的目标 |
| Message | `id` | 消息唯一标识 |

**示例场景**: 用户在群聊中针对某条消息回复
```yaml
session:
  id: "oc_123456"                    # 群聊 ID
  type: "group"
  name: "Monoco Dev Group"
  thread_key: "om_abc123"            # 话题根消息 ID
thread_root: "om_abc123"             # 话题根消息
reply_to: "om_def456"                # 直接回复的消息 ID
```

#### 3.4.2 Email Thread 映射

| 概念 | 映射到 Schema | 说明 |
|------|--------------|------|
| To/Cc | `participants.to`, `participants.cc` | 收件人列表 |
| Thread-Topic | `session.id` 或 `session.thread_key` | 邮件主题规范化 |
| In-Reply-To | `reply_to` | 回复的 Message-ID |
| References | `thread_root` | 引用链的根 |
| Message-ID | `id` | 邮件唯一标识 |

**示例场景**: 邮件回复链
```yaml
id: "email_<message-id-hash>"
session:
  id: "thread:project-alpha"         # 基于主题的 Thread Hash
  type: "thread"
  name: "Re: [Project Alpha] Design Review"
  thread_key: "thread:project-alpha"
reply_to: "email_<parent-msg-id>"
thread_root: "email_<root-msg-id>"
```

---

## 4. Provider 特定示例

### 4.1 飞书 (Lark) - 群聊消息

```markdown
---
id: "lark_om_abc123"
provider: lark
direction: inbound
session:
  id: "oc_123456"
  type: group
  name: "Monoco Dev Group"
  thread_key: null
participants:
  from:
    id: "ou_user123"
    name: "IndenScale"
    platform_id: "ou_user123"
    role: owner
  to: []
  cc: []
  mentions:
    - type: user
      target: "ou_prime456"
      name: "Prime"
      offset: 12
timestamp: "2026-02-06T20:45:00Z"
received_at: "2026-02-06T20:45:02Z"
type: text
content:
  text: "@Prime 帮我分析一下这个 Bug"
  html: null
  markdown: null
artifacts: []
correlation_id: null
reply_to: null
thread_root: null
metadata:
  provider_raw:
    chat_type: group
    msg_type: text
    create_time: "1707249900000"
---
@Prime 帮我分析一下这个 Bug
```

### 4.2 飞书 (Lark) - 话题回复

```markdown
---
id: "lark_om_def456"
provider: lark
direction: inbound
session:
  id: "oc_123456"
  type: group
  name: "Monoco Dev Group"
  thread_key: "om_abc123"
participants:
  from:
    id: "ou_prime456"
    name: "Prime"
    platform_id: "ou_prime456"
    role: member
  to: []
  cc: []
  mentions: []
timestamp: "2026-02-06T20:46:30Z"
received_at: "2026-02-06T20:46:32Z"
type: text
content:
  text: "收到，请提供错误日志"
  html: null
  markdown: null
artifacts: []
correlation_id: "task_bug_789"
reply_to: "lark_om_abc123"
thread_root: "lark_om_abc123"
metadata:
  provider_raw:
    thread_id: "om_abc123"
    parent_id: "om_abc123"
---
收到，请提供错误日志
```

### 4.3 邮件 (Email) - 带附件

```markdown
---
id: "email_a1b2c3d4"
provider: email
direction: inbound
session:
  id: "thread:design-review"
  type: thread
  name: "Re: [Design Review] API Schema"
  thread_key: "thread:design-review"
participants:
  from:
    id: "user@example.com"
    name: "John Doe"
    email: "user@example.com"
    platform_id: "user@example.com"
  to:
    - id: "team@monoco.dev"
      name: "Monoco Team"
      email: "team@monoco.dev"
  cc:
    - id: "manager@example.com"
      name: "Manager"
      email: "manager@example.com"
  bcc: []
  mentions: []
timestamp: "2026-02-06T18:30:00Z"
received_at: "2026-02-06T18:31:15Z"
type: mixed
content:
  text: "请查看附件中的 API 设计文档，有问题请反馈。"
  html: "<p>请查看附件中的 API 设计文档，有问题请反馈。</p>"
  markdown: "请查看附件中的 API 设计文档，有问题请反馈。"
artifacts:
  - id: "sha256:abc123..."
    name: "api-design-v2.pdf"
    type: document
    mime_type: "application/pdf"
    size: 2048576
    path: "inbound/email_20260206/api-design-v2.pdf"
correlation_id: "epic_api_design"
reply_to: "email_x9y8z7w6"
thread_root: "email_root123"
metadata:
  provider_raw:
    message_id: "<msg123@example.com>"
    in_reply_to: "<msg456@monoco.dev>"
    references: ["<root@monoco.dev>", "<msg456@monoco.dev>"]
    subject: "Re: [Design Review] API Schema"
---
请查看附件中的 API 设计文档，有问题请反馈。

[附件: api-design-v2.pdf]
```

### 4.4 邮件 (Email) - 新话题

```markdown
---
id: "email_new_xyz789"
provider: email
direction: inbound
session:
  id: "thread:new-feature"
  type: thread
  name: "[Feature Request] Mailbox Protocol"
  thread_key: null
participants:
  from:
    id: "inden@monoco.dev"
    name: "IndenScale"
    email: "inden@monoco.dev"
  to:
    - id: "dev@monoco.dev"
      name: "Dev Team"
      email: "dev@monoco.dev"
  cc: []
  bcc: []
  mentions: []
timestamp: "2026-02-06T10:00:00Z"
received_at: "2026-02-06T10:05:00Z"
type: text
content:
  text: "建议实现 Mailbox 协议来规范消息处理..."
  html: null
  markdown: null
artifacts: []
correlation_id: null
reply_to: null
thread_root: null
metadata:
  provider_raw:
    message_id: "<new@monoco.dev>"
    subject: "[Feature Request] Mailbox Protocol"
---
建议实现 Mailbox 协议来规范消息处理...
```

---

## 5. Outbound Schema (Agent -> 外部)

### 5.1 发送契约

Agent 在工作目录创建草稿文件，通过 `monoco courier send <file>` 投递。

```yaml
---
# ========== 目标信息 (Target) ==========
to: string | string[]         # 目标用户/群组 ID 或邮箱
cc: string | string[]         # 抄送 (Email)
bcc: string | string[]        # 密送 (Email)

# ========== 上下文 (Context) ==========
provider: enum                # 目标平台: lark | email | ...
reply_to: string | null       # 回复的目标消息 ID
thread_key: string | null     # 话题标识 (保持上下文)

# ========== 内容 (Content) ==========
type: enum                    # 内容类型: text | card | markdown | html
content:                      # 内容载体
  text: string | null
  markdown: string | null
  html: string | null
  card: object | null         # 飞书/Slack 卡片结构

# ========== 附件 (Artifacts) ==========
artifacts:                    # 要附加的文件
  - id: string                # Artifact ID
    name: string              # 显示名称
    inline: boolean           # 是否为内嵌附件

# ========== 选项 (Options) ==========
options:
  silent: boolean             # 是否静默发送 (不触发通知)
  urgent: boolean             # 是否紧急
  schedule_at: ISO8601 | null # 定时发送
---
```

### 5.2 Outbound 示例 - 飞书卡片

```markdown
---
to: "oc_123456"
provider: lark
reply_to: "lark_om_abc123"
thread_key: "om_abc123"
type: card
content:
  card:
    header:
      title: "Bug 分析完成"
      template: "green"
    elements:
      - tag: div
        text: "问题已定位：内存溢出"
      - tag: action
        actions:
          - tag: button
            text: "查看 PR"
            url: "https://github.com/..."
artifacts: []
options:
  silent: false
---
```

### 5.3 Outbound 示例 - 邮件回复

```markdown
---
to: "user@example.com"
cc: "manager@example.com"
provider: email
reply_to: "email_a1b2c3d4"
thread_key: "thread:design-review"
type: markdown
content:
  markdown: |
    ## 评审意见

    1. API 命名需要调整
    2. 缺少错误处理说明

    请修改后重新提交。
artifacts:
  - id: "sha256:def789..."
    name: "review-comments.pdf"
    inline: false
options:
  urgent: false
---
```

---

## 6. Correlation ID 消费逻辑

### 6.1 用途

`correlation_id` 用于追踪跨消息的**业务闭环**:

- Bug 报告 -> 分析 -> 修复 -> 通知
- 任务分配 -> 执行 -> 验收 -> 归档
- 问题咨询 -> 回答 -> 确认 -> 关闭

### 6.2 生成规则

```
{category}_{entity_id}_{timestamp}
```

- **category**: `bug`, `task`, `epic`, `issue`, `pr`, `incident`
- **entity_id**: 关联实体的 ID
- **timestamp**: 可选，用于区分同一实体的不同会话

**示例**:
- `bug_FEAT-0189_20260206`
- `epic_API-Redesign`
- `incident_Production-Down-20260206`

### 6.3 Agent 回溯逻辑

当 Agent 收到带有 `correlation_id` 的消息时：

1. **查询历史**: 扫描 `archive/` 中相同 `correlation_id` 的消息
2. **加载上下文**: 读取关联的 Issue/Memo/Artifact
3. **状态恢复**: 重建会话上下文，继续处理

```python
# 伪代码示例
def load_correlation_context(corr_id: str) -> Context:
    messages = scan_mailbox(
        paths=["inbound/", "archive/"],
        filter=lambda m: m.correlation_id == corr_id,
        order_by="timestamp"
    )

    # 加载关联的 Issue
    issue_id = extract_issue_id(corr_id)
    issue = load_issue(issue_id)

    return Context(messages=messages, issue=issue)
```

---

## 7. 附录

### 7.1 类型枚举定义

```yaml
Provider:
  type: enum
  values: [lark, email, slack, discord, teams, wecom, dingtalk]

Direction:
  type: enum
  values: [inbound, outbound]

SessionType:
  type: enum
  values: [direct, group, thread]

ContentType:
  type: enum
  values: [text, html, markdown, image, file, audio, video, card, mixed]

ArtifactType:
  type: enum
  values: [image, document, audio, video, archive, code, unknown]

Role:
  type: enum
  values: [owner, admin, member, guest, external]
```

### 7.2 完整 Inbound Schema (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://monoco.dev/schemas/mailbox/inbound-v1.json",
  "title": "Mailbox Inbound Message",
  "type": "object",
  "required": ["id", "provider", "direction", "session", "participants", "timestamp", "type"],
  "properties": {
    "id": { "type": "string", "pattern": "^[a-z]+_[a-zA-Z0-9_-]+$" },
    "provider": { "type": "string", "enum": ["lark", "email", "slack", "discord"] },
    "direction": { "type": "string", "enum": ["inbound", "outbound"] },
    "session": {
      "type": "object",
      "required": ["id", "type"],
      "properties": {
        "id": { "type": "string" },
        "type": { "type": "string", "enum": ["direct", "group", "thread"] },
        "name": { "type": "string" },
        "thread_key": { "type": ["string", "null"] }
      }
    },
    "participants": {
      "type": "object",
      "required": ["from"],
      "properties": {
        "from": { "$ref": "#/definitions/participant" },
        "to": { "type": "array", "items": { "$ref": "#/definitions/participant" } },
        "cc": { "type": "array", "items": { "$ref": "#/definitions/participant" } },
        "bcc": { "type": "array", "items": { "$ref": "#/definitions/participant" } },
        "mentions": { "type": "array", "items": { "$ref": "#/definitions/mention" } }
      }
    },
    "timestamp": { "type": "string", "format": "date-time" },
    "received_at": { "type": "string", "format": "date-time" },
    "processed_at": { "type": ["string", "null"], "format": "date-time" },
    "type": { "type": "string", "enum": ["text", "image", "file", "audio", "video", "card", "mixed"] },
    "content": {
      "type": "object",
      "properties": {
        "text": { "type": ["string", "null"] },
        "html": { "type": ["string", "null"] },
        "markdown": { "type": ["string", "null"] }
      }
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "type"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "type": { "type": "string", "enum": ["image", "document", "audio", "video", "archive"] },
          "mime_type": { "type": "string" },
          "size": { "type": "integer" },
          "path": { "type": "string" }
        }
      }
    },
    "correlation_id": { "type": ["string", "null"] },
    "reply_to": { "type": ["string", "null"] },
    "thread_root": { "type": ["string", "null"] },
    "metadata": { "type": "object" }
  },
  "definitions": {
    "participant": {
      "type": "object",
      "required": ["id", "name"],
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "email": { "type": "string", "format": "email" },
        "platform_id": { "type": "string" },
        "role": { "type": "string", "enum": ["owner", "admin", "member", "guest", "external"] },
        "avatar": { "type": "string", "format": "uri" }
      }
    },
    "mention": {
      "type": "object",
      "required": ["type", "target"],
      "properties": {
        "type": { "type": "string", "enum": ["user", "all", "channel", "role"] },
        "target": { "type": "string" },
        "name": { "type": "string" },
        "offset": { "type": "integer" }
      }
    }
  }
}
```

---

## 相关文档

- [01_Architecture](01_Architecture.md) - 整体架构设计
- [03_Mailbox_CLI](03_Mailbox_CLI.md) - Mailbox CLI 命令设计
- [04_Courier_Service](04_Courier_Service.md) - Courier 服务架构设计
- [05_Courier_CLI](05_Courier_CLI.md) - Courier CLI 命令设计
