---
id: FEAT-0204
uid: ee0a36
type: feature
status: open
stage: draft
title: 'pretty-markdown: 自动格式化 Markdown 及配置同步分发'
created_at: '2026-02-20T07:17:02'
updated_at: '2026-02-20T07:17:02'
parent: EPIC-0000
dependencies: []
related: ['FEAT-0203']
domains: []
tags:
  - '#EPIC-0000'
  - '#FEAT-0204'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-20T07:17:02'
---

## FEAT-0204: pretty-markdown: 保存 Markdown 文件后自动格式化

## Objective

实现 Markdown 文件的标准化格式化，包含两个层面：

1. **自动格式化**：Agent 保存 Markdown 文件后自动 prettier 格式化
2. **配置同步**：将标准化的 prettier/markdownlint 配置分发到项目，确保团队一致性

**使用 AgentHooks 实现**：利用 `post-tool-call` 事件拦截文件保存操作，当检测到 `.md` 文件被修改时，自动触发格式化。

## Acceptance Criteria

- [ ] Agent 保存 Markdown 文件后自动 prettier 格式化
- [ ] 支持 `WriteFile` 和 `StrReplaceFile` 工具拦截
- [ ] 只处理 `.md` 和 `.mdx` 文件
- [ ] 格式化失败不阻断 Agent 工作流（记录警告日志）
- [ ] 使用项目根目录的 `.prettierrc` 配置
- [ ] 可作为可选内置 Hook 启用/禁用
- [ ] 支持将标准配置从模板分发到项目
- [ ] 检测配置不一致时提示同步

## Technical Tasks

### Part 1: 配置模板管理

- [ ] 创建配置模板目录 `resources/config-templates/`

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

- [ ] 定义 Monoco 标准配置
  - `.prettierrc`: 100 列宽、2 空格缩进、无分号
  - `.markdownlint.json`: 允许 HTML、适当行长度
- [ ] 实现配置同步命令

  ```bash
  monoco pretty-markdown sync      # 同步 prettier 和 markdownlint 配置到项目
  ```

### Part 2: 自动格式化 Hook

- [ ] 创建 `pretty-markdown` hook 目录结构

  ```text
  src/monoco/core/hooks/builtin/pretty-markdown/
  ├── HOOK.md
  └── scripts/
      └── run.sh
  ```

- [ ] 编写 `HOOK.md` 配置

  ```yaml
  ---
  name: pretty-markdown
  description: Auto-format Markdown files after save
  trigger: post-tool-call
  matcher:
    tool: 'WriteFile|StrReplaceFile'
    pattern: "\\.(md|mdx)$"
  timeout: 10000
  async: false
  priority: 100
  ---
  ```

- [ ] 编写 `scripts/run.sh`
  - 从 stdin 解析 `tool_input.path`
  - 检查文件扩展名
  - 执行 `npx prettier --write <filepath>`
  - 失败时输出警告到 stderr，但 exit 0

### Part 3: 配置一致性检查

- [ ] 实现 `monoco pretty-markdown check` 命令
  - 检测项目配置与模板配置的差异
  - 输出 diff 报告
- [ ] 可选：pre-commit hook 检查配置一致性

### Part 4: 集成与 CLI

- [ ] 注册为内置 Hook，默认禁用
- [ ] 添加 `monoco pretty-markdown` 子命令
  - `monoco pretty-markdown sync` - 同步配置
  - `monoco pretty-markdown check` - 检查配置一致性
  - `monoco pretty-markdown enable` - 启用自动格式化
  - `monoco pretty-markdown disable` - 禁用自动格式化
- [ ] 更新文档：配置同步和自动格式化使用指南

## Dependencies

- 依赖 FEAT-0203（agenthooks 标准支持）完成后实施
- 或作为 FEAT-0203 的验证用例同步开发

## Scope

本 Issue 覆盖 Markdown 格式化的完整工作流：

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  配置模板中心    │────▶│  项目配置同步    │────▶│  自动格式化执行  │
│  (monoco 内置)   │     │ (monoco config) │     │  (agent hook)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  一致性检查      │
                                                │ (monoco check)  │
                                                └─────────────────┘
```

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
