---
id: FEAT-0173
uid: '191169'
type: feature
status: open
stage: doing
title: 实现通用 Hooks 注册与安装机制
created_at: '2026-02-04T13:02:30'
updated_at: 2026-02-04 13:02:56
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0173'
files: []
criticality: medium
solution: null
opened_at: '2026-02-04T13:02:30'
isolation:
  type: branch
  ref: feat/feat-0173-实现通用-hooks-注册与安装机制
  path: null
  created_at: '2026-02-04T13:02:56'
---

## FEAT-0173: 实现通用 Hooks 注册与安装机制

## 背景
目前 Monoco 仅支持基础的 Git Hooks（基于文件名识别），但随着功能扩展，我们需要支持多 Agent 框架（如 Claude Code, Gemini CLI）以及 IDE 场景下的钩子。原有的管理方式无法承载复杂的元数据需求（如类型细分、平台适配、动态开启等）。

## 目标
实现一套基于脚本注释 Front Matter 的通用 Hooks 注册、解析与安装机制，并将其深度集成到 `monoco sync` 流程中。

## 验收标准
- [ ] 实现 `UniversalHookManager` 核心类，取代单一的 `GitHooksManager`。
- [ ] 支持从 Hooks 脚本（.sh, .py）的头部注释中解析 YAML Front Matter 元数据。
- [ ] 支持按类型（`git`, `agent`, `ide`）及其细分属性（如 `agent_type: claude-code`）分发归类。
- [ ] 增强 `monoco sync` 命令，实现自动扫描 Toolkit 特性库中的 Hooks 并安装至指定目标。
- [ ] 确保与现有 Git Hooks 管理逻辑（如 Marker 标记、权限修改）完全兼容。

## 技术任务
- [ ] **前期调研**:
  - [x] 完成 Agent Hooks (Claude Code, Gemini CLI) 调查报告。
  - [x] 完善 Git Hooks 标准化方案方案。
  - [x] 调研 IDE Hooks 集成可行性。
- [ ] **建模与解析**:
  - [ ] 定义 `HookMetadata` Pydantic 模型。
  - [ ] 实现 `HookParser`，支持多种注释风格（`#`, `//`, `--`）下的 YAML 提取。
- [ ] **管理层重构**:
  - [ ] 在 `monoco.features.hooks.core` 中重构管理逻辑。
  - [ ] 实现多平台分发器（Dispatcher），支持 `.git/hooks/` 和 `.claude/hooks/` 等目标。
- [ ] **集成与分发**:
  - [ ] 更新 `monoco.core.sync.py`，在 `sync_command` 中插入 Hook 同步生命周期。
  - [ ] 确保 `monoco uninstall` 对注入的 Hooks 进行正确清理。
- [ ] **测试验证**:
  - [ ] 编写集成测试，验证脚本元数据解析、优先级排序及文件写入的正确性。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
