---
id: FIX-0023
uid: 1d7bf3
type: fix
status: closed
stage: done
title: 修复 monoco courier 无法接收 dingtalk 消息的问题
created_at: '2026-02-07T21:21:44'
updated_at: '2026-02-07T22:56:24'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0023'
files:
- src/monoco/features/courier/api.py
- src/monoco/features/courier/commands.py
criticality: high
solution: implemented
opened_at: '2026-02-07T21:21:44'
closed_at: '2026-02-07T22:56:24'
isolation:
  type: branch
  ref: FIX-0023-修复-monoco-courier-无法接收-dingtalk-消息的问题
  created_at: '2026-02-07T21:21:48'
---

## FIX-0023: 修复 monoco courier 无法接收 dingtalk 消息的问题

## Objective
修复 monoco courier 无法接收 dingtalk 消息的问题。

CourierAPIHandler 类缺少 `_dingtalk_adapter` 类变量声明，导致在调用 `get_dingtalk_adapter()` 时抛出 `AttributeError`，无法处理 DingTalk webhook 消息。

## Acceptance Criteria
- [x] 修复 `_dingtalk_adapter` 类变量缺失问题
- [x] 添加 `monoco courier logs clean` 命令用于清理日志

## Technical Tasks
- [x] 在 CourierAPIHandler 中添加 `_dingtalk_adapter: Optional["DingtalkAdapter"] = None` 声明
- [x] 重构 logs 命令为子命令组（show/clean）
- [x] 实现 logs clean 功能，支持 --all 和 --force 选项

## Review Comments
- 代码审查通过，修复了关键 bug
- 新增 logs clean 功能增强了运维能力
