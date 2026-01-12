# Monoco Toolkit

> **原生代理 (Agent-Native) 开发体验。**

Monoco Toolkit 是一套专为弥合“人类意图”与“代理执行”之间鸿沟而设计的工具链。它通过为 Agent 提供标准化的、确定性的接口来交互代码库、管理任务和获取外部知识，从而解决“自举悖论”。

## 愿景 (Vision)

构建一个 **人机共生开发环境 (Symbiotic Development Environment)**：

- **人类** 专注于 战略 (Strategy)、价值定义 (Value) 和 审查 (Review) —— 通过 Kanban UI。
- **代理** 负责 执行 (Execution)、维护 (Maintenance) 和 验证 (Validation) —— 通过 Toolkit CLI。

## 核心组件 (Components)

Toolkit 包含其实包含两个主要界面：

### 1. Toolkit CLI (`monoco`)

_Agent 的感官延伸。_
一个基于 Python 的 CLI，提供对项目状态的结构化、确定性访问。它奉行 **"Task as Code"** 哲学，将任务、Spike 和质量检查作为文件系统上的结构化文件进行管理。

### 2. Kanban UI

_人类的驾驶舱。_
一个基于 Next.js 的 Web 应用程序，由 `monoco serve` 驱动，为管理由 Toolkit 定义的史诗、故事和任务提供类似 Linear 的现代化体验。

## 快速开始 (Quick Start)

### 1. 安装 CLI

```bash
cd Toolkit
pip install -e .
```

### 2. 启动守护进程与 UI

```bash
# 启动后端守护进程
monoco serve

# 在另一个终端启动 UI
cd Toolkit/Kanban
npm run dev
```

## 文档索引 (Documentation)

- **架构设计**: [设计哲学与标准](docs/zh/architecture.md)
- **Issue 系统**: [用户手册](docs/zh/issue/manual.md)
- **Spike 系统**: [用户手册](docs/zh/spike/manual.md)
