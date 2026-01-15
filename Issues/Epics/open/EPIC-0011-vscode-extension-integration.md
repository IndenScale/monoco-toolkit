---
id: EPIC-0011
type: Epic
title: VS Code Cockpit Integration (VS Code 驾驶舱集成)
status: Open
owner: Product Owner
parent: null
dependencies:
  - EPIC-0006
  - EPIC-0010
tags:
  - vscode
  - extension
  - webview
  - cockpit
created_at: 2026-01-14
progress: 2/4
files_count: 0
stage: draft
uid: 287d08
---

# EPIC-0011: VS Code Cockpit Integration (VS Code 驾驶舱集成)

## 执行摘要 (Executive Summary)

为了将 Monoco 打造为开发者的“第二大脑”，我们需要将其深度嵌入到开发者最核心的工作场域——VS Code。本项目旨在通过 VS Code Extension 将 Kanban (战略管理) 与 Agent Terminal (战术执行) 集成为一套无缝的“驾驶舱”体验。

这不仅是 UI 的迁移，更是上下文 (Context) 的横向贯通。

## 目标与价值 (Outcome & Value)

- **全链路闭环**: 实现从 Issue 阅读、代码定位、Agent 调度到代码提交的完全闭环，无需离开 IDE。
- **上下文增强**: 利用 VS Code API 提供的实时代码上下文（当前文件、选中行、诊断信息），大幅提升 Agent 的决策准确率。
- **极致体验**: 利用 VS Code 原生界面元素（Sidebar, Activity Bar, QuickPick）提供流畅的操作体验。

## 关键结果 (Key Results)

- **KR1**: 支持在 VS Code Sidebar/Webview 完整加载并运行 Monoco Kanban (Next.js 导出版)。
- **KR2**: 建立一套基于消息总线 (Message Bus) 的跨环境通信协议，支持 Webview、插件进程与 Monoco CLI/Daemon 之间的协同。
- **KR3**: 提供一键“由代码创建 Issue”和“一键定位 Issue 关联代码”的功能。
- **KR4**: 在右侧 Agent Bar 实现与 EPIC-0010 PTY 对接的实时执行流展示。

## 范围 (Scope)

### VS Code Extension (桥接层)

- **Activity Bar & Sidebar**: 挂载任务导航。
- **Status Bar**: 显示 Agent 状态与任务进度。
- **Command Palette Integration**: 快速调用 `monoco issue` 等命令。
- **Webview Adapter**: 实现 `acquireVsCodeApi` 到 Monoco Protocol 的适配。

### Toolkit/Kanban (展现层)

- **Universal Adpater**: 适配 Web 环境与 VS Code 环境的通信差异。
- **UX Tuning**: 针对小尺寸侧边栏设计的高密压缩视图。

### Experience (体验层)

- **Code Link**: Issue 详情页中的文件路径可点击，直接在 VS Code 中打开对应位置。
- **Agent Cockpit**: 类似 Cursor 的侧边交互栏，用于触发和监控 Agent 行为。

## 路线图 (Roadmap)

1. **原型验证 (P0)**: 验证 Webview 通信与样式适配。
2. **核心链接 (P1)**: 实现看板与 IDE 代码定位的联动。
3. **Agent 协同 (P2)**: 实现右侧 Agent Bar 与 PTY 的集成。
4. **生态扩展 (P3)**: 发布至 VS Code Marketplace。
