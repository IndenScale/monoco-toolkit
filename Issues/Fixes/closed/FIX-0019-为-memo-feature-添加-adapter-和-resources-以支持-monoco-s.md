---
id: FIX-0019
uid: 65f97f
type: fix
status: closed
stage: done
title: 为 memo feature 添加 adapter 和 resources 以支持 monoco sync
created_at: '2026-01-29T23:07:58'
updated_at: '2026-01-29T23:07:58'
parent: EPIC-0000
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0019'
files:
- monoco/features/memo/adapter.py
- monoco/features/memo/__init__.py
- monoco/features/memo/resources/zh/SKILL.md
- monoco/features/memo/resources/zh/AGENTS.md
- monoco/core/registry.py
opened_at: '2026-01-29T23:07:58'
---

## FIX-0019: 为 memo feature 添加 adapter 和 resources 以支持 monoco sync

### 问题描述

`memo` feature 目前缺少与 `monoco sync` 系统的集成：

1. **缺少 `adapter.py`**: 没有实现 `MonocoFeature` 接口，导致 `monoco sync` 无法识别 memo 功能
2. **缺少 `resources/` 目录**: 没有 `SKILL.md` 和 `AGENTS.md` 文件，无法向 Agent 提供 memo 功能的使用指南

对比其他功能（如 `i18n`, `issue`, `spike`），它们都有完整的 adapter 和 resources 结构。

### 影响

- 运行 `monoco sync` 时，memo 功能不会被同步到 Agent 配置中
- Agent 无法通过 `monoco sync` 获得 memo 的使用指南

### 验收标准

- [x] 创建 `monoco/features/memo/adapter.py`，实现 `MonocoFeature` 接口
- [x] 创建 `monoco/features/memo/resources/zh/SKILL.md`，包含 memo 技能文档
- [x] 创建 `monoco/features/memo/resources/zh/AGENTS.md`，包含 Agent 提示
- [x] 更新 `monoco/features/memo/__init__.py`，导出 `MemoFeature`
- [x] 验证 `monoco sync` 能正确同步 memo 功能到 AGENTS.md/GEMINI.md/CLAUDE.md

### 技术任务

- [x] 创建 `adapter.py`
  - 实现 `MemoFeature` 类，继承 `MonocoFeature`
  - 实现 `initialize` 方法
  - 实现 `integrate` 方法，返回 `IntegrationData`
- [x] 创建 `resources/zh/SKILL.md`
  - 描述 memo 功能的用途
  - 记录命令：`monoco memo add`, `monoco memo list`, `monoco memo open`
  - 与 Issue 区分说明
- [x] 创建 `resources/zh/AGENTS.md`
  - 简洁的 Agent 提示，包含命令速查
- [x] 更新 `__init__.py`
  - 导出 `MemoFeature` 类

## Review Comments

- [x] Verified by Agent.
