---
id: FEAT-0189
uid: 6d2c91
type: feature
status: open
stage: done
title: 定义 Mailbox 协议存储格式与 Schema 规范
created_at: '2026-02-06T21:10:53'
updated_at: '2026-02-06T22:10:54'
parent: EPIC-0035
dependencies: []
related:
- EPIC-0035
domains:
- CollaborationBus
tags:
- '#EPIC-0000'
- '#EPIC-0035'
- '#FEAT-0189'
files:
- ADRs/ADR-003-Mailbox-Protocol-Schema.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Epics/open/EPIC-0035-实现-monoco-courier-外部物流层.md
- Issues/Features/closed/FEAT-0188-intelligent-browser-integration-via-proxy-hooks.md
- Issues/Features/open/FEAT-0188-intelligent-browser-integration-via-proxy-hooks.md
- Issues/Features/open/closed/FEAT-0134-monoco-cockpit-settings.md
- Issues/Features/open/closed/FEAT-0137-unified-module-loader-and-lifecycle-management.md
- Issues/Features/open/closed/FEAT-0138-implement-agent-session-persistence.md
- Issues/Features/open/closed/FEAT-0140-daemon-orchestrator.md
- Issues/Features/open/closed/FEAT-0141-native-git-hooks-management-integration.md
- Issues/Features/open/closed/FEAT-0142-implement-monoco-toolkit-root-structure.md
- Issues/Features/open/closed/FEAT-0143-support-block-level-language-detection-in-i18n-li.md
- Issues/Features/open/closed/FEAT-0144-enforce-strict-status-and-directory-consistency-i.md
- Issues/Features/open/closed/FEAT-0145-integrate-git-hooks-for-development-workflow.md
- Issues/Features/open/closed/FEAT-0146-implement-cli-command-for-issue-domain-management.md
- Issues/Features/open/closed/FEAT-0147-implement-memo-to-issue-linkage-on-cli.md
- Issues/Features/open/closed/FEAT-0148-issue-module-skill-refactor.md
- Issues/Features/open/closed/FEAT-0151-monoco-artifact-core-metadata-registry-and-cas-sto.md
- Issues/Features/open/closed/FEAT-0152-monoco-artifact-skills-multi-modal-document-proces.md
- Issues/Features/open/closed/FEAT-0153-monoco-mailroom-automated-ingestion-environment-di.md
- Issues/Features/open/closed/FEAT-0154-optimize-git-merge-strategy-and-enhance-issue-clos.md
- Issues/Features/open/closed/FEAT-0155-重构-agent-调度架构-事件驱动-去链式化.md
- Issues/Features/open/closed/FEAT-0160-agentscheduler-abstraction-layer.md
- Issues/Features/open/closed/FEAT-0161-filesystem-event-automation-framework.md
- Issues/Features/open/closed/FEAT-0162-agent-collaboration-workflow.md
- Issues/Features/open/closed/FEAT-0163-在-issue-submit-运行过程中自动执行-sync-files.md
- Issues/Features/open/closed/FEAT-0164-refactor-unified-event-driven-architecture.md
- Issues/Features/open/closed/FEAT-0165-重构-memo-inbox-为信号队列模型-消费即销毁.md
- Issues/Features/open/closed/FEAT-0166-daemon-process-management-service-governance.md
- Issues/Features/open/closed/FEAT-0167-im-基础设施-核心数据模型与存储.md
- Issues/Features/open/closed/FEAT-0172-优化-issue-close-时的文件合并策略-直接覆盖主线-issue-ticket.md
- Issues/Features/open/closed/FEAT-0174-universal-hooks-core-models-and-parser.md
- Issues/Features/open/closed/FEAT-0175-universal-hooks-git-hooks-dispatcher.md
- Issues/Features/open/closed/FEAT-0176-universal-hooks-agent-hooks-with-acl.md
- Issues/Features/open/closed/FEAT-0178-add-debug-flag-to-monoco-sync-and-is_debug-to-hook.md
- Issues/Features/open/closed/FEAT-0179-治理与简化-skill-体系-role-workflow-融合与-jit-劝导.md
- Issues/Features/open/closed/FEAT-0181-implement-issue-lifecycle-hooks-adr-001.md
- Issues/Features/open/closed/FEAT-0182-细化-issue-生命周期钩子命名并完成逻辑卸载.md
- Issues/Features/open/closed/FEAT-0183-实现-post-issue-create-实时-lint-反馈机制.md
- Issues/Features/open/closed/FEAT-0184-document-principles-of-agentic-system.md
- Issues/Features/open/closed/FEAT-0185-doc-principles-of-agentic-system-05-glimpse-of-ada.md
- Issues/Features/open/closed/FEAT-0186-define-monoco-spike-directory-structure-and-articl.md
- Issues/Features/open/closed/FEAT-0187-govern-references-directory-structure-and-implemen.md
- Memos/2026-02-06_Mailbox_Protocol_Draft.md
- docs/Specs/mailbox-protocol-schema.md
- docs/examples/mailbox/draft_reply.yaml
- docs/examples/mailbox/inbound_email_thread.yaml
- docs/examples/mailbox/inbound_lark_group.yaml
- src/monoco/mailbox/__init__.py
- src/monoco/mailbox/constants.py
- src/monoco/mailbox/schema.py
- src/monoco/mailbox/validators.py
criticality: medium
solution: implemented
opened_at: '2026-02-06T21:10:53'
isolation:
  type: branch
  ref: FEAT-0189-定义-mailbox-协议存储格式与-schema-规范
  created_at: '2026-02-06T21:11:01'
