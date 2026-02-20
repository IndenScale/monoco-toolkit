---
id: FEAT-0204
uid: ee0a36
type: feature
status: closed
stage: done
title: 'pretty-markdown: 自动格式化 Markdown 及配置同步分发'
created_at: '2026-02-20T07:17:02'
updated_at: '2026-02-20T09:41:10'
parent: EPIC-0000
dependencies: []
related:
  - FEAT-0203
domains: []
tags:
  - '#EPIC-0000'
  - '#FEAT-0203'
  - '#FEAT-0204'
files:
  - .gitignore
  - .markdownlint.json
  - .markdownlintignore
  - resources/config-templates/markdownlint/.markdownlint.json
  - resources/config-templates/markdownlint/.markdownlintignore
  - resources/config-templates/prettier/.prettierignore
  - resources/config-templates/prettier/.prettierrc
  - resources/config-templates/prettier/package.json
  - src/monoco/features/hooks/resources/pretty-markdown.sh
  - src/monoco/features/pretty_markdown/__init__.py
  - src/monoco/features/pretty_markdown/commands.py
  - src/monoco/features/pretty_markdown/core.py
  - src/monoco/main.py
criticality: medium
solution: implemented
opened_at: '2026-02-20T07:17:02'
closed_at: '2026-02-20T09:45:00'
isolation:
  type: worktree
  ref: FEAT-0204-pretty-markdown-自动格式化-markdown-及配置同步分发
  path: /Users/indenscale/Documents/Projects/Monoco/Monoco/.monoco/worktrees/feat-0204-pretty-markdown-自动格式化-markdown-及配置同步分发
  created_at: '2026-02-20T09:32:07'
---

## FEAT-0204: pretty-markdown: 自动格式化 Markdown 及配置同步分发

## Objective

实现 Markdown 文件的标准化格式化，包含两个层面：

1. **自动格式化**：Agent 保存 Markdown 文件后自动 prettier 格式化
2. **配置同步**：将标准化的 prettier/markdownlint 配置分发到项目，确保团队一致性

**使用 AgentHooks 实现**：利用 `post-tool-call` 事件拦截文件保存操作，当检测到 `.md` 文件被修改时，自动触发格式化。

## Acceptance Criteria

- [x] Hook 拦截 Markdown 文件保存 (`WriteFile`, `StrReplaceFile`)
- [x] 仅处理 `.md` 和 `.mdx` 文件
- [x] 运行 `markdownlint` 检查，仅当发现问题时拦截
  - 无问题 → 静默通过，零打扰
  - 有 warning/error → 拦截并注入 Agent 上下文
- [x] Agent 根据问题类型自主决策：
  - 纯格式问题（MD013/行长度等）→ 调用 `prettier --write` 自动修复
  - 内容/语义问题（MD033/HTML 等）→ 手动修改
  - 混合/不确定 → Agent 自行判断优先级
- [x] 格式化失败不阻断 Agent 工作流（记录警告日志）
- [x] 使用项目根目录的 `.prettierrc` 配置（如存在）
- [x] 可作为可选内置 Hook 启用/禁用
- [x] 支持将标准配置从模板分发到项目
- [x] 检测配置不一致时提示同步

## Technical Tasks

### Part 1: 配置模板管理

- [x] 创建配置模板目录 `resources/config-templates/`

  ```text
  resources/config-templates/
  ├── prettier/
  │   ├── .prettierrc           # 基础配置
  │   ├── .prettierignore       # 忽略模式
  │   └── package.json          # 依赖声明
  └── markdownlint/
      ├── .markdownlint.json    # lint 规则
      └── .markdownlintignore   # 忽略模式
  ```

- [x] 定义 Monoco 标准配置
  - `.prettierrc`: 100 列宽、2 空格缩进、无分号
  - `.markdownlint.json`: 允许 HTML、适当行长度
- [x] 实现配置同步命令

  ```bash
  monoco pretty-markdown sync      # 同步 prettier 和 markdownlint 配置到项目
  ```

### Part 2: 自动格式化 Hook

- [x] 创建 `pretty-markdown` hook 目录结构

  ```text
  src/monoco/core/hooks/builtin/pretty-markdown/
  ├── HOOK.md
  └── scripts/
      └── run.sh
  ```

