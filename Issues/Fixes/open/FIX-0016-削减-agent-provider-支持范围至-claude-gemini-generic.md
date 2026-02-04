---
id: FIX-0016
uid: 342e6c
type: fix
status: open
stage: review
title: 削减 agent provider 支持范围至 Claude+Gemini+Generic
created_at: '2026-02-04T22:05:57'
updated_at: '2026-02-04T22:07:12'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0016'
files:
- monoco/core/integrations.py
- monoco/core/sync.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T22:05:57'
isolation:
  type: branch
  ref: FIX-0016-削减-agent-provider-支持范围至-claude-gemini-generic
  created_at: '2026-02-04T22:06:00'
---

## FIX-0016: 削减 agent provider 支持范围至 Claude+Gemini+Generic

## Objective
削减 agent provider 支持范围，从 6 个减少到 3 个（Claude Code + Gemini CLI + Generic Agent），降低维护成本。

## Acceptance Criteria
- [x] 从 `DEFAULT_INTEGRATIONS` 中移除 Cursor 和 Qwen
- [x] 从 `agent_dispatchers` 中移除非核心 provider
- [x] 归档 `.qwen/` 目录
- [x] 更新 fallback defaults 列表

## Technical Tasks
- [x] 修改 `monoco/core/integrations.py` - 移除 cursor/qwen/kimi 配置
- [x] 修改 `monoco/core/sync.py` - 清理 dispatchers 和 defaults
- [x] 归档 `.qwen/` 到 `.archives/legacy/`
- [x] 手动更新 files 字段

## Review Comments

### 变更总结

1. **integrations.py**: 从 6 个 provider 削减至 3 个
   - 保留: `claude`, `gemini`, `agent`
   - 移除: `cursor`, `qwen`, `kimi` (kimi 使用 generic agent)

2. **sync.py**: 添加注释说明仅支持 Claude Code 和 Gemini CLI

3. **归档**: `.qwen/` 目录已移动到 `.archives/legacy/.qwen/`

### 影响分析
- Cursor 用户：需手动使用 `.agent/workflows/` 中的工作流
- Qwen 用户：可迁移到 Generic Agent (`AGENTS.md` + `.agent/`)
- Kimi 用户：无影响，继续使用 `AGENTS.md`
