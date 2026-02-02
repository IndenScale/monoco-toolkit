---
name: monoco_atom_glossary
description: Monoco 官方术语表和操作法则
tags: [core, definition]
type: atom
version: 1.0.0
---

# Monoco 术语表

## 核心架构隐喻: "Linux 发行版"

| 术语 | 定义 | 隐喻 |
| :--- | :--- | :--- |
| **Monoco** | 智能体操作系统发行版。管理策略、工作流和包系统。 | **发行版** (如 Ubuntu, Arch) |
| **Kimi CLI** | 核心运行时执行引擎。处理 LLM 交互、工具执行和进程管理。 | **内核** (Linux Kernel) |
| **Session** | 由 Monoco 管理的智能体内核初始化实例。具有状态和上下文。 | **初始化系统/守护进程** (systemd) |
| **Issue** | 具有状态（Open/Done）和严格生命周期的原子工作单元。 | **单元文件** (systemd unit) |
| **Skill** | 扩展智能体功能的工具、提示词和流程包。 | **软件包** (apt/pacman package) |
| **Context File** | 定义环境规则和行为偏好的配置文件（如 `GEMINI.md`, `AGENTS.md`）。 | **配置** (`/etc/config`) |
| **Agent Client** | 连接 Monoco 的用户界面（CLI, VSCode, Zed）。 | **桌面环境** (GNOME/KDE) |

## 关键概念

### Context File

像 `GEMINI.md` 这样的文件，为智能体提供"宪法"。它们定义了特定上下文（根目录、目录、项目）中智能体的角色、范围和行为策略。

### Headless

Monoco 设计为无需原生 GUI 即可运行。它通过标准协议（LSP, ACP）暴露其能力，供各种客户端（IDE、终端）使用。

### Universal Shell

CLI 是所有工作流的通用接口的概念。Monoco 作为 shell 的智能层。
