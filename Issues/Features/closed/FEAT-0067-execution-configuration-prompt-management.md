---
id: FEAT-0067
uid: 232d88
type: feature
status: closed
stage: done
title: 执行配置与提示词管理
created_at: '2026-01-15T08:55:53'
opened_at: '2026-01-15T08:55:53'
updated_at: '2026-01-15T13:22:55'
closed_at: '2026-01-15T13:22:55'
parent: EPIC-0012
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0012'
- '#FEAT-0067'
---

## FEAT-0067: 执行配置与提示词管理

## 目标

为 Agent 执行 (Agent Execution) 实现一套基于文件的配置系统。支持全局和项目级作用域，并通过 VS Code 扩展的统一 UI 进行控制。

## 验收标准

1. **混合存储 (Hybrid Storage)**:
   - 支持全局配置: `~/.monoco/execution/{action}/SOP.md`
   - 支持项目配置: `./.monoco/execution/{action}/SOP.md`
   - 同名 Action 的项目级配置将覆盖全局配置。

2. **配置格式 (Configuration Format)**:
   - 使用 Markdown 文件 (`SOP.md`) 存储系统提示词 (System Prompts) 或标准作业程序 (SOP)。
   - 使用 YAML Frontmatter 存储元数据:
     - `command`: 要运行的 CLI 命令 (如 `gemini -p`)。
     - (未来扩展) `max_turns`, `timeout`, `branch_name_template`, `access_scope`。

3. **设置 UI (Settings UI)**:
   - 重构设置页面，使用 **选项卡 (Tabs)** 结构: [常规 (General)] | [执行 (Execution)]。
   - **“执行”选项卡**:
     - 列出所有发现的配置 Profile (显示名称及来源)。
     - 点击 Profile 即可立即在 VS Code 编辑器中打开对应的 `SOP.md` 文件。

## 技术任务

- [x] 创建全局 (`~/.monoco/execution`) 和项目 (`.monoco/execution`) 范围的目录结构。
- [x] 创建带有正确 Frontmatter 的示例 `implement/SOP.md`。
- [x] 在 Extension Host 中实现 `scanExecutionProfiles` 以发现配置。
- [x] 重构 Webview `settings` 页面以支持选项卡 (`General`, `Execution`)。
- [x] 实现 IPC 处理器 `FETCH_EXECUTION_PROFILES` 和 `OPEN_FILE`。
- [x] 在 UI 中添加“执行”选项卡并渲染 Profile 列表。
- [x] 启用“点击编辑”功能。

## Review Comments

- [x] Self-Review
