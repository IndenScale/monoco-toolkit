# Monoco Toolkit 架构 (Architecture)

Monoco Toolkit 是一个基于 Python 的模块化工具链，旨在为 Agent 和人类提供一致的开发体验。本构建遵循 DDD (领域驱动设计) 原则。

## 1. 核心架构模式 (Core Architectural Patterns)

### 1.1 文件系统即单一真实源 (Filesystem as SSOT)

**真理存储于磁盘上，而非内存中。**

- **数据持久化**: 所有的业务状态（Issues, Spikes, Configs）都必须以人类可读的文件格式（Markdown/YAML/JSON）持久化在文件系统中。
- **模块解耦**: 模块之间**禁止**直接通过内存调用传输业务数据。Feature A 不应直接调用 Feature B 的 Python 函数。所有的交互都应通过文件系统作为中介。
  - _错误示例_: `issue_manager.add_dependency(spike_id)`
  - _正确示例_: `Issue` 模块读取 `Spike` 模块生成的 `.md` 文件来验证引用。

### 1.2 生命周期分离 (Lifecycle Separation)

Toolkit 包含两种截然不同的运行时生命周期：

- **CLI (命令行界面)**: **瞬态 (Transient)**。
  - 不仅是人类的工具，更是 Agent 的“手”。
  - 每次调用都是独立的进程，启动 -> 执行 -> 退出。
  - 无状态（Stateless），每次运行都从 FS 重新水合上下文。
- **Daemon (守护进程)**: **长效 (Long-running)**。
  - 作为 UI (Kanban) 的后端服务。
  - 维护内存缓存（Watcher）以提供高性能的读取和推送（SSE）。
  - **不作为真理源**，它只是文件系统的“高性能视图”。

### 1.3 自举性与初始化 (Bootstrapping & Init)

每个功能模块都必须具备“自举能力”。

- **Init 接口**: 每个模块（如 `issue`, `spike`）都必须实现 `init` 子命令。
- **按需激活**: 用户（或 Agent）不应被迫接受全家桶。可以通过 `monoco spike init` 仅激活 Spike 功能。
- **约定优于配置**: `init` 应该生成标准的目录结构和默认配置，让模块立即进入可用状态。

## 2. 模块标准 (Module Standards)

Toolkit 采用插件化架构，每个 Feature 都是独立的目录。

```text
Toolkit/monoco/features/
├── issue/
│   ├── commands.py   # CLI 入口
│   ├── service.py    # 业务逻辑 (CRUD)
│   ├── models.py     # Pydantic 模型
│   └── daemon.py     # FastAPI 路由 (可选)
├── spike/
│   └── ...
└── ...
```

## 3. 跨模块协作 (Cross-Module Collaboration)

虽然禁止内存直接耦合，但模块间需要协作。我们通过 **"软链接" (Soft Linking)** 和 **"标准协议" (Standard Protocols)** 实现。

- **引用协议**: 如 `[[ticket-id]]` 或 `Ref: <ID>`，各模块负责解析标准文本模式。
- **公共接口**: 如果必须交互，模块应暴露显式的 `PublicAPI` 类，仅用于只读查询，严禁用于修改其他模块的状态。
