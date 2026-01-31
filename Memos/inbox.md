# Monoco Memos Inbox

## [5cec77] 2026-01-30 17:17:25
- **Status**: [ ] Pending

关于 Agent Hooks 的架构决策：1. 各 CLI 工具的 Agent Hooks 是私有特性，生态碎片化严重；2. Git Hooks 上下文不匹配，无法满足 Session 级别的清理需求；3. 必需设计 Monoco Native Hook System 以实现统一的生命周期管理。

## [ff8dc3] 2026-01-30 17:40:45
- **Status**: [ ] Pending

> **Context**: `scheduler-flow-skills`

架构设计假设突破：单一 Skill 模式 vs Flow Skills 多目录模式

## [e81dd0] 2026-01-30 17:40:47
- **Status**: [ ] Pending

> **Context**: `scheduler-refactor`

重构需求：Feature 资源目录结构需要支持多 Skill 类型（标准 Skill + Flow Skills）

## [fb30c2] 2026-01-30 17:40:49
- **Status**: [ ] Pending

> **Context**: `scheduler-conflict`

当前冲突：SkillManager 假设 resources/{lang}/SKILL.md，但 Flow Skills 需要 resources/skills/flow_*/SKILL.md

## [83b536] 2026-01-30 17:40:51
- **Status**: [ ] Pending

> **Context**: `scheduler-consensus`

原子共识：需要重构 SkillManager 或创建 FlowSkillManager 来支持多 Skill 目录注入

## [b4b49d] 2026-01-30 17:41:59
- **Status**: [ ] Pending

> **Context**: `skillmanager-enhancement`

原子共识：SkillManager 需要增强以支持 Feature 级别的多 Skill 细分（如 i18n 可分为 github-spike, archive-spike 等）

## [b03194] 2026-01-30 17:42:01
- **Status**: [ ] Pending

> **Context**: `skill-architecture`

设计原则：1 Feature : N Skills，而非 1 Feature : 1 Skill。Skill 是原子能力单元，Feature 是业务领域聚合

## [5f379d] 2026-01-30 17:42:03
- **Status**: [ ] Pending

> **Context**: `skill-directory-structure`

目录结构新规范：resources/skills/{skill-name}/SKILL.md 支持多 Skill，保留 resources/{lang}/SKILL.md 作为默认 Skill 兼容

## [90bb4e] 2026-01-30 17:42:57
- **Status**: [ ] Pending

> **Context**: `skill-pattern-analysis`

分析：i18n/spike/memo/issue 当前是 Command Reference 模式（是什么），而非 Flow Skill 模式（怎么做）

## [6b8ae7] 2026-01-30 17:42:59
- **Status**: [ ] Pending

> **Context**: `i18n-flow-potential`

i18n 适合 Flow Skill：翻译工作流应有状态机 (Scan -> Translate -> Verify -> Sync)

## [19b9fd] 2026-01-30 17:43:01
- **Status**: [ ] Pending

> **Context**: `spike-flow-potential`

spike 适合 Flow Skill：研究流程应有状态机 (Add -> Sync -> Analyze -> Extract -> Archive)

## [138d0f] 2026-01-30 17:43:11
- **Status**: [ ] Pending

> **Context**: `issue-flow-potential`

issue 适合 Flow Skill：Issue 生命周期本身就是状态机 (Open -> Start -> Develop -> Submit -> Review -> Close)

## [8c39de] 2026-01-30 17:43:14
- **Status**: [ ] Pending

> **Context**: `dual-mode-consensus`

