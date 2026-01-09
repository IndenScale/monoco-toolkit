# Monoco Initialization

`monoco init` 是 Monoco Toolkit 的引导命令，用于初始化 Monoco 的运行环境。它负责建立全局配置、项目级配置，并生成必要的目录结构和智能体记忆注入。

## 核心功能

1. **环境自举 (Bootstrap)**: 检查并创建必要的配置文件。
2. **上下文注入 (Context Injection)**: 将 Toolkit 的能力描述（Skills & Prompts）注入到项目的 `GEMINI.md` 或 `CLAUDE.md` 中，激活 AI 智能体的能力。
3. **结构脚手架 (Scaffolding)**: 初始化 `Issues/`, `.references/` 等标准目录结构。

## 用法

```bash
monoco init [OPTIONS]
```

### 选项

- `--global`: 仅配置用户全局设置（如作者名称）。
- `--project`: 仅配置当前项目设置（如项目名称、Key）。
- `--help`: 显示帮助信息。

通常在克隆一个新仓库或创建一个新项目时，直接运行 `monoco init` 即可。

## 初始化流程详解

### 1. 全局配置 (Global Configuration)

- **位置**: `~/.monoco/config.yaml`
- **内容**: 存储用户的全局身份信息。
- **交互**:
  - 首次运行时，会询问 "Your Name"。该名称将作为 Issue 系统的默认 Author。
  - 支持从 git config 自动读取作为默认值。

```yaml
core:
  author: "Alice"
```

### 2. 项目配置 (Project Configuration)

- **位置**: `./.monoco/config.yaml`
- **内容**: 定义项目的元数据及路径映射。
- **交互**:
  - **Project Name**: 项目名称。
  - **Project Key**: 3-4 位大写字母，作为 Issue ID 的前缀 (e.g., `MON-123`)。Monoco 会根据项目名自动推荐 Key。

生成的配置文件示例：

```yaml
project:
  name: "Monoco Main"
  key: "MON"
paths:
  issues: "Issues" # Issue 存储路径
  spikes: ".references" # Spike 把资料存储路径
  specs: "SPECS" # 规格说明书路径
```

### 3. 脚手架与资源注入 (Scaffolding & Injection)

`monoco init` 会调用各个功能模块 (Features) 的 `init` 方法，执行以下操作：

- **Issues**:确保存储目录存在（默认 `Issues/`）。
- **Spikes**: 确保存储目录存在（默认 `.references/`）。
- **I18n**: 初始化国际化相关设置。
- **Skills**:
  - 在 `Toolkit/skills/` 下生成各个模块的 `SKILL.md` (如 `issues-management/SKILL.md`)。
  - **关键步骤**: 修改项目根目录下的 `GEMINI.md`, `CLAUDE.md`, `AGENTS.md`。
  - **注入内容**: 在这些文件中插入或更新 `## Monoco Toolkit` 章节，包含所有可用命令的 Prompt 提示。

## 常见问题

### Q: 如果我修改了 `GEMINI.md` 里的 Prompt，会被覆盖吗？

A: `monoco init` 使用正则匹配 `## Monoco Toolkit` 章节。

- 如果该章节存在，会进行**全量替换**。请不要在该章节内手动修改内容，而是修改对应的 Feature 代码 (Generated Source)。
- 该章节之外的内容不会被影响。

### Q: 如何更新 Toolkit 的 Prompt？

A: 当 Monoco Toolkit 升级后，只需在项目根目录再次运行 `monoco init`，即可将最新的 Prompt 注入到 `GEMINI.md` 中。
