# Discussion: Mailbox Protocol & Directory-based Message Bus

**Date**: 2026-02-06
**Context**: EPIC-0035 Implementation of Monoco Courier
**Goal**: Define a robust, file-based mailbox protocol for IM (Lark/Email) integration, moving away from the shared `Memos/inbox.md` to avoid race conditions and latency.

---

## 1. 物理架构 (Physical Structure)

不再使用单文件追加，改用 **Maildir 模式**，利用文件系统的原子创建能力进行解耦。

目录：`.monoco/mailbox/`

- `inbound/` : 由 Courier (Sidecar) 写入。所有未处理的外部消息。
- `outbound/` : 由 Agents 写入。待 Courier 推送至外部。
- `archive/` : 已完成闭环的消息存档。

**物理镜像原则 (Mirrored Structure)**：上述三个目录内部均按 `provider` 建立二级子目录（如 `inbound/lark/`, `outbound/lark/`, `archive/lark/`），以实现适配器的监听隔离与差异化清理策略。

文件名规范：`{ISO8601}_{Provider}_{UID}.md`
例如：`20260206T2045_lark_abc123.md`

## 2. 消息协议契约 (Message Schema)

消息文件采用 **Markdown + YAML Frontmatter** 格式，确保人类可读且 Agent 易读。

### Inbound Schema (外部 -> Monoco)

```yaml
---
id: 'msg_lark_001'
provider: 'lark'
session:
  id: 'chat_888' # 物理聚合标识符 (Channel ID)
  type: 'group' # group (群聊), direct (单聊), thread (会话)
  name: 'Monoco Dev Group'
participants:
  sender: { id: 'u_1', name: 'IndenScale', role: 'owner' }
  recipients: [] # IM 可能为空，Email 会有多个
  cc: [] # Email 专属字段
  mentions: ['@Prime'] # IM 专属字段
timestamp: '2026-02-06T20:45:00'
type: 'text' # text, image, file, audio
artifacts:
  - 'sha256:xxxx' # 附件落地后生成的 Hash
---
帮我分析一下这个 Bug，附件里是错误日志。
```

### Outbound Schema (Monoco -> 外部)

```yaml
---
to: "user_888"
provider: "lark"
reply_to: "msg_lark_001" # 引用原始消息实现上下文对齐
msg_type: "interactive_card" # 交互卡片或普通文本
artifacts: []
---

Prime Engineer 已经定位问题：
- **原因**: 内存溢出
- **建议**: 合并 PR #45
```

## 3. 生命周期与触发链 (Lifecycle) - 受保护模式 (Protected Mode)

Monoco 采用 **“内核-用户空间隔离”** 模式管理物流：

- **Kernel/System Area**: `.monoco/mailbox/` (仅 Courier 和 monoco CLI 可写)
- **User/Agent Area**: `Issues/Features/.../` (Agent 的自由作业区)

1. **Ingress**: `Courier` 收到 Webhook -> 写入 `.monoco/mailbox/inbound/` 文件。
2. **Trigger**: `monoco serve` 捕获事件 -> 拉起 **Prime Agent**。
3. **Execution**: **Agent** 在其工作目录下进行推理和编码，如果需要回复：
   - **Step 3.1**: 在本地工作目录写入 `draft.md`。
   - **Step 3.2**: 执行 `monoco courier send draft.md`。
4. **Relay (CLI)**: CLI 校验 Frontmatter 格式 -> 将文件原子化移动或拷贝至 `.monoco/mailbox/outbound/`。
5. **Egress**: `Courier` 监听 `outbound/` -> 调用接口发送 -> 移动至 `archive/`。

**核心哲学**：Agent 永远不应该直接 `touch` 受保护的 `mailbox` 目录，所有的写操作必须通过有状态校验的 CLI 完成。防止 Agent 在逻辑混乱时删除历史事实（Inbound/Archive）。

## 5. 深度分析：多源适配与流式处理 (Deep Dive: Multi-source & Streaming)

### 5.1 多源标识与会话隔离 (Source & Session Differentiation)

**问题 1**：如何区分不同 Source (Email, Lark, Discord等)？是否需要独立目录？

**建议方案**：**物理分箱 + 逻辑会话 (Physical Binning + Logical Sessioning)**

- **物理分箱**：在 `inbound/` 下按 `provider` 建立子目录。
  - `inbound/lark/`
  - `inbound/email/`
  - 理由：不同适配器的速率、鉴权机制和清理策略不同，分箱可以隔离侧车的运维压力。
- **逻辑会话 (Session Entity)**：在 Frontmatter 中引入核心字段：
  - `session_id`: 跨消息的唯一会话标识。对于 IM 是 `chat_id` 或 `thread_id`；对于 Email 是 `Thread-Topic` 的 Hash。
  - `correlation_id`: 用于追踪特定任务的闭环。
- **建模抽象**：
  - 不需要为每个 Source 独立建模，但需要一个 **“会话上下文 (Conversation Context)”** 缓存，记录该 `session_id` 当前关联的 `AgentTask` 或 `IssueID`。

### 5.2 流式 IM 的批处理逻辑 (Handling Streaming IM vs. Atomic Email)

**问题 2**：邮件是原子的，IM 是流式的（用户连发 3 条），如何划分 Batch？

**建议方案**：**侧车防抖 + 窗口化消费 (Sidecar Debouncing + Windowed Consumption)**

- **方案 A：侧车防抖 (Courier-side Debouncing)** —— _推荐_
  - `Courier` 收到消息后不立即落地，而是启动一个 **“静止窗口 (Quiescence Window)”**（例如 30 秒）。
  - 在窗口期内收到的同一 `session_id` 的消息被拼接到同一个 Batch 文件中。
  - 窗口结束（用户停止输入）后，一次性写入 `inbound/`。
  - **优点**：极大减少 Agent 被频繁拉起的成本，符合人类对话习惯。
- **方案 B：窗口化消费 (Windowed Consumption)**
  - 每一个 IM 消息都是一个独立文件进入 `inbound/`。
  - 触发 `Prime Engineer` 后，它不只读当前文件，而是扫描整个 `inbound/lark/{session_id}/*.md`。
  - **优点**：响应极快，但 Agent 的 Prompt 构造会变复杂。

## 6. 最终设计结论 (Final Design Conclusion)

经过评估，Monoco Courier 将采用以下核心设计方案：

1.  **物理架构**：采用 **Maildir 模式**。
    - 根目录：`.monoco/mailbox/`
    - 子目录：`inbound/`, `outbound/`, `archive/`
    - **物理分桶**：所有根目录下均按 `provider` 建立二级目录（如 `inbound/lark/`, `outbound/lark/`）实现监听隔离。
2.  **协议契约**：采用 **Markdown + YAML Frontmatter**，遵循“物理分桶，逻辑建模”。
    - **核心标识**：使用 `session.id` 追踪会话。
    - **多态参与者**：发件人、抄送人、提及人员及聊天类型（单聊/群聊）全部封锁在 Frontmatter 中，不再下钻物理目录。
    - **附件关联**：使用 `artifacts` 数组关联 `dropzone` 中的文件。
3.  **防抖策略**：采用 **方案 A：侧车防抖 (Courier-side Debouncing)**。
    - **逻辑原子化**：Courier 负责在 30s 的静止窗口内合并流式输入，避免 Agent 频繁冷启动。
    - **差异化窗口**：IM 默认为 30s，Email 默认为 0s。

---

**IndenScale，结论已记录。该方案完美平衡了系统的响应性与计算成本。后续将根据此协议进入 EPIC-0035 的开发阶段。**
