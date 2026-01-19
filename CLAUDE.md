## Monoco Toolkit

> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.

### Design Philosophy

### 设计哲学

Monoco CLI is designed as an **Agent-Native Interface**.
Monoco CLI 被设计为 **Agent 原生接口**。

- **Strictly Non-Interactive**: Commands MUST NOT prompt for user input. If arguments are missing, the command MUST fail immediately.
- **严格非交互**: 命令绝不允许提示用户输入。如果参数缺失，命令必须立即失败。这确保了 Agent 行为的确定性。

- **Text as Interface**: We prefer structured text (Markdown/YAML) over complex UI states.
- **文本即接口**: 我们倾向于结构化文本 (Markdown/YAML) 而非复杂的 UI 状态。

- **Explicit Context**: Agents must provide full context (e.g., explicit paths) to avoid ambiguity.
- **显式上下文**: Agent 必须提供完整上下文（如显式路径）以避免歧义。

### Issue Management

### Issue 管理

使用 `monoco issue` 管理任务的系统。

- **创建**: `monoco issue create <type> -t "标题"` (类型: epic, feature, chore, fix)
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint` (手动编辑后必须运行)
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]`
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (例如 `Issues/Features/open/`)。不要偏离此结构。
- **环境策略**:
  - 必须使用 `monoco issue start --branch`。
  - 受保护分支 (main/master) 仅限只读。
  - Linter 会阻止在主分支直接修改代码。

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

### Release Management

### 发布管理

Manage release lifecycle and versioning.
管理发布生命周期和版本控制。

- **Protocol**: Releases must be pushed from a dedicated branch `release/vX.Y.Z` matching the version in `pyproject.toml`.
- **协议**: 发布必须从名为 `release/vX.Y.Z` 的专用分支推送，且分支名必须与 `pyproject.toml` 中的版本号匹配。

- **Set Version**: `python Toolkit/scripts/set_version.py <version>` (Update version in all manifests)
- **设置版本**: `python Toolkit/scripts/set_version.py <version>` (更新所有清单文件中的版本)

- **Release Check**: `Toolkit/scripts/run_release_checks.sh <version>` (Run full validation suite)
- **发布检查**: `Toolkit/scripts/run_release_checks.sh <version>` (运行完整验证套件)
