# Monoco Toolkit


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

###### 术语表

####### Monoco 术语表

######## 核心架构隐喻: "Linux 发行版"

| 术语 | 定义 | 隐喻 |
| :--- | :--- | :--- |
| **Monoco** | 智能体操作系统发行版。管理策略、工作流和包系统。 | **发行版** (如 Ubuntu, Arch) |
| **Kimi CLI** | 核心运行时执行引擎。处理 LLM 交互、工具执行和进程管理。 | **内核** (Linux Kernel) |
| **Session** | 由 Monoco 管理的智能体内核初始化实例。具有状态和上下文。 | **初始化系统/守护进程** (systemd) |
| **Issue** | 具有状态（Open/Done）和严格生命周期的原子工作单元。 | **单元文件** (systemd unit) |
| **Skill** | 扩展智能体功能的工具、提示词和流程包。 | **软件包** (apt/pacman package) |
| **Context File** | 定义环境规则和行为偏好的配置文件（如 `GEMINI.md`, `AGENTS.md`）。 | **配置** (`/etc/config`) |
| **Agent Client** | 连接 Monoco 的用户界面（CLI, VSCode, Zed）。 | **桌面环境** (GNOME/KDE) |

######## 关键概念

######### Context File

像 `GEMINI.md` 这样的文件，为智能体提供"宪法"。它们定义了特定上下文（根目录、目录、项目）中智能体的角色、范围和行为策略。

######### Headless

Monoco 设计为无需原生 GUI 即可运行。它通过标准协议（LSP, ACP）暴露其能力，供各种客户端（IDE、终端）使用。

######### Universal Shell

CLI 是所有工作流的通用接口的概念。Monoco 作为 shell 的智能层。

### Agent

<!-- MONOCO_GENERATED_END -->
