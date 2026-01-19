---
id: CHORE-0008
uid: 302bb8
type: chore
status: closed
stage: done
title: 修复 monoco init 语法错误和幂等性
created_at: '2026-01-19T00:34:15'
opened_at: '2026-01-19T00:34:15'
updated_at: '2026-01-19T00:35:31'
closed_at: '2026-01-19T00:35:31'
parent: EPIC-0017
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0008'
- '#EPIC-0017'
---

## CHORE-0008: 修复 monoco init 语法错误和幂等性

## 目标

<!-- 清晰地描述“为什么”和“是什么”。关注价值。 -->
修复 `monoco init` 中的语法错误，并确保重新运行该命令时不会删除现有配置，而是确保 Hooks 已安装。

## 验收标准

<!-- 定义成功的二进制条件。 -->

- [x] `monoco init` 运行无 SyntaxError
- [x] 重新运行 `monoco init` 不会删除配置，但确保 Hooks 已安装

## 技术任务

<!-- 分解为原子步骤。使用嵌套列表表示子任务。 -->

<!-- 状态语法： -->
<!-- [ ] 待办 -->
<!-- [/] 正在进行 -->
<!-- [x] 已完成 -->
<!-- [~] 已取消 -->
<!-- - [ ] 父任务 -->
<!--   - [ ] 子任务 -->

- [x] 修复 `monoco/core/setup.py` 中的 SyntaxError
- [x] 重构 `init_cli` 以支持幂等重新运行（跳过配置覆盖，允许资源初始化）

## Review Comments

- [x] Self-Review
