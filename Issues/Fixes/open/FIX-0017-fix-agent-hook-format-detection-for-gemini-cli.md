---
id: FIX-0017
uid: 32d840
type: fix
status: open
stage: review
title: Fix agent hook format detection for Gemini CLI
created_at: '2026-02-04T23:23:50'
updated_at: '2026-02-04T23:26:57'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0017'
files:
- monoco/features/hooks/universal_interceptor.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T23:23:50'
isolation:
  type: branch
  ref: FIX-0017-fix-agent-hook-format-detection-for-gemini-cli
  created_at: '2026-02-04T23:23:56'
---

## FIX-0017: Fix agent hook format detection for Gemini CLI

## Objective
修复 `UniversalInterceptor` 无法正确识别 Gemini CLI Hook 输入格式的问题。

## Acceptance Criteria
- [x] `GeminiAdapter` 能够正确识别包含 `hook_event_name` 字段的输入。
- [x] `GeminiAdapter` 能够正确识别并翻译 `BeforeModel`, `AfterModel`, `BeforeToolSelection` 和 `Notification` 事件。
- [x] `GeminiAdapter` 能够兼容 `tool_name` 和 `tool_input` 字段名。

## Technical Tasks
- [x] 分析 Gemini CLI 实际发送的数据格式。
- [x] 更新 `GeminiAdapter.EVENT_MAP` 补全缺失事件。
- [x] 更新 `GeminiAdapter.detect` 和 `translate_input` 支持备选字段。
- [x] 验证修复后的 Interceptor 是否能正确处理新旧两种格式。

## Review Comments
修复了 Gemini CLI 格式识别问题，已通过模拟输入验证。
