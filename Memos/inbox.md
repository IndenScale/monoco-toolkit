# Monoco Memos Inbox

## [5cec77] 2026-01-30 17:17:25
关于 Agent Hooks 的架构决策：1. 各 CLI 工具的 Agent Hooks 是私有特性，生态碎片化严重；2. Git Hooks 上下文不匹配，无法满足 Session 级别的清理需求；3. 必需设计 Monoco Native Hook System 以实现统一的生命周期管理。

## [ff8dc3] 2026-01-30 17:40:45
> **Context**: `scheduler-flow-skills`

架构设计假设突破：单一 Skill 模式 vs Flow Skills 多目录模式

## [e81dd0] 2026-01-30 17:40:47
> **Context**: `scheduler-refactor`

重构需求：Feature 资源目录结构需要支持多 Skill 类型（标准 Skill + Flow Skills）

## [fb30c2] 2026-01-30 17:40:49
> **Context**: `scheduler-conflict`

当前冲突：SkillManager 假设 resources/{lang}/SKILL.md，但 Flow Skills 需要 resources/skills/flow_*/SKILL.md

## [83b536] 2026-01-30 17:40:51
> **Context**: `scheduler-consensus`

原子共识：需要重构 SkillManager 或创建 FlowSkillManager 来支持多 Skill 目录注入

## [b4b49d] 2026-01-30 17:41:59
> **Context**: `skillmanager-enhancement`

原子共识：SkillManager 需要增强以支持 Feature 级别的多 Skill 细分（如 i18n 可分为 github-spike, archive-spike 等）

## [b03194] 2026-01-30 17:42:01
> **Context**: `skill-architecture`

设计原则：1 Feature : N Skills，而非 1 Feature : 1 Skill。Skill 是原子能力单元，Feature 是业务领域聚合

## [5f379d] 2026-01-30 17:42:03
> **Context**: `skill-directory-structure`

目录结构新规范：resources/skills/{skill-name}/SKILL.md 支持多 Skill，保留 resources/{lang}/SKILL.md 作为默认 Skill 兼容

## [90bb4e] 2026-01-30 17:42:57
> **Context**: `skill-pattern-analysis`

分析：i18n/spike/memo/issue 当前是 Command Reference 模式（是什么），而非 Flow Skill 模式（怎么做）

## [6b8ae7] 2026-01-30 17:42:59
> **Context**: `i18n-flow-potential`

i18n 适合 Flow Skill：翻译工作流应有状态机 (Scan -> Translate -> Verify -> Sync)

## [19b9fd] 2026-01-30 17:43:01
> **Context**: `spike-flow-potential`

spike 适合 Flow Skill：研究流程应有状态机 (Add -> Sync -> Analyze -> Extract -> Archive)

## [138d0f] 2026-01-30 17:43:11
> **Context**: `issue-flow-potential`

issue 适合 Flow Skill：Issue 生命周期本身就是状态机 (Open -> Start -> Develop -> Submit -> Review -> Close)

## [8c39de] 2026-01-30 17:43:14
> **Context**: `dual-mode-consensus`

原子共识：所有 Feature 都应支持双模式 - Command Reference (AGENTS.md) + Flow Skills (skills/*/)，前者是手册，后者是 SOP

## [0f4c20] 2026-01-30 17:46:42
> **Context**: `issue-tracking`

Issue FEAT-0122 已创建: Enhance SkillManager to Support Multi-Skill Architecture (AgentOnboarding)

## [c8f858] 2026-01-30 17:46:43
> **Context**: `issue-tracking`

Issue FEAT-0123 已创建: Migrate Core Features to Flow Skills Pattern (Guardrail), 依赖 FEAT-0122

## [e0a602] 2026-01-30 17:48:09
> **Context**: `docs-debt`

FEAT-0120 剩余文档任务转移至文档专项：Hook System 使用文档、自定义 Hook 开发指南

## [de8156] 2026-01-30 17:48:24
> **Context**: `issue-closed`

FEAT-0120 已关闭 (implemented)：Agent Session Lifecycle Hooks 功能完成，文档债务已记录

## [478b7b] 2026-01-30 17:49:15
> **Context**: `naming-analysis`

分析：scheduler 模块命名与其实际职责不匹配 - CLI 命令是 agent，但模块名是 scheduler

## [f3cb0a] 2026-01-30 17:52:40
> **Context**: `issue-tracking`

CHORE-0023 已创建：Rename scheduler module to agent for semantic consistency (AgentOnboarding)
