---
id: FEAT-0076
uid: dbecda
type: feature
status: closed
stage: done
title: Implement Monoco Language Server
created_at: "2026-01-15T20:57:14"
opened_at: "2026-01-15T20:57:14"
updated_at: "2026-01-15T20:57:14"
dependencies: []
related: []
solution: >
  Implemented a dual-project structure (client/server) within `extensions/vscode`.
  The core logic was migrated to a TypeScript-based LSP server that validates Markdown frontmatter against JSON Schemas exported from the Python core.
  This decoupled architecture removes the runtime dependency on Python for basic editor features and improves performance.
tags: []
---

## FEAT-0076: 实现 Monoco 语言服务器 (TypeScript)

## 目标 (Objective)

将 Monoco Issue System 当前僵化的 "Action Proxy" 模式替换为灵活、基于校验驱动的 **Language Server Protocol (LSP)** 架构。
**技术决策**：为了确保插件的轻量化、高性能和易分发性，决定采用 **TypeScript** 技术栈 (`vscode-languageserver`) 实现 LSP，与 VS Code 插件生态保持原生一致。

## 架构上下文 (Context & Architecture)

- **Native LSP (TypeScript)**: `extensions/vscode` 目录将被重构为 Monorepo 结构，包含 `client` 和 `server` 两个子项目。Server 运行在 Node.js 环境中，直接解析 Issue 文件。
- **Schema Sync (协议一致性)**:
  - **Python Core**: 依然作为业务逻辑的 SSOT (Single Source of Truth)。
  - **JSON Schema**: 所有的 Pydantic Models (Issue, Epic, Feature) 将自动导出为 JSON Schema。
  - **TS Validator**: LSP Server 加载 JSON Schema 进行校验，确保编辑器与 CLI 的逻辑一致。
- **Decoupling**: 编辑器体验完全独立于 Python 环境，无需配置 Python 解释器即可获得基本的语法高亮和校验。

## 验收标准 (Acceptance Criteria)

1. **分发友好**: 插件打包后为单一 `.vsix`，不依赖外部 Python 环境。
2. **诊断 (Diagnostics)**:
   - 基于 JSON Schema 校验 Frontmatter 结构 (字段类型、枚举值)。
   - 自定义逻辑校验 (Logic Validation): 如断链检测 (Link Integrity)。
3. **能力对齐**:
   - 支持 `completion` (智能补全状态和 ID)。
   - 支持 `definition` (跳转到 Parent/Dependency 文件)。
   - 支持 `codeAction` (状态机流转快速修复)。
4. **Schema 同步**: 提供脚本从 `monoco.core` 导出 Schema 供 LSP 使用。

## 技术任务 (Technical Tasks)

### 1. 项目结构重构

- [x] 在 `extensions/vscode` 下建立结构 (`client` / `server`)。
- [x] 初始化 `server` 目录，安装 `vscode-languageserver`, `vscode-languageserver-textdocument`。
- [x] 配置 `server` 的 `tsconfig.json` 和构建脚本。

### 2. 协议同步 (Schema Pipeline)

- [x] 创建脚本 `scripts/export_schema.py`: 从 `monoco.features.issue.models` 导出 JSON Schema。
- [x] 将生成的 schema 放置在 `extensions/vscode/server/src/schema/` 中。

### 3. LSP Server 实现 (TypeScript)

- [x] **初始化**: 实现 `connection.onInitialize`。
- [x] **文档同步**: 使用 `TextDocuments` 管理全量/增量文档同步。
- [x] **诊断**: 实现 `validateTextDocument` 函数，解析 YAML Frontmatter 并对照 Schema 校验。
- [x] **图谱构建**: 实现简易的 Workspace 扫描器 (用于 ID 索引和跳转)。

### 4. Client 集成

- [x] 修改 `client/src/extension.ts` 以启动 Server (`LanguageClient`).
- [x] 移除旧的 `issueCommands.ts` 和相关命令注册。

### 5. 功能迁移

- [x] 移植 Status/Stage 校验逻辑到 TypeScript。
- [x] 实现 ID 索引逻辑 (用于 Auto-completion 和 Goto Definition)。
