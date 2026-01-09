---
name: toolkit-core
description: Monoco Toolkit 基础技能。涵盖项目初始化、环境探测及 Agent-Native 交互规范。
---

# Toolkit 基础 (Toolkit Core)

Monoco Toolkit 是 Agent 的感官和运动系统。此技能定义了 Toolkit 的基础操作和交互标准。

## 核心哲学

1. **Agent Native**: 优先服务于 Agent。所有命令必须支持 `--json` 输出。
2. **Dual Mode**:
   - **Human Mode**: 默认模式，输出易读的文本、表格和树状图。
   - **Agent Mode**: 通过 `--json` 或设置环境变量 `AGENT_FLAG=true` 触发，输出紧凑的 JSON。

## 基础指令

### 1. 初始化 (Setup)

- `monoco init`: 初始化 Monoco 环境。
  - **Global Setup**: 配置个人信息（作者名等），存储在 `~/.monoco/config.yaml`。
  - **Project Setup**: 在当前目录初始化项目，配置项目名称、Key（工单前缀）等，存储在 `.monoco/config.yaml`。
  - 参数:
    - `--global`: 仅配置全局设置。
    - `--project`: 仅配置当前项目。

### 2. 环境探测 (Info)

- `monoco info`: 显示当前 Toolkit 的运行状态。
  - 包含版本信息、当前模式 (Human/Agent)、项目根目录及关联项目信息。
  - 建议在 Session 开始时运行，以确认上下文对齐。

## 交互规范

### 1. 结构化输出

Agent 在调用 `monoco` 命令时，应始终关注其 JSON 输出（如果提供）。

### 2. 上下文自动识别

Toolkit 会自动从当前目录向上寻找 `.monoco` 文件夹或 `monoco.yaml` 文件以确定项目根目录。Agent 无需手动指定路径。