---

## FEAT-0189: 定义 Mailbox 协议存储格式与 Schema 规范

建立一套标准化的、基于文件的 Mailbox 协议规范，作为 Courier 与 Monoco 内核的**受保护物理接口**。

- **保护设计**：`.monoco/mailbox/` 对 Agent 是只读或受限访问的。
- **发送机制**：Agent 在 Feature 分支的工作目录下撰写邮件草稿，通过 `monoco courier send` 命令将其原子化地投递至受保护的 `outbox`。
  重点解决：

1. **职责边界**：Courier 负责外部物流，CLI 负责投递校验，内核负责逻辑决策。
2. **安全隔离**：防止 Agent 误删或篡改 `mailbox` 中的原始历史记录（Facts）。
3. **统一建模**：如何在一个 Schema 中同时兼容 IM 和 Email 的数据结构。
4. **关系编排**：定义 Session, Thread 和 Correlation 的物理与逻辑关联方式。

## Acceptance Criteria

- [x] **多源兼容方案**：定义 `participants` 结构，支持 `from`, `to`, `cc`, `mentions` 的多态存储。
- [x] **Thread 关联逻辑**：定义 `session.id` (物理聚合) 与 `session.thread_key` (逻辑话题) 的协同机制。
- [x] **Schema 验证**：提供飞书和邮件的典型 YAML Frontmatter 示例。
- [x] **~Courier 能够将外部消息写入 `.monoco/mailbox/inbound/`~** (Moved to EPIC-0035)
- [x] **~Courier 能够将附件下载至 `.monoco/dropzone/` 并由 Mailroom 自动处理~** (Moved to EPIC-0035)

## Technical Tasks

- [x] **协议规约制定**
  - [x] 定义参与者对象的详细字段 (id, name, platform_id, email, role, avatar)。
  - [x] 定义 Mention 对象结构 (type, target, name, offset) 支持 IM @提及。
- [x] **逻辑关系建模**
  - [x] 详细描述 IM Thread (root_id/parent_id) 到 `session.thread_key` 的映射。
  - [x] 详细描述 Email Thread (In-Reply-To) 到 `session.thread_key` 的映射。
  - [x] 定义 Session 结构 (id, type, name, thread_key)。
- [x] **CLI 与投递机制设计**
  - [x] 设计 `monoco courier send <file>` 命令的入参规范与校验逻辑。
  - [x] 定义 Agent 工作目录下草稿文件的存储位置建议（`Issues/Features/work/FEAT-XXXX/drafts/`）。
  - [x] 定义投递流程 (草稿 -> 校验 -> outbound -> Courier -> archive)。
- [x] **工程化适配准备**
  - [x] 设计 `correlation_id` 的生成规则与消费逻辑。
  - [x] 提供完整的 JSON Schema 定义。

## 设计成果摘要

### Participants 多源兼容结构

```yaml
participants:
  from:          # 发送者 (Participant)
    id: string
    name: string
    email: string?        # Email 必需
    platform_id: string?  # IM 平台标识
    role: enum            # owner | admin | member | guest | external
    avatar: string?
  to: Participant[]        # 主收件人
  cc: Participant[]        # 抄送 (Email)
  bcc: Participant[]       # 密送 (Email)
  mentions:                # @提及 (IM)
    - type: enum          # user | all | channel | role
      target: string
      name: string
      offset: integer
```

### Thread 映射逻辑

| 概念 | Lark/IM | Email |
|------|---------|-------|
| 物理聚合 | `session.id` = chat_id | `session.id` = thread hash |
| 逻辑话题 | `session.thread_key` = root_msg_id | `session.thread_key` = Thread-Topic |
| 回复目标 | `reply_to` = parent_msg_id | `reply_to` = In-Reply-To |
| 话题根 | `thread_root` = root_msg_id | `thread_root` = Root Message-ID |

### CLI 发送契约

```bash
monoco courier send <draft-file> [--dry-run] [--provider <name>]
```

- Agent 在 `Issues/Features/work/FEAT-XXXX/drafts/` 创建草稿
- CLI 执行格式校验 → 原子移动至 `outbound/{provider}/`
- Courier 监听并发送 → 成功移至 `archive/`

### Correlation ID 规则

```
{category}_{entity_id}_{timestamp}
```

用于跨消息追踪业务闭环 (bug → 分析 → 修复 → 通知)。

## Review Comments

- **2026-02-06 (Initial Design)**: 由 IndenScale 提出，决定将具体存储格式讨论从 EPIC 下推至此 FEAT。
- **2026-02-06 (Schema Complete)**: 完成 Mailbox Protocol Schema v1.0.0 定义，包含完整字段规范、Provider 示例、JSON Schema。
