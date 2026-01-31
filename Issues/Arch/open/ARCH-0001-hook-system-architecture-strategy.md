---
id: ARCH-0001
uid: 2edc85
type: arch
status: open
stage: doing
title: Hook System Architecture Strategy
created_at: '2026-01-31T10:38:10'
updated_at: '2026-01-31T10:51:41'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#ARCH-0001'
- '#EPIC-0000'
files: []
criticality: medium
opened_at: '2026-01-31T10:38:10'
---

## ARCH-0001: Hook System Architecture Strategy

## Context
Monoco Toolkit 需要一个扩展机制来处理生命周期事件。目前存在两种不同的 "Hook" 概念：
1. **Session Hooks (`monoco.core.hooks`)**: 在 Python 进程内运行，管理 Agent Session 的生命周期（如 `start`, `terminate`）。具备丰富的上下文感知能力。
2. **Git Hooks (`monoco.core.githooks`)**: 作为 Shell 脚本安装在 `.git/hooks`，由 Git 进程触发。用于代码质量控制。

## Problem
我们需要实现 **Issue Lifecycle Automation**（例如：Issue 状态变为 `doing` 时自动启动 Agent，提交时自动运行 Reviewer）。
现有的 Session Hooks 作用域局限于 Session 内部，无法感知或控制 Issue 状态的流转。而 Git Hooks 仅在 Git 操作时触发，无法与 Monoco 的业务逻辑（如 Agent Roles）联动。

## Options Considered

### Option 1: 扩展 Session Hooks
将 Issue 事件注入到 Session Hooks 中。
- **Pros**: 复用现有架构。
- **Cons**: 作用域错误。Session Hook 是 Session 的子集，Issue Hook 应该是 Session 的超集（Issue 包含 Session）。

### Option 2: 独立的 Event Bus
引入一个全局事件总线，监听所有 Monoco 事件。
- **Pros**: 极其灵活，解耦。
- **Cons**: 对于目前的单体 CLI 来说过度工程化。

### Option 3: Workflow Triggers / Post Actions (Selected)
利用状态机 (`state machine`) 的特性，在 `workspace.yaml` 的 `workflows` 定义中直接配置 `post_actions`。
- **Pros**:
    - **Contextual**: 动作与状态转换直接绑定，逻辑清晰（"Start" -> "Run Agent"）。
    - **Config-Driven**: 用户可以在 `workspace.yaml` 中直观配置。
    - **Low Overhead**: 不需要新的守护进程或复杂的事件系统。

## Decision
1. **明确职责边界**:
    - **Session Hooks**: 负责 **Runtime Environment** 管理（如 Git 分支清理、Docker 容器启停）。属于 Infrastructure 层。
    - **Git Hooks**: 负责 **Code Quality** 拦截（Lint, Commit Message Check）。属于 External Tooling 层。
    - **Workflow Triggers**: 负责 **Business Process** 自动化（如 Agent 编排）。属于 Application 层。

2. **技术路线 (FEAT-0124)**:
    - 采用 **Option 3**。
    - 在 `TransitionConfig` 中增加 `post_actions` 字段。
    - 实现命令模板替换（如 `monoco agent run --issue {id}`）。

3. **默认策略**:
    - **GitCleanupHook**: 采用“保守默认”策略。默认开启 `switch_to_main`，默认关闭 `delete_branch`。安全第一。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