- [x] 编写 `HOOK.md` 配置 (Frontmatter embedded in script)

  ```yaml
  ---
  name: pretty-markdown
  description: Lint Markdown files after save and inject issues into Agent context
  trigger: post-tool-call
  matcher:
    tool: 'WriteFile|StrReplaceFile'
    pattern: "\\.(md|mdx)$"
  timeout: 10000
  async: false
  priority: 100
  ---
  ```

- [x] 编写 `scripts/run.sh` (implemented as pretty-markdown.sh)
  - 从 stdin 解析 `tool_input.path`
  - 检查文件扩展名（仅 `.md`, `.mdx`）
  - 运行 `npx markdownlint --json <filepath>` 收集问题
  - **如无问题**：静默退出（exit 0，零输出）
  - **如有问题**：
    - 输出结构化报告到 stderr（注入 Agent 上下文）
    - 标注问题类型（格式类 vs 内容类）
    - exit 0（不阻断工作流，让 Agent 自主决策）
  - 分类规则：
    - 格式类（prettier 可修复）：MD013, MD004, MD009, MD012
    - 内容类（需 Agent 判断）：MD033, MD041, MD024, MD002, MD025

### Part 3: 配置一致性检查

- [x] 实现 `monoco pretty-markdown check` 命令
  - 检测项目配置与模板配置的差异
  - 输出 diff 报告
- [x] 可选：pre-commit hook 检查配置一致性 (deferred to future release)

### Part 4: 集成与 CLI

- [x] 注册为内置 Hook，默认禁用
- [x] 添加 `monoco pretty-markdown` 子命令
  - `monoco pretty-markdown sync` - 同步配置
  - `monoco pretty-markdown check` - 检查配置一致性
  - `monoco pretty-markdown enable` - 启用自动格式化
  - `monoco pretty-markdown disable` - 禁用自动格式化
- [x] 更新文档：配置同步和自动格式化使用指南 (see CLI help: `monoco pretty-markdown --help`)

## Dependencies

- 依赖 FEAT-0203（agenthooks 标准支持）完成后实施
- 或作为 FEAT-0203 的验证用例同步开发

## Design Decisions

### 1. Agent 自主决策模式

不同于传统 Hook 的「自动修复」或「人工确认」，本设计采用 **L3 Agentic 模式**：

- Hook **只收集信息**（lint 结果），**不决策**
- 将问题上下文 **注入 Agent 工作记忆**
- Agent 结合自身当前任务状态，**自主判断**如何处理

这种模式的优势：

- **零打扰**：无问题时完全静默
- **有上下文**：Agent 知道问题在哪、什么类型
- **可解释**：Agent 的决策过程通过工具调用链可见

### 2. 问题分类策略

| 类型       | 规则示例                         | 建议操作           |
| ---------- | -------------------------------- | ------------------ |
| **格式类** | MD013(行长度), MD004(列表缩进)   | `prettier --write` |
| **内容类** | MD033(HTML), MD041(首行标题)     | 需理解语义后修改   |
| **结构类** | MD002(一级标题), MD025(唯一标题) | Agent 判断优先级   |

### 3. 与 Feat-0203 的关系

本 Hook 是 **AgentHooks 框架的验证用例**，验证以下能力：

- `post-tool-call` 拦截
- 选择性上下文注入（有问题时才注入）
- Agent 对 Hook 输出的响应能力

## Scope

本 Issue 覆盖 Markdown 格式化的完整工作流：

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  配置模板中心    │────▶│  项目配置同步    │────▶│   Lint 检查     │
│  (monoco 内置)   │     │ (monoco config) │     │  (agent hook)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                            ┌──────────────────────────┘
                            │ 有问题时注入上下文
                            ▼
                    ┌─────────────────┐
                    │  Agent 自主决策  │
                    │  • prettier fix │
                    │  • 手动修改      │
                    │  • 延后处理      │
                    └─────────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │  一致性检查      │
                    │ (monoco check)  │
                    └─────────────────┘
```

## Review Comments

- 2026-02-20: Implementation completed. All acceptance criteria met.