原子共识：所有 Feature 都应支持双模式 - Command Reference (AGENTS.md) + Flow Skills (skills/*/)，前者是手册，后者是 SOP

## [0f4c20] 2026-01-30 17:46:42
- **Status**: [ ] Pending

> **Context**: `issue-tracking`

Issue FEAT-0122 已创建: Enhance SkillManager to Support Multi-Skill Architecture (AgentOnboarding)

## [c8f858] 2026-01-30 17:46:43
- **Status**: [ ] Pending

> **Context**: `issue-tracking`

Issue FEAT-0123 已创建: Migrate Core Features to Flow Skills Pattern (Guardrail), 依赖 FEAT-0122

## [e0a602] 2026-01-30 17:48:09
- **Status**: [ ] Pending

> **Context**: `docs-debt`

FEAT-0120 剩余文档任务转移至文档专项：Hook System 使用文档、自定义 Hook 开发指南

## [de8156] 2026-01-30 17:48:24
- **Status**: [ ] Pending

> **Context**: `issue-closed`

FEAT-0120 已关闭 (implemented)：Agent Session Lifecycle Hooks 功能完成，文档债务已记录

## [478b7b] 2026-01-30 17:49:15
- **Status**: [ ] Pending

> **Context**: `naming-analysis`

分析：scheduler 模块命名与其实际职责不匹配 - CLI 命令是 agent，但模块名是 scheduler

## [f3cb0a] 2026-01-30 17:52:40
- **Status**: [ ] Pending

> **Context**: `issue-tracking`

CHORE-0023 已创建：Rename scheduler module to agent for semantic consistency (AgentOnboarding)

## [23ef5f] 2026-01-30 17:59:23
- **Status**: [ ] Pending

> **Context**: `task-completed`

CHORE-0023 验收通过：scheduler → agent 重命名完成，FEAT-0122 已更新路径引用

## [b6fb7a] 2026-01-30 18:10:36
- **Status**: [ ] Pending

> **Context**: `task-completed`

FEAT-0123 已完成：所有核心 Feature 已迁移到 Flow Skills 模式 (7个 Flow Skills)

## [3cf012] 2026-01-30 18:13:09
- **Status**: [ ] Pending

> **Context**: `skill-architecture-analysis`

分析：传统 Skills (monoco_i18n, monoco_issue 等) 与 Flow Skills 的职责对比

## [0b15f1] 2026-01-31 17:47:54
- **Status**: [ ] Pending

增强 i18n 检查: 支持 Block 级别的语言检测，避免在混合语言 Markdown（如中文 Issue 中的英文 Review Comments）中出现误报。

## [6f50db] 2026-01-31 18:16:52
- **Status**: [ ] Pending

ACP 调查结论：

**ACP 是什么**
- Agent Client Protocol (ACP) 是一个开放标准，类似于 LSP (Language Server Protocol)
- 目的：标准化 AI Agent 与代码编辑器/IDE 之间的通信协议
- 通信方式：JSON-RPC over stdio (本地) 或 HTTP/WebSocket (远程)
- 由 Zed 等编辑器推动，目标是解决 Agent-Editor 集成的碎片化问题

**Kimi CLI 的 ACP 支持**
- Kimi CLI 完全支持 ACP，通过 'kimi acp' 命令启动 ACP 服务器
- 可以作为后端 Agent 被 Zed、JetBrains 等 ACP 兼容的编辑器调用
- 这是 Agent-to-Editor 的协议，不是 Agent-to-Agent 的协议

**当前 Monoco Agent 模块架构**
- 使用 EngineAdapter 模式，通过 CLI 命令行直接调用各个 Agent (gemini, claude, kimi, qwen)
- Worker 通过 subprocess.Popen 启动 Agent 进程，传递 prompt
- 当前是 'Monoco 调用 Agent CLI' 的单向模式

**是否应该使用 ACP 接入 Kimi CLI？**

**不应该**。原因如下：

1. **架构不匹配**：ACP 是为 'Editor 调用 Agent' 设计的，而 Monoco 的需求是 'Orchestrator 调用 Agent'
2. **复杂度增加**：引入 ACP 需要启动 ACP 服务器、实现 JSON-RPC 客户端，远比当前的 CLI 调用复杂
3. **功能冗余**：Kimi CLI 的 '-p prompt --print' 模式已经满足 Monoco 的需求（非交互式、自动执行）
4. **维护成本**：需要适配 ACP 协议的变化，而 CLI 接口更稳定
5. **通用性降低**：其他 Agent (gemini, claude) 可能不支持 ACP，会导致架构不一致

**建议**
- 保持当前的 EngineAdapter + CLI 调用模式
- 如果未来需要 'Editor 调用 Monoco'，可以考虑让 Monoco 本身实现 ACP Server
- ACP 更适合作为 Monoco 的 **北向接口** (暴露给 IDE)，而非 **南向接口** (调用底层 Agent)

## [20cac7] 2026-01-31 20:17:43
- **Status**: [ ] Pending

> **Context**: `issue-system`

强化 monoco issue lint：检测非法 status 值和目录不匹配

问题发现：
1. FEAT-0129 使用了非法 status: done（应为 open/closed）
2. 存在非法目录 Issues/Features/done/（应为 open/closed/backlog）
3. FEAT-0129 文件在 done/ 目录但 status 也写错
4. linter 没有检测出这些问题

需要增加的检查规则：
- status 必须是 enum: [open, closed, backlog]
- 文件所在目录必须与 status 匹配
- stage 必须是 enum: [draft, doing, review, done]
- 检查非法目录名

## [5031cb] 2026-01-31 20:22:03
- **Status**: [ ] Pending

> **Context**: `issue-system`

Git Commit Hooks 需求分析

问题背景：
FEAT-0128/0129 被关闭时缺少必需的 solution 字段，导致：
1. linter 解析失败，Issue 未被加入索引
2. FEAT-0130 的依赖检查出现虚警
3. 需要手动修复 closed issue

根本原因：
缺少 pre-commit hook 在提交前验证 Issue 格式合规性

Git Hooks 需求：
1. pre-commit: 运行 monoco issue lint，阻止不合规提交
2. pre-push: 检查是否有未完成的关键 Issue
3. post-checkout: 自动同步 issue 状态到工作区

monoco sync 扩展建议：
- : 安装/更新 git hooks
- 支持 hooks 模板自定义
- 与现有 skill 分发机制集成

相关文件：
- .git/hooks/pre-commit (需要创建)
- monoco/features/issue/linter.py (已有)
- monoco/features/sync/commands.py (扩展)

优先级：medium
影响：防止不合规 Issue 进入仓库

## [4d19e0] 2026-01-31 22:19:10
- **Status**: [ ] Pending

> **Context**: `kimi-cli research`

kimi-cli hooks系统调研：社区Issue #785已提出User-Configurable Lifecycle Hooks System需求，官方暂无计划但可通过Wire模式实现。Wire模式是kimi-cli的headless运行方式，通过JSON-RPC 2.0 over stdin/stdout与外部程序双向通信，支持监听TurnBegin/StepBegin/ToolCall/TurnEnd等生命周期事件。与Claude Code hooks的区别：kimi-cli需外部包装器实现，非内置配置。参考：docs/en/customization/wire-mode.md

## [8bcfc1] 2026-01-31 22:19:17
- **Status**: [ ] Pending

> **Context**: `kimi-cli tech`

kimi-cli Wire模式事件类型：TurnBegin(用户输入开始), TurnEnd(2026-01-26新增), StepBegin(步骤开始), StepInterrupted(步骤中断), CompactionBegin/End(上下文压缩), StatusUpdate(状态更新含token使用), ContentPart(AI输出), ToolCall/ToolResult(工具调用), ApprovalRequest(需响应), SubagentEvent(子代理事件)。基于这些事件可实现pre/post hooks

## [56842d] 2026-01-31 22:19:18
- **Status**: [ ] Pending

> **Context**: `kimi-cli concept`

kimi-cli Agent Flow vs Hooks区别：Agent Flow通过/flow:name执行Mermaid/D2流程图，每步需AI参与消耗token；Hooks是事件触发的确定性脚本，零token开销。官方推荐Agent Flow替代Hooks，但社区认为两者适用场景不同

## [0eb28f] 2026-02-01 00:59:22
- **Type**: feature
- **Status**: [x] Resolved
- **Ref**: FEAT-0131
- **Context**: ```test/file:10```

测试反馈：Memo增强功能测试
