# Monoco VS Code Extension

Monoco VS Code 扩展 (`monoco-vscode`) 是 Monoco Toolkit 的官方编辑器集成，旨在提供无缝的“代理原生”开发体验。

它采用 **Language Server Protocol (LSP)** 架构，将智能感知与 IDE 解耦，同时保留了可视化的 Cockpit 界面用于高层管理。

## 核心功能 (Core Features)

### 1. 智能语言服务 (LSP Intelligence)

由内置的 Node.js Language Server 提供支持，专门针对 Monoco 的任务文件 (`.md`) 进行语义分析。

- **实时诊断 (Diagnostics)**:
  - **Frontmatter 校验**: 检查 YAML 头部语法的正确性。
  - **生命周期逻辑检查**: 强制执行业务规则（例如：当 `status: closed` 时，`stage` 必须为 `done`），防止无效的状态流转。
- **智能补全 (Auto-Completion)**:
  - 根据工作区索引，自动补全 Issue ID 引用。
  - 提示信息包含 Issue 的标题、类型和阶段。
- **跳转定义 (Go to Definition)**:
  - 支持 `Ctrl+Click` (macOS `Cmd+Click`) 点击 Issue ID，直接跳转到对应的 Markdown 文件位置。

### 2. 可视化看板 (Cockpit View)

集成在 VS Code 活动栏 (Activity Bar) 中的可视化管理界面。

- **Monoco Kanban**: 提供全局任务的看板视图，直观展示 Epic/Feature/Bug 的流动。
- **实时同步**: 通过 SSE (Server-Sent Events) 与本地 Daemon 保持毫秒级同步，外部修改（如 CLI 操作）会即时反映在试图中。
- **快捷操作**:
  - 创建新 Issue。
  - 点击卡片打开对应的 Markdown 文件。
  - 查看和筛选执行配置 (Execution Profiles)。

### 3. 运行时管理 (Runtime Management)

扩展负责维护 Monoco 的后台服务，确保“开箱即用”。

- **自动守护 (Daemon Auto-start)**:
  - 扩展启动时会自动检测本地 `8642` 端口。
  - 若服务未运行，将自动在后台终端执行 `uv run monoco serve` 启动守护进程。
- **环境引导 (Bootstrap)**:
  - 自动检查并初始化必要的 `.monoco` 环境配置。

## 架构设计 (Architecture)

目前扩展处于 "Hybrid" 阶段，同时包含 LSP 和 Legacy Webview 逻辑：

- **Client (`/client`)**:
  - 负责 VS Code UI 集成 (Webview, Commands)。
  - 管理 Language Client 生命周期。
  - 负责与 Monoco Daemon (Python) 的 HTTP/SSE 通信。
- **Server (`/server`)**:
  - 标准 LSP 实现 (Node.js)。
  - 独立维护工作区的文件索引 (Indexer)。
  - 提供文本分析服务，**不依赖** Python 环境即可运行基础智能特性。

## 配置项 (Configuration)

- `monoco.apiBaseUrl`: Monoco Daemon API 地址 (默认: `http://127.0.0.1:8642/api/v1`)
- `monoco.webUrl`: Monoco Web UI 地址 (默认: `http://127.0.0.1:8642`)
