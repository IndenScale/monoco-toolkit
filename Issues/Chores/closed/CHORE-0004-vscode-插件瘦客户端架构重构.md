---
id: CHORE-0004
parent: EPIC-0000
uid: d31189
type: chore
status: closed
stage: done
title: VSCode 插件瘦客户端架构重构
created_at: '2026-01-16T22:32:58'
opened_at: '2026-01-16T22:32:58'
updated_at: '2026-01-16T22:42:30'
closed_at: '2026-01-16T22:42:30'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0004'
- '#EPIC-0000'
---

## CHORE-0004: VSCode 插件瘦客户端架构重构

### 背景与目标 (Context & Objective)

当前 VS Code 插件架构处于 "Hybrid Client" 状态:

- **写操作 (Write)**: 部分通过 CLI (LSP Lint)，部分手动实现 (Create/Toggle)。
- **读操作 (Read)**: 大量依赖前端手动扫描文件系统 (`indexer.ts`, `server.ts`)。

这种分裂导致了 "Split Brain" 风险，即 VS Code 与 Monoco Core 对于 "Issue 是什么" 以及 "操作是否合法" 存在认知偏差。
本任务旨在将插件彻底重构为 **Thin Client**，删除所有重复的业务逻辑，确立 Core/CLI 为唯一事实来源 (SSOT)。

### 范围 (Scope)

1.  **写操作重构**: 移除所有前端手动拼接文件/正则替换的代码。
2.  **读操作重构**: 移除所有前端文件扫描器/解析器。
3.  **Core 补全**: 确保 CLI 提供所有必要的 JSON 接口支持。

### 验收标准 (Acceptance Criteria)

- [x] **Create 一致性**: `monoco.createIssue` 命令必须调用 `monoco issue create`，不再包含任何模板字符串拼接。
- [x] **Update 一致性**: `monoco.toggleStatus` 等命令必须调用 `monoco issue update`，不再包含任何 Regex 替换。
- [x] **Read 一致性**: LSP Server 不再包含 `indexer.ts`，Issue 列表数据直接来自 `monoco issue list --json`。
- [x] **Agent 一致性**: LSP Server 不再扫描 `.monoco/execution`，Agent 列表来自 `monoco agent list` (需实现)。
- [x] **代码量缩减**: `indexer.ts` 应被删除，`server.ts` 和 `extension.ts` 大幅瘦身。

### 技术任务 (Technical Tasks)

#### Phase 1: Core 增强 (CLI Support)

- [x] **feat(cli)**: 确保 `monoco issue create` 支持 `--json` 输出完整文件路径与内容。
- [x] **feat(cli)**: 实现 `monoco agent list --json` 命令（替代 `execution profiles` 扫描）。
- [x] **feat(cli)**: (可选) 暴露 `monoco issue inspect --id <ID>` 以获取 `allowed_transitions`。

#### Phase 2: Extension 写路径重构 (Write Path)

- [x] **refactor(vscode)**: 重写 `CREATE_ISSUE` handler，对接 CLI create 命令。
- [x] **refactor(vscode)**: 删除 `monoco.toggleStatus/Stage` 的 Regex 实现，改为调用 `issue update`。

#### Phase 3: Extension 读路径重构 (Read Path)

- [x] **refactor(vscode)**: 重写 `indexer.ts` (或直接在 Server 中)，对接 `monoco issue list`。
- [x] **refactor(vscode)**: 重写 `FETCH_EXECUTION_PROFILES`，对接 `monoco agent list`。
- [x] **chore(vscode)**: 删除旧的 `indexer.ts` 及相关 legacy 代码。

#### Phase 4: 验证

- [x] **verify**: 确保所有操作在无 Monoco CLI 环境下有优雅的降级或错误提示。

## Review Comments

- [x] Self-Review
