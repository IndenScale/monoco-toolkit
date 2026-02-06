---
id: FEAT-0178
uid: b27a54
type: feature
status: closed
stage: done
title: Add --debug flag to monoco sync and is_debug to hook metadata
created_at: '2026-02-04T17:26:41'
updated_at: '2026-02-04T18:13:55'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0178'
files:
- .monoco/roles/engineer.yaml
- .monoco/roles/manager.yaml
- .monoco/roles/planner.yaml
- .monoco/roles/reviewer.yaml
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- monoco/core/sync.py
- monoco/features/hooks/commands.py
- monoco/features/hooks/dispatchers/agent_dispatcher.py
- monoco/features/hooks/models.py
- monoco/features/hooks/resources/hooks/agent/after-tool-claude.sh
- monoco/features/hooks/resources/hooks/agent/after-tool-gemini.sh
- monoco/features/hooks/resources/hooks/agent/before-tool-claude.sh
- monoco/features/hooks/resources/hooks/agent/before-tool-gemini.sh
- monoco/features/hooks/universal_interceptor.py
criticality: medium
solution: implemented # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T17:26:41'
isolation:
  type: branch
  ref: FEAT-0178-add-debug-flag-to-monoco-sync-and-is_debug-to-hook
  created_at: '2026-02-04T17:26:46'
---

## FEAT-0178: Add --debug flag to monoco sync and is_debug to hook metadata

## Objective
为 monoco sync 添加 --debug flag，并为 hooks system 的元数据添加 is_debug 字段，实现 hook 级别的调试输出控制。

## Acceptance Criteria
- [x] `monoco sync --debug` 启用全局 hook debug 模式
- [x] `HookMetadata` 支持 `is_debug` 字段用于单个 hook 调试
- [x] `monoco hook run --debug` 支持运行时调试
- [x] 创建 test agent hooks (before-tool, after-tool) 验证功能

## Technical Tasks
- [x] 修改 `HookMetadata` 模型，添加 `is_debug` 字段
- [x] 修改 `monoco/core/sync.py`，添加 `--debug` flag
- [x] 修改 `monoco/features/hooks/commands.py`，添加 `--debug` flag
- [x] 更新 `ClaudeCodeDispatcher` 和 `GeminiDispatcher` 传递 debug 状态
- [x] 更新 `universal_interceptor.py` 传递 debug 环境变量
- [x] 创建 `before-tool-claude.sh` 和 `after-tool-claude.sh` test hooks
- [x] 创建 `before-tool-gemini.sh` 和 `after-tool-gemini.sh` test hooks
- [x] 删除 `CLAUDE_CODE_REMOTE` 和 `GEMINI_ENV_FILE` 环境变量检测
- [x] 改为通过输入格式自动检测 agent 类型
- [x] 改为通过 skills 目录存在性检测 agent 可用性

## Review Comments

### Self Review

1. **代码质量**: 实现遵循现有模式，修改最小化
   - `is_debug` 字段添加到 `HookMetadata`，类型为 bool，默认 False
   - `--debug` flag 添加到 `monoco sync` 和 `monoco hook run`
   - 环境变量 `MONOCO_HOOK_DEBUG` 用于运行时传递状态

2. **测试覆盖**: 创建了 test agent hooks
   - `before-tool.sh`: 工具调用前打印 debug 信息
   - `after-tool.sh`: 工具调用后打印 debug 信息
   - 两个 hook 都设置了 `is_debug: true`

3. **兼容性**:
   - 向后兼容：默认 `is_debug=False`，不影响现有功能
   - 支持 Claude Code 和 Gemini CLI 两种 provider

4. **使用方式**:
   ```bash
   # 全局启用 debug
   monoco sync --debug

   # 单个 hook 启用 debug（在 hook 文件的 Front Matter 中设置）
   is_debug: true
   ```
