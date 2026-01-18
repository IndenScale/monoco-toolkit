---
id: EPIC-0016
uid: cc3c36
type: epic
status: open
stage: draft
title: LSP Cross-Project Navigation Architecture
created_at: "2026-01-17T10:33:08"
opened_at: "2026-01-17T10:33:08"
updated_at: "2026-01-17T10:33:08"
dependencies: []
related: []
tags: []
---

## EPIC-0016: LSP Cross-Project Navigation Architecture

## Objective

在 Monoco Workspace 内实现 "跨项目导航" (Go-to-Definition)。这将允许用户使用 `[[Project::IssueID]]` 语法在不同项目（例如从 `Toolkit` 到 `IndenScale`）的 Issue 之间无缝跳转。

这需要对 `monoco.features.issue` 模块进行底层升级，以支持 **细粒度位置感知 (Fine-grained Location Awareness)** (Spans) 和 **全工作区符号索引 (Workspace-wide Symbol Indexing)**。

## Architecture Design

### 1. 领域层 (Domain Layer): Span-Aware Parser

当前的 `ContentBlock` 仅追踪行级范围。我们需要引入 `Span` 概念来定位行内的特定 Token。

```python
class Span(BaseModel):
    type: str  # 'wikilink', 'issue_id', 'checkbox', 'yaml_key'
    range: Range # start/end (line, char)
    content: str
    metadata: Dict[str, Any]
```

这是实现以下功能的基础:

- **语义高亮 (Semantic Tokens)**: 精确的语法高亮。
- **定义跳转 (Definition)**: `[[...]]` 的精确点击目标。
- **悬停提示 (Hover)**: 鼠标悬停时的上下文元数据。

### 2. 服务层 (Service Layer): Workspace Symbol Index

增强现有的 `IssueValidator` 或创建一个新的 `WorkspaceService` 来维护全局查找表:

- **注册表 (Registry)**: `Map<IssueID, IssueLocation>`
- **作用域感知 (Scope Awareness)**: 解析 `ID` (本地) vs `Project::ID` (全局)。
- **缓存 (Caching)**: 高效处理多项目工作区，避免每次按键都重新解析所有内容。

### 3. 应用层 (Application Layer): LSP Adapters

实现专用的 LSP 请求适配器，将请求委托给领域层:

- `DefinitionAdapter`: `textDocument/definition` -> `Parser.find_span_at(pos)` -> `Resolver.resolve(span)`。
- `SemanticTokensAdapter`: `textDocument/semanticTokens/full` -> `Parser.parse(doc).to_tokens()`。

## Acceptance Criteria

- [ ] **解析器升级**: `MarkdownParser` 生成包含详细 `spans` 的 `blocks`。
- [ ] **跨项目解析**: 能够将 `[[OtherProject::FEAT-123]]` 解析到正确的文件路径。
- [ ] **LSP 定义**: `monoco issue lsp` 正确处理 `textDocument/definition` 请求。
- [ ] **Extension 逻辑**: VS Code Extension 将 "Go to Definition" 路由到 CLI (瘦客户端模式)。

## Technical Tasks

- [ ] **Design**: 定义 `Span` 模型并更新 `ContentBlock`。
- [ ] **Core**: 重构 `MarkdownParser` 以提取 Spans (基于正则)。
- [ ] **Core**: 实现 `WorkspaceSymbolIndex` (扩展 `linter.py` 逻辑)。
- [ ] **LSP**: 在 `monoco.features.issue.lsp` 中实现 `DefinitionProvider`。
- [ ] **Test**: 添加 Parser 的回归测试和跨项目解析的新测试。
