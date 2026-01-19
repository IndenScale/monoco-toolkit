---
id: FEAT-0080
type: feature
status: closed
stage: done
title: 'VS Code Execution UI: Sidebar & CodeLens'
created_at: '2026-01-15T23:30:15'
updated_at: '2026-01-15T23:30:18'
closed_at: '2026-01-15T23:30:18'
parent: EPIC-0010
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0010'
- '#FEAT-0080'
priority: High
author: Monoco
---

## FEAT-0080: VS Code Execution UI: Sidebar & CodeLens

## Feature: VS Code Execution UI

## 目标 (Objective)

为 Monoco Extension 增加可视化交互能力，使用户通过 Sidebar 管理 Execution，并在编辑器上下文中直接触发 Agent Action。

## 需求 (Requirements)

### 1. Sidebar Execution Manager

在 `monoco-cockpit` 视图容器中新增一个 "Executions" 视图。

- [x] **UI**: Tree View 结构。
- [x] **内容**:
  - [x] 列出系统注册的所有 Executions (读取 `monoco agent list --json`)。
  - [x] 列出当前配置的 Provider (Claude, Gemini, etc)。
- [x] **交互**:
  - [x] 点击 Execution 节点，可以查看其 Prompt 模板详情（只读 Webview 或 Virtual Document）。
  - [x] 右键菜单支持 "Run in Terminal"（调用 `monoco agent run ...`）。

### 2. Contextual Actions (Hover & CodeLens)

在 Markdown 编辑器中，增强对 `stage` 字段体验。

- [x] **Hover Provider**:
  - [x] 当鼠标悬停在 `stage: ...` 字段值上时。
  - [x] 显示 Markdown Tooltip，列出可用的下一阶段 Actions (基于 Execution Registry)。
- [x] **CodeLens**:
  - [x] 在 `stage` 行上方显示 `$(sparkle) Agent Actions` 链接。
  - [x] 点击后弹出 QuickPick，列出适用于当前文件类型的 Executions。
- [x] **Injection**:
  - [x] 选择 Action 后，支持弹出 InputBox 让用户输入额外指令（User Instruction）。
  - [x] 最终组装命令: `monoco agent run <task> <current_file> --instruction "..."`

## 技术方案 (Technical Design)

### 1. Execution Service (Client Side)

Extension 需要一个 `ExecutionService` 单例。

### 2. View - ExecutionsTreeProvider

实现 `vscode.TreeDataProvider`。

### 3. Editor - IssueHoverProvider

实现 `vscode.HoverProvider`。

## 验收标准 (Acceptance Criteria)

- [x] Sidebar 显示 "Executions" 面板，并列出 `refine-issue`。
- [x] 在 Issue 文件中 hover `stage` 字段，显示 Agent Actions 列表。
- [x] 点击 Action 能在 Terminal 中正确触发 `monoco agent run` 命令。

## Review Comments

- [x] Self-Review
