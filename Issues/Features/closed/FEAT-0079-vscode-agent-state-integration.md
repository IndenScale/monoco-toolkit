---
id: FEAT-0079
type: feature
status: closed
stage: done
title: VS Code 扩展与 Agent 状态的集成
created_at: "2026-01-15T23:19:38"
updated_at: "2026-01-15T23:19:44"
closed_at: "2026-01-15T23:19:44"
parent: EPIC-0014
solution: implemented
dependencies: []
related: []
tags: []
priority: Medium
author: Monoco
---

## FEAT-0079: VS Code 扩展与 Agent 状态的集成

# Feature: VS Code 扩展与 Agent 状态的集成

## 目标 (Objective)

使 Monoco VS Code 扩展能够感知本地 Agent CLI 的可用性。通过读取 Toolkit 管理的共享文件 `agent_state.yaml` 来实现。

## 背景 (Context)

Toolkit 已经实现了 Agent 执行层 (`monoco.core.agent`)，它通过 `monoco doctor`（以及 `check_agents.sh`）诊断工具可用性，并将结果持久化到 `~/.monoco/agent_state.yaml`。

目前的 VS Code 扩展对这个状态是不可见的，这意味着它无法根据用户是否安装了 `claude` 或 `gemini` 来智能地隐藏/显示 Agent 相关功能（如 "Refine Issue" CodeLens）。

## 策略 (Strategy)

1. **被动读取 (Passive Read)**: 扩展 **不要** 直接调用 shell 脚本（以避免性能问题和权限问题）。它应严格读取 `~/.monoco/agent_state.yaml`。
2. **优雅降级 (Graceful Degredation)**: 如果文件缺失或所有 agent 均不可用，Agent 相关的 UI 元素应隐藏或禁用，并显示 Tooltip 提示 "运行 'monoco doctor' 以启用"。
3. **文件监听 (File Watcher)**: 监听 `~/.monoco/agent_state.yaml` 的变更，以便在用户于终端运行 `monoco doctor` 时立即作出反应。

## 详细设计 (Detailed Design)

### 1. 状态服务 (State Service)

用 TypeScript 实现 `AgentStateService`:

```typescript
interface AgentState {
  last_checked: string;
  providers: Record<str, { available: boolean; path?: string }>;
}

class AgentStateService {
  private state: AgentState | undefined;

  constructor() {
    this.watchStateFile(); // 使用 chokidar 或 vscode.FileSystemWatcher
  }

  isAvailable(provider: string): boolean {
    return this.state?.providers[provider]?.available ?? false;
  }
}
```

### 2. 上下文键 (Context Keys)

设置 VS Code Context Keys 供 `package.json` 菜单使用:

- `monoco:agentAvailable`: 如果任一 provider 可用则为 true。
- `monoco:geminiAvailable`: 如果 gemini 可用则为 true。
- `monoco:claudeAvailable`: 如果 claude 可用则为 true。

### 3. UI 提示 (UI Hints)

如果用户尝试运行 Agent 命令但 `agentAvailable` 为 false，显示 toast 提示:
"Agent 环境未就绪。请在终端运行 `monoco doctor`。"

## Acceptance Criteria

- [x] 扩展在启动时读取 `~/.monoco/agent_state.yaml`。
- [x] 扩展正确设置 `monoco:agentAvailable` context key。
- [x] 如果 YAML 文件发生变化（例如用户运行了 `monoco doctor`），扩展自动更新状态。

## Technical Tasks

- [x] Implement `AgentStateService` in VS Code extension.
- [x] Set context keys for agent availability.
- [x] Implement file watcher for `agent_state.yaml`.

## Review Comments

- [x] Self-Review
