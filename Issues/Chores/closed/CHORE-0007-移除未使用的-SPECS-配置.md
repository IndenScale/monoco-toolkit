---
id: CHORE-0007
uid: b2be9a
type: chore
status: closed
stage: done
title: 移除未使用的 SPECS 配置
created_at: '2026-01-19T00:27:17'
opened_at: '2026-01-19T00:27:17'
updated_at: '2026-01-19T00:28:18'
closed_at: '2026-01-19T00:28:18'
parent: EPIC-0017
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0007'
- '#EPIC-0017'
---

## CHORE-0007: 移除未使用的 SPECS 配置

## 目标

<!-- 清晰地描述“为什么”和“是什么”。关注价值。 -->
清理代码库中已弃用的 `SPECS` 相关配置。

## 验收标准

<!-- 定义成功的二进制条件。 -->

- [x] 代码库配置中不再有 `SPECS` 引用

## 技术任务

<!-- 分解为原子步骤。使用嵌套列表表示子任务。 -->

<!-- 状态语法： -->
<!-- [ ] 待办 -->
<!-- [/] 正在进行 -->
<!-- [x] 已完成 -->
<!-- [~] 已取消 -->
<!-- - [ ] 父任务 -->
<!--   - [ ] 子任务 -->

- [x] 从 `monoco/core/config.py` 中移除 `specs`
- [x] 从 `monoco/core/setup.py` 中移除 `specs`
- [x] 从 `monoco/cli/workspace.py` 中移除 `specs`

## Review Comments

- [x] Self-Review
