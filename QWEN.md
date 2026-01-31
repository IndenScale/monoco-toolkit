<!-- MONOCO_GENERATED_START -->
## Monoco Toolkit

> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.

### Issue Management

#### Issue 管理 (Agent 指引)

##### Issue 管理

使用 `monoco issue` 管理任务的系统。

- **创建**: `monoco issue create <type> -t "标题"` (类型: epic, feature, chore, fix)
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint` (手动编辑后必须运行)
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]` (更新文件追踪)
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (如 `Issues/Features/open/`)。
- **强制规则**:
  1. **先有 Issue**: 在进行任何调研、设计或 Draft 之前，必须先使用 `monoco issue create` 创建 Issue。
  2. **标题**: 必须包含 `## {ID}: {Title}` 标题（与 Front Matter 一致）。
  3. **内容**: 至少 2 个 Checkbox，使用 `- [ ]`, `- [x]`, `- [-]`, `- [/]`。
  4. **评审**: `review`/`done` 阶段必须包含 `## Review Comments` 章节且内容不为空。
  5. **环境策略**:
     - 必须使用 `monoco issue start --branch` 创建 Feature 分支。
     - 🛑 **禁止**直接在 `main`/`master` 分支修改代码 (Linter 会报错)。
     - **清理时机**: 环境清理仅应在 `close` 时执行。**禁止**在 `submit` 阶段清理环境。
     - 修改代码后**必须**更新 `files` 字段（通过 `sync-files` 或手动）。

### Spike (Research)

###### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

###### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

### Memo (Fleeting Notes)

Lightweight note-taking for ideas and quick thoughts.

- **Add**: `monoco memo add "Content" [-c context]`
- **List**: `monoco memo list`
- **Open**: `monoco memo open` (Edit in default editor)
- **Guideline**: Use Memos for ideas; use Issues for actionable tasks.

### Glossary

#### Monoco Glossary

##### Core Architecture Metaphor: "Linux Distro"

| Term             | Definition                                                                                          | Metaphor                            |
| :--------------- | :-------------------------------------------------------------------------------------------------- | :---------------------------------- |
| **Monoco**       | The Agent Operating System Distribution. Managed policy, workflow, and package system.              | **Distro** (e.g., Ubuntu, Arch)     |
| **Kimi CLI**     | The core runtime execution engine. Handles LLM interaction, tool execution, and process management. | **Kernel** (Linux Kernel)           |
| **Session**      | An initialized instance of the Agent Kernel, managed by Monoco. Has state and context.              | **Init System / Daemon** (systemd)  |
| **Issue**        | An atomic unit of work with state (Open/Done) and strict lifecycle.                                 | **Unit File** (systemd unit)        |
| **Skill**        | A package of capabilities (tools, prompts, flows) that extends the Agent.                           | **Package** (apt/pacman package)    |
| **Context File** | Configuration files (e.g., `GEMINI.md`, `AGENTS.md`) defining environment rules and preferences.    | **Config** (`/etc/config`)          |
| **Agent Client** | The user interface connecting to Monoco (CLI, VSCode, Zed).                                         | **Desktop Environment** (GNOME/KDE) |

##### Key Concepts

###### Context File

Files like `GEMINI.md` that provide the "Constitution" for the Agent. They define the role, scope, and behavioral policies of the Agent within a specific context (Root, Directory, Project).

###### Headless

Monoco is designed to run without a native GUI. It exposes its capabilities via standard protocols (LSP, ACP) to be consumed by various Clients (IDEs, Terminals).

###### Universal Shell

The concept that the CLI is the universal interface for all workflows. Monoco acts as an intelligent layer over the shell.

<!-- MONOCO_GENERATED_END -->
