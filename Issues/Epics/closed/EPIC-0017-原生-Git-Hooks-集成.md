---
id: EPIC-0017
uid: 89dd60
type: epic
status: closed
stage: done
title: 原生 Git Hooks 集成
created_at: '2026-01-19T00:27:09'
opened_at: '2026-01-19T00:27:09'
updated_at: '2026-01-19T14:30:34'
closed_at: '2026-01-19T14:30:34'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0017'
files: []
progress: 4/4
files_count: 0
parent: EPIC-0000
---

## EPIC-0017: 原生 Git Hooks 集成

## 目标

<!-- 清晰地描述“为什么”和“是什么”。关注价值。 -->

实现 Monoco 的原生 Git Hooks 集成，以自动化工作流（如提交前的 Issue 检查）。

## 验收标准

- [x] 能够在初始化时自动安装 Hooks
- [x] Hooks 可以触发 `monoco issue lint`

## 技术任务

- [x] 实现 Git Hooks 机制

## Review Comments

- Git Hooks 安装逻辑已集成至 `monoco init` 过程。
- 默认配置包含 `pre-commit` 钩子，自动执行 `monoco issue lint --recursive`。
- `monoco.core.hooks` 模块负责物理注入 `.git/hooks` 脚本。
