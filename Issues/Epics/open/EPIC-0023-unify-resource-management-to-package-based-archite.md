---
id: EPIC-0023
uid: f8428d
type: epic
status: open
stage: doing
title: Unify Resource Management to Package-Based Architecture
created_at: '2026-01-31T17:09:08'
updated_at: '2026-01-31T17:10:10'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0023'
- '#EPIC-0000'
files: []
criticality: high
opened_at: '2026-01-31T17:09:08'
isolation:
  type: branch
  ref: feat/epic-0023-unify-resource-management-to-package-based-archite
  path: null
  created_at: '2026-01-31T17:10:11'
progress: 1/1
files_count: 0
---

## EPIC-0023: Unify Resource Management to Package-Based Architecture

## Objective
重构 Monoco 的资源管理机制，从硬编码/散乱模式迁移到统一的 **Package-Based Architecture**。
确立 "Monoco Sync" 作为核心的分发机制，将 Python 包内的资源（Prompt, Rules, Skills）动态安装/更新到用户工作区。

## Scope
- **Standard**: 定义Feature资源的目录结构规范 (`monoco/features/{module}/resources/{lang}/...`)。
- **Core**: 重构 `monoco sync` 命令，支持基于 Feature 的资源发现与注入。
- **Migration**: 将现有模块（Issue, Memo, Spike）迁移到新架构。
- **New Feature**: 实现 Glossary 模块作为架构样板。

## Key Results
- [x] 所有 Feature 资源均以 Markdown 文件形式存于 Python 包内
- [x] `monoco sync` 能够正确生成 `AGENTS.md`
    - [x] 实现明确的 `Generated` vs `User Maintained` 分割线 (e.g., `<!-- MONOCO_GENERATED_START -->`)
    - [x] 解决 Header Level 冲突，实现注入内容的动态标题降级
    - [x] 根据 user workspace `i18n.source_lang` 仅生成单一语言内容，避免中英重复
- [x] 移除所有 Python 代码中的硬编码 Prompt 字符串
- [x] Glossary 模块成功实现并分发

## Technical Tasks
- [x] Design & Implement `monoco.core.resource` package
- [x] Update `monoco sync` to use new resource discovery logic
- [x] Execute FEAT-0126 (Glossary Module) as pilot
- [x] Refactor existing features (Issue, Memo, Spike, Agent) to new architecture

## Review Comments
- Initial draft for the resource management unification epic.
- Implementation confirmed complete. Package-based architecture is active. Core functionality (`monoco sync`, resource injection) is verified. All key modules (Issue, Memo, Spike, Agent, Glossary) have been migrated to use `resources/` directory structure.
