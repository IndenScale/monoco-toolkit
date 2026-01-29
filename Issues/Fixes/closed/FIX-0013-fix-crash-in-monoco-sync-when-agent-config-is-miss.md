---
id: FIX-0013
parent: EPIC-0000
uid: 5aeb94
type: fix
status: closed
stage: done
title: 修复 monoco sync 在缺少 agent 配置时的崩溃与残余代码清理
created_at: '2026-01-23T19:32:33'
opened_at: '2026-01-23T19:32:33'
updated_at: '2026-01-23T19:38:42'
closed_at: '2026-01-23T19:38:42'
solution: implemented
isolation:
  type: branch
  ref: feat/fix-0013-fix-crash-in-monoco-sync-when-agent-config-is-miss
  created_at: '2026-01-23T19:32:37'
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0013'
files: []
---

## FIX-0013: 修复 monoco sync 在缺少 agent 配置时的崩溃与残余代码清理

## Objective
修复 `monoco sync` 命令运行时出现的 `AttributeError: 'MonocoConfig' object has no attribute 'agent'` 错误。该错误是由于 `MonocoConfig` 模型中缺少 `agent` 字段定义导致的。

## Acceptance Criteria
- [x] `MonocoConfig` 模型中包含 `agent` 字段。
- [x] `monoco sync` 在没有手动配置 `agent` 字段的情况下也能正常运行（使用默认值）。
- [x] 成功同步指令与技能。

## Technical Tasks
- [x] 在 `monoco/core/config.py` 中定义 `AgentConfig` Pydantic 模型。
- [x] 将 `agent` 字段添加到 `MonocoConfig` 中。
- [x] 验证 `monoco sync` 修复后的运行情况。

## Review Comments
修复已验证。通过在 `MonocoConfig` 中添加 `agent` 字段并提供默认工厂，确保了在所有环境下 `config.agent` 均可访问。
