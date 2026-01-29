---
id: FIX-0010
parent: EPIC-0000
uid: 0f8174
type: fix
status: closed
stage: done
title: 从 setup 中移除已弃用的 agent 模块引用
created_at: '2026-01-19T00:37:20'
opened_at: '2026-01-19T00:37:20'
updated_at: '2026-01-19T00:38:05'
closed_at: '2026-01-19T00:38:05'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0010'
---

## FIX-0010: 从 setup 中移除已弃用的 agent 模块引用

## 目标

<!-- 清晰地描述“为什么”和“是什么”。关注价值。 -->
解决 `monoco init` 时由于引用已不存在的模块而产生的警告。

## 验收标准

<!-- 定义成功的二进制条件。 -->

- [x] `monoco init` 不再提示缺失模块的警告

## 技术任务

- [x] 从 `monoco/core/setup.py` 中移除对 `monoco.features.agent.core` 的导入

## Review Comments

- [x] Self-Review
