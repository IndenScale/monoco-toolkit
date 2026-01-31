---
id: FEAT-0126
uid: cf806e
type: feature
status: closed
stage: done
title: Implement Glossary Feature Module
created_at: '2026-01-31T16:57:27'
updated_at: '2026-01-31T17:27:10'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0126'
files:
- Issues/Epics/open/EPIC-0023-unify-resource-management-to-package-based-archite.md
criticality: medium
opened_at: '2026-01-31T16:57:27'
closed_at: '2026-01-31T17:27:10'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0126-implement-glossary-feature-module
  created_at: '2026-01-31T16:57:51'
---

## FEAT-0126: Implement Glossary Feature Module

## Objective
实现 `monoco.features.glossary` 模块，将核心术语（如 Distro, Kernel, Unit）和操作法则作为标准能力注入到 Agent 的上下文中。
这将替代手动的 `GLOSSARY.md` 文件维护，通过 `monoco sync` 机制确保所有 Agent 始终拥有最新的架构认知。

## Acceptance Criteria
- [x] 创建 `monoco/features/glossary` 模块结构
- [x] 实现 `GlossaryManager` 负责管理和渲染术语定义
    - [x] 渲染逻辑需尊守 `i18n.source_lang` 配置，仅输出一种语言
    - [x] 渲染逻辑需动态调整 Markdown Header Level，避免破坏宿主文件大纲
- [x] 定义 `monoco_glossary` Skill (包含术语表和核心法则)
- [x] 注册 Feature 并集成到 `monoco sync` 流程中
- [x] 验证运行 `monoco sync` 后，`GEMINI.md` 或 `AGENTS.md` 正确包含了 Glossary 内容
    - [x] 验证内容位于自动生成区域内，且未覆盖用户自定义内容
- [x] 移除旧的 `.agent/GLOSSARY.md` 文件

## Technical Tasks
- [x] 初始化 `monoco/features/glossary` (core.py, config.py)
- [x] 创建 `.agent/skills/monoco_glossary/SKILL.md` 模板
- [x] 实现 `get_context_prompt` 接口，整合 Architecture Metaphor 和 Operational Laws
- [x] 更新 `monoco/features/__init__.py` 进行注册
- [x] 编写测试用例验证注入逻辑



## Review Comments

- **Completed**: 2026-01-31
- **Summary**: Implemented Glossary feature module and integrated with `monoco sync`.
  - Created `monoco/features/glossary` package.
  - Implemented `GlossaryManager` with dynamic header demotion and `i18n.source_lang` support.
  - Updated `monoco sync` to inject managed blocks with explicit delimiters.
  - Verified generation of `AGENTS.md` with correct content and structure.
  - Distributed `monoco_glossary` skill via sync.
