<!--
⚠️ IMPORTANT: This file is partially managed by Monoco.
- Content between MONOCO_GENERATED_START and MONOCO_GENERATED_END is auto-generated.
- Use `monoco sync` to refresh this content.
- Do NOT manually edit the managed block.
- Do NOT add content after MONOCO_GENERATED_END (use separate files instead).
-->

<!-- MONOCO_GENERATED_START -->
## Monoco

> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.

### Agent

#### Monoco 核心

项目管理的核心命令。遵循 **Trunk Based Development (TBD)** 模式。

- **初始化**: `monoco init` (初始化新的 Monoco 项目)
- **配置**: `monoco config get|set <key> [value]` (管理配置)
- **同步**: `monoco sync` (与 agent 环境同步)
- **卸载**: `monoco uninstall` (清理 agent 集成)

---

#### ⚠️ Agent 必读: Git 工作流协议 (Trunk-Branch)

在修改任何代码前,**必须**遵循以下步骤:

##### 标准流程

1. **创建 Issue**: `monoco issue create feature -t "功能标题"`
2. **🔒 启动 Branch**: `monoco issue start FEAT-XXX --branch`
   - ⚠️ **强制要求隔离**: 使用 `--branch` 或 `--worktree` 参数
   - ❌ **严禁操作 Trunk**: 禁止在 Trunk (`main`/`master`) 分支直接修改代码
3. **实现功能**: 正常编码和测试
4. **同步文件**: `monoco issue sync-files` (提交前必须运行)
5. **提交审查**: `monoco issue submit FEAT-XXX`
6. **合拢至 Trunk**: `monoco issue close FEAT-XXX --solution implemented`

##### 质量门禁

- Git Hooks 会自动运行 `monoco issue lint` 和测试
- 不要使用 `git commit --no-verify` 绕过检查
- Linter 会阻止在受保护的 Trunk 分支上的直接修改

> 📖 详见 `monoco-issue` skill 获取完整工作流文档。

### Issue Management

#### Issue 管理 & Trunk Based Development

Monoco 遵循 **Trunk Based Development (TBD)** 模式。所有的开发工作都在短平快的分支（Branch）中进行，并最终合并回干线（Trunk）。

使用 `monoco issue` 管理任务生命周期。

- **创建**: `monoco issue create <type> -t "标题"`
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint`
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]`
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (如 `Issues/Features/open/`)

#### 标准工作流 (Trunk-Branch)

1. **创建 Issue**: `monoco issue create feature -t "标题"`
2. **开启 Branch**: `monoco issue start FEAT-XXX --branch` (隔离环境)
3. **实现功能**: 正常编码与测试。
4. **同步变更**: `monoco issue sync-files` (更新 `files` 字段)。
5. **提交审查**: `monoco issue submit FEAT-XXX`。
6. **合并至 Trunk**: `monoco issue close FEAT-XXX --solution implemented` (进入 Trunk 的唯一途径)。

#### Git 合并策略

- **禁止手动操作 Trunk**: 严禁在 Trunk (`main`/`master`) 分支直接执行 `git merge` 或 `git pull`。
- **原子合并**: `monoco issue close` 仅根据 Issue 的 `files` 列表将变更从 Branch 合并至 Trunk。
- **冲突处理**: 若产生冲突，请遵循 `close` 命令产生的指引进行手动 Cherry-Pick。
- **清理策略**: `monoco issue close` 默认执行清理（删除 Branch/Worktree）。

### Memo (Fleeting Notes)

#### 信号队列模型 (FEAT-0165)

轻量级笔记，用于快速记录想法。

- **Memo 是信号，不是资产** - 其价值在于触发行动
- **文件存在 = 信号待处理** - Inbox 有未处理的 memo
- **文件清空 = 信号已消费** - Memo 在处理后被删除
- **Git 是档案** - 历史记录在 git 中，不在应用状态里

#### 命令

- **添加**: `monoco memo add "内容" [-c 上下文]` - 创建信号
- **列表**: `monoco memo list` - 显示待处理信号（已消费的 memo 在 git 历史中）
- **删除**: `monoco memo delete <id>` - 手动删除（通常自动消费）
- **打开**: `monoco memo open` - 直接编辑 inbox

#### 工作流

1. 将想法捕获为 memo
2. 当阈值（5个）达到时，自动触发 Architect
3. Memo 被消费（删除）并嵌入 Architect 的 prompt
4. Architect 从 memo 创建 Issue
5. 不需要"链接"或"解决" memo - 消费后即消失

#### 指南

- 使用 Memo 记录** fleeting 想法** - 可能成为 Issue 的事情
- 使用 Issue 进行**可操作的工作** - 结构化、可跟踪、有生命周期
- 永远不要手动将 memo 链接到 Issue - 如果重要，创建一个 Issue

### Glossary

#### 核心架构隐喻: "Linux 发行版"

| 术语             | 定义                                                                     | 隐喻                              |
| :--------------- | :----------------------------------------------------------------------- | :-------------------------------- |
| **Monoco**       | 智能体操作系统发行版。管理策略、工作流和包系统。                         | **发行版** (如 Ubuntu, Arch)      |
| **Kimi CLI**     | 核心运行时执行引擎。处理 LLM 交互、工具执行和进程管理。                  | **内核** (Linux Kernel)           |
| **Session**      | 由 Monoco 管理的智能体内核初始化实例。具有状态和上下文。                 | **初始化系统/守护进程** (systemd) |
| **Issue**        | 具有状态（Open/Done）和严格生命周期的原子工作单元。                      | **单元文件** (systemd unit)       |
| **Skill**        | 扩展智能体功能的工具、提示词和流程包。                                   | **软件包** (apt/pacman package)   |
| **Context File** | 定义环境规则和行为偏好的配置文件（如 `GEMINI.md`, `AGENTS.md`）。        | **配置** (`/etc/config`)          |
| **Agent Client** | 连接 Monoco 的用户界面（CLI, VSCode, Zed）。                             | **桌面环境** (GNOME/KDE)          |
| **Trunk**        | 稳定的主干代码流（通常是 `main` 或 `master` 分支）。所有功能的最终归宿。 | **主干/干线**                     |
| **Branch**       | 为解决特定 Issue 而开启的临时隔离开发环境。                              | **分支**                          |

#### Context File

像 `GEMINI.md` 这样的文件，为智能体提供"宪法"。它们定义了特定上下文（根目录、目录、项目）中智能体的角色、范围和行为策略。

#### Headless

Monoco 设计为无需原生 GUI 即可运行。它通过标准协议（LSP, ACP）暴露其能力，供各种客户端（IDE、终端）使用。

#### Universal Shell

CLI 是所有工作流的通用接口的概念。Monoco 作为 shell 的智能层。

### Spike (Research)

#### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

#### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

<!-- MONOCO_GENERATED_END -->
