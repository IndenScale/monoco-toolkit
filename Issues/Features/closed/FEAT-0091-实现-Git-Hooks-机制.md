---
id: FEAT-0091
uid: c64e73
type: feature
status: closed
stage: done
title: 实现 Git Hooks 机制
created_at: '2026-01-19T00:27:17'
opened_at: '2026-01-19T00:27:17'
updated_at: '2026-01-19T00:30:01'
closed_at: '2026-01-19T00:30:01'
parent: EPIC-0017
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0017'
- '#FEAT-0091'
---

## FEAT-0091: 实现 Git Hooks 机制

## 目标

<!-- 清晰地描述“为什么”和“是什么”。关注价值。 -->
为 Monoco 提供自动化的 Git Hooks 安装和管理功能。

## 验收标准

<!-- 定义成功的二进制条件。 -->

- [x] 工作区初始化时创建 .git/hooks 脚本
- [x] CLI 初始化时创建 .git/hooks 脚本
- [x] Hooks 可通过 workspace.yaml 配置

## 技术任务

- [x] 在 `monoco/core/config.py` 中定义 `HooksConfig`
- [x] 在 `monoco/core/hooks.py` 中实现 `install_hooks`
- [x] 将 Hook 安装集成到 `monoco/core/setup.py` (CLI Init)
- [x] 将 Hook 安装集成到 `monoco/cli/workspace.py` (Workspace Init)

## Review Comments

- [x] Self-Review
