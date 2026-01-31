---
id: FEAT-0126
uid: cf806e
type: feature
status: open
stage: doing
title: Implement Glossary Feature Module
created_at: '2026-01-31T16:57:27'
updated_at: '2026-01-31T17:10:19'
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
- [ ] 创建 `monoco/features/glossary` 模块结构
- [ ] 实现 `GlossaryManager` 负责管理和渲染术语定义
- [ ] 定义 `monoco_glossary` Skill (包含术语表和核心法则)
- [ ] 注册 Feature 并集成到 `monoco sync` 流程中
- [ ] 验证运行 `monoco sync` 后，`GEMINI.md` 或 `AGENTS.md` 正确包含了 Glossary 内容
- [ ] 移除旧的 `.agent/GLOSSARY.md` 文件

## Technical Tasks
- [ ] 初始化 `monoco/features/glossary` (core.py, config.py)
- [ ] 创建 `.agent/skills/monoco_glossary/SKILL.md` 模板
- [ ] 实现 `get_context_prompt` 接口，整合 Architecture Metaphor 和 Operational Laws
- [ ] 更新 `monoco/features/__init__.py` 进行注册
- [ ] 编写测试用例验证注入逻辑



## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
