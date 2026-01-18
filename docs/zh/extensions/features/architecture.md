# 核心架构

`monoco-vscode` 扩展采用严格的客户端-服务端（Client-Server）分离架构，所有通信基于 LSP 协议。

- **架构模式**
  - **协议**: Language Server Protocol (LSP)。
  - **通信方式**: 进程间通信 (IPC)。
  - **依赖变更**: 已完全移除对旧版 HTTP Server 的依赖。

- **客户端 (Client - VS Code Extension)**
  - **职责**:
    - 负责所有 UI 交互（Webview, TreeView, QuickPick）。
    - 注册 VS Code 命令和事件监听。
    - 管理 Webview 面板的生命周期。
  - **交互**: 通过 `sendRequest` 向服务端发送请求，接收服务端推送的通知。

- **服务端 (Server - Language Server)**
  - **职责**:
    - 维护工作区索引（Issue 索引、元数据缓存）。
    - 执行耗时的后台任务（如文件扫描、CLI 调用）。
    - 提供语言特性（自动补全、定义跳转、诊断）。
  - **实现**: 基于 Node.js，通过 `monoco` CLI 执行实际业务逻辑。
