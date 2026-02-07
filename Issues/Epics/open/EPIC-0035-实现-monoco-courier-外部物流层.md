---
id: EPIC-0035
uid: 0d92ab
type: epic
status: open
stage: doing
title: 实现 Monoco Courier：外部物流层
created_at: '2026-02-06T20:30:10'
updated_at: '2026-02-06T21:10:00'
parent: EPIC-0033
dependencies: []
related:
- FEAT-0189
domains:
- CollaborationBus
- AgentEmpowerment
tags:
- '#Courier'
- '#EPIC-0033'
- '#EPIC-0035'
- '#FEAT-0189'
files:
- Memos/2026-02-06_Mailbox_Protocol_Draft.md
- Issues/Features/open/FEAT-0189-定义-mailbox-协议存储格式与-schema-规范.md
criticality: high
solution: null
opened_at: '2026-02-06T20:30:10'
progress: 0/1
files_count: 0
---

## EPIC-0035: 实现 Monoco Courier：外部物流层

## 目标 (Objective)

建立 `Monoco Courier` 作为 Monoco 环境与外部世界（IM、邮件等）之间的“信号适配器”。采用 Sidecar 模式，确保内核精简的同时，提供强大的外部连接能力。Courier 将处理外部信号（Signals）的输入转化和内部事件（Events）的外部推送。

## 验收标准 (Acceptance Criteria)

- [ ] 定义通用的 Courier 适配器架构协议。
- [ ] 实现针对“飞书 (Lark)”的首个生产级适配器。
- [ ] Courier 能够将外部消息写入 `.monoco/mailbox/{source}/inbound/`。
- [ ] Courier 能够将附件下载至 `.monoco/dropzone/` 并由 Mailroom 自动处理。
- [ ] Courier 能够订阅 Monoco SSE 事件并实时推送至 IM（卡片消息）。
- [ ] 支持 Workspace-Local 配置隔离，每个项目拥有独立的 Token 和回调地址。

## 技术任务 (Technical Tasks)

- [ ] **基础架构设计**
  - [x] 定义 Mailbox 协议存储格式与 Schema 规范。
  - [ ] 定义受保护的 Mailbox 目录结构与权限模型。
  - [ ] 实现 `monoco courier send` 投递命令。
  - [ ] 定义 Courier 与 Daemon (Serve) 之间的交互契约 (REST + SSE)。
  - [ ] 设计通用的适配器基类，支持插件式扩展（IM、Email）。
- [ ] **侧车启动与管理机制**
  - [ ] 实现 `monoco serve --with-courier` 或独立启动脚本。
  - [ ] 定义 `.monoco/config/courier.yaml` 配置规范。
- [ ] **飞书适配器实现 (Lark Adapter)**
  - [ ] 集成飞书 Open API / SDK。
  - [ ] 实现 Webhook 回调接收与鉴权。
  - [ ] 实现文件下载并写入 `dropzone`。
  - [ ] 实现 SSE 事件监听与飞书卡片消息构造。
- [ ] **集成测试与文档**
  - [ ] 验证端到端的“消息 -> Memo -> Issue”链路。
  - [ ] 编写 `Courier` 部署与配置手册。

## Review Comments

- **2026-02-06 (Design Conclusion)**: 确认采用 Maildir 模式 + Courier 侧防抖 (Scheme A)。
- **Mirrored Structure**: `inbound/`, `outbound/`, `archive/` 均按 `provider` 分二级目录。
- **YAML Modeling**: 发件/抄送/单聊/群聊等复杂元数据封锁在 YAML 中，不在物理目录展现。
- **Debouncing**: IM 默认 30s 窗口，Email 0s。
- **Protocol**: Markdown + YAML Frontmatter, 核心标识符为 `session.id`。

---

**IndenScale，EPIC 状态已更新，设计方案已合拢。**
