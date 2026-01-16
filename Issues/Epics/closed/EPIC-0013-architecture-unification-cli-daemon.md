---
id: EPIC-0013
uid: e13a2d
type: epic
status: closed
stage: Done
progress: 2/2
title: "Architecture Unification: CLI & Daemon"
created_at: "2026-01-15T16:45:00"
opened_at: "2026-01-15T16:45:00"
updated_at: "2026-01-15T18:30:00"
closed_at: "2026-01-15T18:30:00"
solution: implemented
---

## EPIC-0013: Architecture Unification: CLI & Daemon

## 目标 (Objective)

通过引入统一的核心 Primitives (Workspace, Project, State)，消除 Monoco CLI 和 Monoco Daemon 之间的行为差异，确保“文件即协议”的严格执行。

## 核心交付点 (Key Results)

1. **统一的项目发现逻辑**：CLI 和 Daemon 使用同一套代码识别 Project 和 Workspace。
2. **统一的状态持久化**：所有的持久化状态（如上次活动项目）存储在 `.monoco/state.json`。
3. **插件 Proxy 化**：VS Code 插件彻底移除逻辑计算，仅作为 Daemon 的展示层。

## 工作包 (Work Packages)

### 1. 物理协议形式化 [DONE]

- [x] **Config Schema**：统一使用 `MonocoConfig` Pydantic 模型。
- [x] **Issue Schema**：统一使用 `IssueMetadata` Pydantic 模型。
- [x] **State Schema**：实现 `monoco.core.state.WorkspaceState`。

### 2. 核心架构对齐 [DONE]

- [x] **项目抽象 (Project Primitive)**：统一 `MonocoProject` 和 `Workspace` 管理。
- [x] **服务解耦 (Service Decoupling)**：Monitor (Watchdog) 逻辑从 Daemon 上帝类中剥离，沉淀到 core/feature。

### 3. 命令行为一致性 [DONE]

- [x] **Issue 逻辑复用**：CLI (`monoco issue`) 直接调用 `monoco.features.issue.core`。
- [x] **配置管理一致性**：Daemon 通过 `ConfigMonitor` 实时更新配置，确保与 CLI 行为同步。

### 4. VS Code 插件“去计算化” [DONE]

- [x] **统一 Profiles 扫描**：插件通过 `/api/v1/execution/profiles` 获取，不再手动扫描。
- [x] **移除冗余解析**：删除 `IssueParser.ts`，CodeLens 定位改为轻量级行扫描。
- [x] **插件瘦身**：插件侧不持有任何 Issue 生命周期逻辑（如状态环），完全透传 API。

## 验收标准 (Acceptance Criteria)

- [x] `monoco issue open/close` 导致 VS Code Kanban 实时刷新。
- [x] `monoco.yaml` (legacy) 兼容逻辑彻底移除，统一使用 `.monoco/` 目录。
- [x] 插件侧 `IssueParser.ts` 文件被物理删除。
- [x] 代码中不再存在硬编码的生命周期状态环。

## Review Comments

- [x] Self-Review
