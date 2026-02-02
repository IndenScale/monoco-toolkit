---
id: FEAT-0138
uid: 5d2c5f
type: feature
status: open
stage: doing
title: 实现代理会话持久化
created_at: '2026-02-01T20:44:08'
updated_at: '2026-02-02T11:21:24'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0138'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-01T20:44:08'
---

## FEAT-0138: 实现代理会话持久化

## 背景与目标

实现代理会话持久化功能，确保会话状态在系统重启后不会丢失。当前会话信息仅保存在内存中，当守护进程或系统重启时，所有进行中的会话状态都会丢失。本功能需要扩展 Session 模型，添加进程 ID 字段，实现 SessionManager 的持久化存储（加载/保存到 `.monoco/sessions/*.json`），并支持本地（所有者）与远程（观察者）两种模式，确保 Daemon 能够列出由 CLI 子任务创建的会话。

## 目标
<!-- 清晰描述"为什么"和"做什么"。聚焦于价值。 -->

## 验收标准
<!-- 定义成功的二元条件。 -->
- [ ] 标准 1

## 技术任务
<!-- 分解为原子步骤。使用嵌套列表表示子任务。 -->

- [ ] 更新 `Session` 模型，添加 `pid` 字段
- [ ] 实现 `SessionManager` 持久化（加载/保存到 `.monoco/sessions/*.json`）
- [ ] 更新 `RuntimeSession` 以支持本地（所有者）与远程（观察者）两种模式
- [ ] 确保 `Worker` 在 Session 模型中更新 `pid`
- [ ] 验证 Daemon 可以列出由 CLI 子任务创建的会话

- [ ] 任务 1

## 评审意见


