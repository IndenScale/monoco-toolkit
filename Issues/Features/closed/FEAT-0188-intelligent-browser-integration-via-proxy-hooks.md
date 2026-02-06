---
id: FEAT-0188
uid: d47ccf
type: feature
status: closed
stage: done
title: Intelligent Browser Integration via Proxy Hooks
created_at: '2026-02-06T17:16:01'
updated_at: 2026-02-06 17:32:59
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0188'
files:
- .monoco/roles/engineer.yaml
- .monoco/roles/principal.yaml
- .monoco/roles/reviewer.yaml
- Issues/Chores/closed/CHORE-0046-架构重构-agent-session-职责拆分与生命周期管理.md
- Issues/Chores/closed/CHORE-0047-角色重命名-收缩为三角色模型-principal-engineer-reviewer.md
- Issues/Chores/open/CHORE-0043-重构-open-和-close-命令以支持完整的生命周期钩子.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
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
- src/monoco/features/browser/adapter.py
- src/monoco/features/browser/resources/hooks/browser_availability.sh
- src/monoco/features/browser/resources/hooks/browser_cleanup.sh
- src/monoco/features/issue/linter.py
criticality: medium
solution: implemented
opened_at: '2026-02-06T17:16:01'
closed_at: '2026-02-06T17:32:58'
---

## FEAT-0188: Intelligent Browser Integration via Proxy Hooks

## Objective
将 `agent-browser` 深度整合进 Monoco 体系。通过 Monoco 强大的 Universal Hooks 系统，为 Agent 提供一套具备“自我解释能力”和“环境自愈能力”的智能浏览器插件。

核心价值：
- **消除冷启动**：自动识别 URL 并预热浏览器，减少 Agent 试错。
- **按需引导**：在 Session 初期提供操作指南，在熟练期保持上下文清爽。
- **工程化分发**：通过 `monoco sync` 自动配置 Hook，实现“一键可用”。

## Acceptance Criteria
- [x] 在 `src/monoco/features/browser` 中建立完整的 Feature 结构。
- [x] 实现具备 Front Matter 的 Hook 脚本，支持 `monoco hook scan` 识别。
- [x] Hook 支持 Availability Check：未安装工具时主动报错并引导安装。
- [x] Hook 支持 Session-Counter：记录会话内调用次数，实现智能帮助注入（1, 16... 次触发）。
- [x] Hook 支持 SessionEnd 清理：自动移除 /tmp 下的计数状态文件。
- [x] `monoco sync` 能够自动将 Hook 注册到 `.claude/settings.json-managed` 区域。

## Technical Tasks
- [x] **Feature 初始化**
  - [x] 创建 `src/monoco/features/browser` 目录及 `adapter.py`。
  - [x] 定义 `browser` feature 的元数据及集成逻辑。
- [x] **Hook 逻辑实现**
  - [x] 编写 `resources/hooks/browser_helper.sh`。
  - [x] 添加 Front Matter 元数据（type: agent, provider: claude-code, event: ...）。
  - [x] 实现计数器、URL 预热及清理逻辑。
- [x] **清理旧配置**
  - [x] 移除手动修改的 `.claude/settings.json` 和 `.claude/hooks` 临时文件。
- [x] **验证与提测**
  - [x] 运行 `monoco sync` 验证钩子自动分发。
  - [x] 验证 `SessionEnd` 是否触发清理。

## Review Comments
- 已经完成 `agent-browser` 的深度集成。
- 通过 `resources/hooks` 实现了智能引导。
- 经过 `monoco sync` 验证，Hooks 自动下发逻辑工作正常。
