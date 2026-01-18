---
id: FEAT-0075
uid: c5fed3
type: feature
status: closed
stage: done
solution: implemented
title: 'VS Code Extension Realignment: Implementation of Proxy Pattern'
created_at: '2026-01-15T18:02:47'
opened_at: '2026-01-15T18:02:47'
updated_at: '2026-01-15T18:30:00'
closed_at: '2026-01-15T18:30:00'
parent: EPIC-0013
dependencies: []
related: []
tags:
- '#EPIC-0013'
- '#FEAT-0075'
- extension
---

## FEAT-0075: VS Code Extension Realignment: Implementation of Proxy Pattern

## 最终成果 (Outcome)

成功将 VS Code 插件重构为纯粹的 **Proxy (代理)**。插件侧零逻辑,所有行为均由 Server 驱动。

### 核心亮点

1. **Server-Driven CodeLens**: 按钮列表、标题、目标状态均来自后端 `actions` 字段。
2. **符合 VS Code 风格的交互**: 取消图标,改为平铺的动作按钮。
3. **实时响应**: 通过原生 SSE 流实现 UI 的自动刷新。
4. **移除冗余**: 彻底删除了 `IssueParser.ts` 和插件侧的文件扫描逻辑。

## 目标 (Objective)

将插件重构为 **Proxy 模式**，彻底移除其“计算”职责，仅作为服务器状态的展示层和请求触发器。

## 验收标准 (Acceptance Criteria)

- [x] **1. Profiles 去中心化**: 插件侧扫描 `.monoco/execution` 的逻辑彻底移除, 改为调用 `/api/v1/execution/profiles`。
- [x] **2. Issue 解析下沉**: `IssueLensProvider` 不再手动解析 Markdown Frontmatter,改为通过文件的绝对路径向 API 请求 `GET /api/v1/issues?path=<absolute_path>` 获取元数据。
- [x] **3. 操作行为闭环**: `toggleStatus`、`toggleStage`、`selectParent` 等指令不再直接修改文档内容,而是发送 `PATCH /api/v1/issues/{id}` 请求。
- [x] **4. 自动刷新**: 插件通过 SSE 监听 `issue_upserted`、`issue_moved` 等事件,自动刷新相关展示(如 CodeLens 或 Kanban)。

## 技术任务 (Technical Tasks)

- [x] **Task 0: 后端 API 增强**
  - [x] 增强 `IssueMetadata` 模型: 增加 `available_actions` 字段。
  - [x] 实现 `get_available_actions()` 核心逻辑。
  - [x] 增强 `update_issue()` 核心函数: 支持所有新字段的更新和验证。
- [x] **Task 1: 重构 Execution Profiles 获取**
  - [x] 物理文件扫描逻辑彻底移除,改为通过 API 获取。
- [x] **Task 2: 实现 CodeLens 异步解析**
  - [x] 修改 `IssueLensProvider`,调用 `GET /api/v1/issues?path=<absolute_path>`。
- [x] **Task 3: 重构 Issue 指令集与事件桥接**
  - [x] 修改 `issueCommands.ts`,将文本操作替换为标准的 API 请求。
  - [x] 注册 `monoco.runAction` 通用动作指令。
  - [x] 实现 SSE 事件流监听并触发 UI 刷新。
- [x] **Task 4: 增强 Daemon 服务一致性**
  - [x] 确保广播器 (Broadcaster) 正确发送所有 Issue 生命周期事件。
- [x] **Task 5: 清理冗余代码**
  - [x] 删除了 `IssueParser.ts`。
  - [x] 移除了 `extension.ts` 中的手动文件扫描。

## Review Comments

- [x] Self-Review
