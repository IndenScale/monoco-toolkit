---
id: FEAT-0101
uid: 4e0731
type: feature
status: open
stage: doing
title: 实现无状态 Agent Draft 命令
created_at: '2026-01-24T19:10:47'
updated_at: 2026-01-25 23:03:10
parent: EPIC-0019
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0019'
- '#FEAT-0101'
files: []
opened_at: '2026-01-24T19:10:47'
isolation:
  type: branch
  ref: feat/feat-0101-实现无状态-agent-draft-命令
  path: null
  created_at: '2026-01-25T23:03:10'
---

## FEAT-0101: 实现无状态 Agent Draft 命令

## 目标
实现一个 Agent 的 "One-shot" CLI 命令，用于执行原子任务而无需持久化 Session。
初始用例：`monoco agent draft` 用于根据简短的文本描述生成 Issue 文件。
这将 Agent 智能与 Daemon 运行时解耦，允许快速、可脚本化的使用。

## 验收标准
<!-- Define binary conditions for success. -->
- [ ] **CLI 命令**: `monoco agent draft` 可用。
- [ ] **输入**: 支持 `--type` 和 `--desc` (description)。
- [ ] **输出**: 根据描述自动生成结构化的 Issue 文件。
- [ ] **无状态**: 不需要运行中的 Daemon 或 Session。

## 技术任务
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [x] CLI 命令实现 (`monoco agent draft`)
- [x] Mock 生成逻辑 (Template-based for MVP)
- [x] 基于 Session 的集成 (作为短生命周期的 Agent Session 运行)
- [x] 与 Issue Core 集成 (create_issue_file)

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
- 2026-01-25: Implemented `draft` command in CLI. Fixed role name mismatch (crafter vs drafter). Fixed session monitoring loop to correctly poll worker status.

## Post-mortem (Session ae71e4f9)
**Date**: 2026-01-24
**Author**: Coroner (System)

### 问题分析
在处理此 Feature 时，前一个 Session 意外终止。
经检查，`monoco agent draft` 命令被标记为 "Done"，但 `monoco/features/scheduler/cli.py` 中缺失实现。

### 发现
1.  **缺少 CLI 入口**: `monoco/features/scheduler/cli.py` 仅包含 `run`, `kill`, `autopsy`, `list`, 和 `logs`。`draft` 命令未定义。
2.  **核心逻辑存在**: `monoco/features/issue/core.py` 正确定义了 `create_issue_file`，且 `monoco/features/scheduler/worker.py` 似乎包含 `drafter` 角色逻辑。
3.  **状态不一致**: 任务在 Issue 文件中被标记为完成，但代码未反映这一点。

### 恢复计划
-   [x] 重置任务: "CLI 命令实现" 和 "基于 Session 的集成"。
-   [x] 下一个 Agent 必须在 `monoco/features/scheduler/cli.py` 中实现 `draft` 命令。
-   [x] 验证 `monoco agent draft --desc "..."` 正确调用逻辑以创建 issue 文件。
