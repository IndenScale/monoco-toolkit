---
id: CHORE-0043
uid: 89c45c
type: chore
status: open
stage: draft
title: 重构 open 和 close 命令以支持完整的生命周期钩子
created_at: '2026-02-05T10:19:56'
updated_at: '2026-02-05T10:19:56'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0043'
- '#EPIC-0000'
files: []
criticality: low
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-05T10:19:56'
---

## CHORE-0043: 重构 open 和 close 命令以支持完整的生命周期钩子

## 目标
重构 `open` 和 `close` 命令，为其提供完整的生命周期钩子实现。当前这两个命令虽然通过 `HookContextManager` 支持 pre/post 钩子调用，但缺乏实际的 built-in 钩子逻辑。

## 现状分析

### 已实现部分
1. **HookContextManager 集成**: `commands.py:225-271`(open) 和 `:465-684`(close) 已使用 `HookContextManager` 包装
2. **事件定义**: `hooks/models.py:19-46` 已定义 `PRE_OPEN`, `POST_OPEN`, `PRE_CLOSE`, `POST_CLOSE` 事件
3. **事件映射**: `hooks/models.py:275-283` 已将命令映射到对应事件对

### 缺失部分
1. **无 built-in 钩子实现**: `hooks/builtin/__init__.py:247-302` 中**没有**为 open/close 注册任何钩子
2. **钩子行为未定义**: 未明确 pre-open/post-open/pre-close/post-close 应该执行什么操作

## 验收标准
- [ ] 为 `PRE_OPEN`/`POST_OPEN` 实现 built-in 钩子，支持状态变更验证
- [ ] 为 `PRE_CLOSE`/`POST_CLOSE` 实现 built-in 钩子，支持关闭前的资源检查
- [ ] 钩子优先级设计合理（pre: 10, post: 100）
- [ ] 添加 `--dry-run` 选项支持在 close 前预览钩子执行结果
- [ ] 所有钩子遵循现有的 `IssueHookResult` 协议（allow/warn/deny）

## 技术任务

### Phase 1: 设计钩子行为
- [ ] 定义 `pre_open_hook`: 检查 issue 是否可被重新打开（如：是否已被 archive）
- [ ] 定义 `post_open_hook`: 状态变更后通知（如：记录日志、触发 sync）
- [ ] 定义 `pre_close_hook`: 关闭前最终检查（如：验证 stage 合规性、检查未提交变更）
- [ ] 定义 `post_close_hook`: 关闭后清理（如：清理缓存、触发归档流程）

### Phase 2: 实现 Built-in Hooks
- [ ] 在 `hooks/builtin/open_hooks.py` 实现 pre_open_hook 和 post_open_hook
- [ ] 在 `hooks/builtin/close_hooks.py` 实现 pre_close_hook 和 post_close_hook
- [ ] 在 `hooks/builtin/__init__.py:register_all_builtins()` 注册新钩子

### Phase 3: 增强命令选项
- [ ] 为 `close` 命令添加 `--dry-run` 选项（预览模式）
- [ ] 优化 `--debug-hooks` 输出格式，显示每个钩子的执行时间和结果

### Phase 4: 测试与文档
- [ ] 为 open/close 钩子编写单元测试
- [ ] 更新 `docs/hooks.md` 文档，说明 open/close 钩子的行为

## Review Comments
待审查。
