# Monoco Toolkit Guidance

本目录是 Monoco Toolkit 的工程核心。

## 🧠 开发原则 (Principles)

### 1. Issue 归属 (Issue Ownership)

- **工程隔离**: 所有涉及 Toolkit 代码实现的 Fix, Feature, Chore 必须存放在 `Toolkit/Issues/`。
- **关联引用**: 若某个任务是根目录 Epic 的子任务，请在 Frontmatter 中使用 `parent: root::EPIC-XXXX` 进行关联。

### 2. 开发与运行 (Development & Runtime)

- **严禁使用全局工具**: 在开发过程中，**禁止**运行全局安装的 `monoco` 命令测试代码。
- **虚拟环境优先**: 必须使用 `uv run monoco` 来运行当前目录下的源代码。
- **环境切换**: 修改代码后，应立即在 `Toolkit/` 目录下运行 `uv run monoco issue lint` 验证逻辑。

### 3. 工程流 (Engineering Workflow)

采用 **主干开发 (Trunk Based Development)** 模式。

- **分支策略**:
  - **Main**: 唯一真理源 (Source of Truth)。
  - **Feature**: 短命分支 (`feat/ID`, `fix/ID`)，完成后 Squash Merge 并删除。
- **发布策略**:
  - **Trigger**: 仅通过 Git Tag (`v*`) 触发发布流水线。
  - **Constraint**: 严禁维护长周期的 `release` 分支。
  - **Version Update**: 必须使用 `python Toolkit/scripts/set_version.py <version>` 更新版本号，严禁手动修改配置文件。

## Issue 管理 (Agent 指引)

使用 `monoco issue` 子命令进行生命周期管理。

- **创建**: `monoco issue create <type> -t "标题"`
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint` (手动编辑后必须运行)
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]`
- **物理结构**: `Issues/{FormattedType}/{status}/`

### 强制规则 (Hard Rules)

1. **先有 Issue，后有 Draft**: 开始任何调研、设计或 Draft 阶段之前，必须使用 `monoco issue create` 创建 Issue。禁止在没有 Issue 的情况下开展工作。
2. **分支隔离 (Build 阶段)**: 进行代码构建或修改时，**必须**使用 `monoco issue start --branch` 创建特有的 Git 分支。禁止在 `main` 分支直接提交。
3. **环境清理时机**: 环境清理（分支/Worktree 删除）**仅**应在 `monoco issue close --prune` 时执行。**禁止**在 `submit` 阶段清理环境，因为 Review 过程可能需要进一步修改。
4. **标题对齐**: 必须包含 `## {ID}: {Title}` 标题，且与 Frontmatter 一致。
5. **任务颗粒度**: 至少包含 2 个任务项，使用 `- [ ]` 语法。
6. **评审义务**: 进入 `review` 或 `done` 阶段时，必须包含 `## Review Comments` 章节。

## Spike (研究)

管理外部参考仓库，用于学习成熟架构或库的使用。

- **添加**: `monoco spike add <url>`
- **同步**: `monoco spike sync`
- **读取**: 参考代码存放在 `.reference/` 目录下，仅供只读。

## 文档国际化 (I18n)

确保 Toolkit 及其文档支持多语言协作。

- **扫描**: `monoco i18n scan`
- **翻译**: 遵循 `folder/zh/file.md` 的层级结构。






## Monoco Toolkit

> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.

### Issue Management

# Issue 管理 (Agent 指引)

## Issue 管理

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

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

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

# Issue 管理 (Agent 指引)

## Issue 管理

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

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

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

# Issue 管理 (Agent 指引)

## Issue 管理

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

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

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

# Issue 管理 (Agent 指引)

## Issue 管理

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

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

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

# Issue 管理 (Agent 指引)

## Issue 管理

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

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

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

# Issue 管理 (Agent 指引)

## Issue 管理

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

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

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
