---
id: FEAT-0181
uid: 806e54
type: feature
status: open
stage: draft
title: Implement Issue Lifecycle Hooks (ADR-001)
created_at: '2026-02-05T08:58:16'
updated_at: '2026-02-05T09:04:10'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0181'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Features/open/FEAT-0180-issue-lifecycle-hooks-pre-post-command-validation.md
- docs/zh/98_ADRs/ADR-001-issue-lifecycle-hooks.md
- docs/zh/98_ADRs/ADR-002-lint-error-collection-strategy.md
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-05T08:58:16'
isolation: null
---

## FEAT-0181: Implement Issue Lifecycle Hooks (ADR-001)

## Objective
根据 ADR-001 实现 Monoco Issue 的生命周期钩子系统。该系统的核心价值在于：
1. **统一治理**：无论是 CLI 直接调用还是 Agent 触发，都遵循相同的准入（pre）和准出（post）规则。
2. **逻辑解耦**：将分支上下文检查、Working Tree 状态验证、Lint 调用等非核心业务逻辑从 Issue 命令实现中抽离。
3. **闭环反馈**：向 Agent 提供结构化的 Hook 失败建议（Suggestions），引导其自动修复问题。
4. **命名对齐**：**强制要求**内部所有钩子事件命名严格遵循 Monoco ACL 统一协议中的 `pre/post` 规范（参考 `acl_unified_protocol_ZH.md`）。

## Acceptance Criteria
- [ ] **命名一致性**：核心实现必须通过 `NamingACL` 映射逻辑，确保内部消费的事件主语（Session, Agent, Subagent, Tool, Issue）与 `pre/post` 动作严格对称，严禁在内部逻辑中直接透传 Agent 原生命名（如 `SessionStart`）。
- [ ] **领域模型**：在 `monoco.core.issue` 中实现 `IssueEvent`, `HookDecision` 和 `IssueHookResult` 数据结构。
- [ ] **核心分发器**：实现 `IssueHookDispatcher` 类，支持：
    - 加载内置 Hooks (位于 `monoco/hooks/issue/`)
    - 发现用户自定义 Hooks (位于 `.monoco/hooks/issue/`)
    - 支持同步执行，并能根据 `deny` 决策阻断流程。
- [ ] **CLI 集成**：重构 `commands.py` 中的 `start`, `submit`, `close` 方法，注入生命周期事件。
- [ ] **Agent 桥接**：实现 `AgentToolAdapter`，能够拦截 `issue` 子命令，并在执行前注入钩子逻辑。
- [ ] **开发者体验**：
    - 实现 `monoco issue --no-hooks` 跳过钩子。
    - 实现 `monoco issue --debug-hooks` 展示钩子执行详情（名称、耗时、结果）。
- [ ] **内置 Hooks 落地**：
    - `pre-submit`: 自动执行 `sync-files` 检查及 `lint` 校验。
    - `post-start`: 初始化 Feature 分支并设置本地隔离环境（Isolation）。

## Technical Tasks

- [ ] **Phase 1: 协议与模型定义**
    - [ ] 设计 `IssueHookContext` 模型，包含执行环境、用户信息及目标 Issue 状态。
    - [ ] 在 `monoco/models/issue.py` 中定义枚举与 Pydantic 模型。
- [ ] **Phase 2: 基础设施逻辑**
    - [ ] 实现钩子查找路径管理（Built-in vs Local）。
    - [ ] 实现脚本执行器（支持 Python 原生、Shell 脚本及 Python 动态加载）。
    - [ ] 编写 `IssueHookDispatcher` 的单元测试。
- [ ] **Phase 3: CLI 与 Agent 适配器**
    - [ ] 修改 `click` 命令装饰器或核心调用链路，注入 Hooks。
    - [ ] 实现 `NamingACL` 映射逻辑，统一 `pre/post` 规范并适配 Claude/Gemini native events。
    - [ ] 针对 `AgentToolAdapter` 设计 Mock 测试，验证 Suggestions 注入。
- [ ] **Phase 4: 内置 Hooks 迁移**
    - [ ] 将现有 `submit` 中的 Lint 逻辑迁移至 `pre-submit` 钩子。
    - [ ] 将现有的 `start` 分支创建逻辑迁移至 `pre-start` 或 `post-start` 钩子。
- [ ] **Phase 5: 交付与文档**
    - [ ] 更新 `GEMINI.md` 中的工作流指南。
    - [ ] 编写 `docs/zh/40_hooks/issue_hooks.md` 开发者指南。

## Review Comments


