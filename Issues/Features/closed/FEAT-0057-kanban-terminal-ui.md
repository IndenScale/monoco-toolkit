---
id: FEAT-0057
type: feature
status: closed
stage: done
title: 看板终端集成 (xterm.js)
created_at: '2026-01-14T00:00:00'
updated_at: '2026-01-15T13:45:57'
closed_at: '2026-01-15T13:45:57'
parent: EPIC-0010
solution: implemented
dependencies:
- FEAT-0056
related: []
domains: []
tags:
- '#EPIC-0010'
- '#FEAT-0056'
- '#FEAT-0057'
- kanban
- pty
- ui
- xterm
owner: 前端工程师
uid: 86ce1a
---

## FEAT-0057: 看板终端集成 (xterm.js)

# 功能: 看板终端集成

## 上下文

后端 PTY 服务 (`monoco pty`) 已通过 FEAT-0056 实现。
现在我们需要将终端界面集成到看板 Web UI 中以实现"驾驶舱"体验。

## 目标

1.  将 `xterm.js` 集成到 Next.js 应用程序中。
2.  为终端实现可折叠的底部面板。
3.  连接到 `ws://localhost:3124` 以流式传输 PTY 数据。

## 技术设计

### 1. 依赖项

- `xterm`: 核心终端模拟器。
- `xterm-addon-fit`: 自动调整大小支持。
- `xterm-addon-web-links`: 可点击链接。

### 2. 组件

- **`TerminalPanel`**:
  - 位置: 固定在底部 (`z-50`)。
  - 布局: 头部（标签 + 操作）+ 主体（Xterm 容器）。
  - 状态: `isOpen`，`activeSessionId`。

### 3. 状态管理

- 使用 `React Context` (`TerminalContext`) 管理 WebSocket 连接和全局可见性。
- **快捷键**: 监听本地 `Cmd+J` 以切换可见性。

### 4. 连接逻辑

- 连接到 `ws://localhost:3124/ws/{session_id}`。
- 握手: 连接时发送初始调整大小事件。
- 重新连接: 实现简单的退避重试策略。

## 任务

- [x] **设置**: 安装 `xterm`，`xterm-addon-fit`。
- [x] **组件**: 创建 `src/components/terminal/XTermView.tsx`。
- [x] **布局**: 在 `providers.tsx` 或布局根目录中创建全局 `TerminalPanel`。
- [x] **逻辑**: 实现 WebSocket 钩子以将数据传输到/从 xterm 实例传输。
- [x] **样式**: 将 Monoco 主题（颜色、字体）应用于 xterm。

## 验收标准

- [x] 看板底部出现终端条。
- [x] 点击或按快捷键可展开/折叠面板。
- [x] 终端能成功连接后端，显示提示符，并能执行 `ls` 命令。
- [x] 调整浏览器窗口大小时，终端内容自适应重排 (resize)。

## Review Comments

- [x] Self review
