---
id: FEAT-0057
type: feature
status: open
stage: todo
title: Kanban Terminal Integration (xterm.js)
created_at: '2026-01-14T00:00:00'
updated_at: '2026-01-14T11:47:28'
parent: EPIC-0010
dependencies:
- FEAT-0056
related: []
tags:
- kanban
- ui
- pty
- xterm
owner: Frontend Engineer
---

# Feature: Kanban Terminal Integration

## Context

Backend PTY Service (`monoco pty`) has been implemented via FEAT-0056.
Now we need to integrate the Terminal interface into the Kanban Web UI to achieve the "Cockpit" experience.

## Goals

1.  Integrate `xterm.js` into the Next.js application.
2.  Implement a collapsable Bottom Panel for the terminal.
3.  Connect to `ws://localhost:3124` to stream PTY data.

## Technical Design

### 1. Dependencies

- `xterm`: Core terminal emulator.
- `xterm-addon-fit`: Auto-resize support.
- `xterm-addon-web-links`: Clickable links.

### 2. Components

- **`TerminalPanel`**:
  - Position: Fixed at bottom (`z-50`).
  - Layout: Header (Tabs + Actions) + Body (Xterm Container).
  - State: `isOpen`, `activeSessionId`.

### 3. State Management

- Use `React Context` (`TerminalContext`) to manage the WebSocket connection and global visibility.
- **Shortcuts**: Listen for `Cmd+J` locally to toggle visibility.

### 4. Connection Logic

- Connect to `ws://localhost:3124/ws/{session_id}`.
- Handshake: Send initial resize event on connect.
- Reconnect: Implement simple backoff retry strategy.

## Tasks

- [x] **Setup**: Install `xterm`, `xterm-addon-fit`.
- [x] **Component**: Create `src/components/terminal/XTermView.tsx`.
- [x] **Layout**: Create global `TerminalPanel` in `providers.tsx` or layout root.
- [x] **Logic**: Implement WebSocket hook to pipe data to/from xterm instance.
- [x] **Style**: Apply Monoco theme (colors, fonts) to xterm.

## Acceptance Criteria

- [x] Kanban 底部出现 Terminal 条。
- [x] 点击或按快捷键可展开/折叠面板。
- [x] 终端能成功连接后端，显示 prompt，并能执行 `ls` 命令。
- [x] 调整浏览器窗口大小时，终端内容自适应重排 (resize)。
