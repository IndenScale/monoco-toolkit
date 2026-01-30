---
id: FEAT-0120
uid: 3a9b1c
type: feature
status: closed
stage: done
title: Implement Agent Session Lifecycle Hooks
created_at: '2026-01-30T16:55:00'
updated_at: '2026-01-30T17:48:20'
parent: EPIC-0022
dependencies: []
related: []
domains:
- Guardrail
tags:
- '#FEAT-0120'
- '#EPIC-0022'
files:
- monoco/core/hooks/__init__.py
- monoco/core/hooks/base.py
- monoco/core/hooks/context.py
- monoco/core/hooks/registry.py
- monoco/core/hooks/builtin/__init__.py
- monoco/core/hooks/builtin/git_cleanup.py
- monoco/core/hooks/builtin/logging_hook.py
- monoco/features/scheduler/session.py
- monoco/features/scheduler/manager.py
- monoco/core/config.py
- tests/core/hooks/test_base.py
- tests/core/hooks/test_context.py
- tests/core/hooks/test_registry.py
- tests/core/hooks/test_git_cleanup.py
- tests/core/hooks/test_logging_hook.py
criticality: medium
opened_at: '2026-01-30T16:55:00'
closed_at: '2026-01-30T17:48:20'
solution: implemented
---

## FEAT-0120: Implement Agent Session Lifecycle Hooks

## 目标 (Objective)
为 Agent Session 实现生命周期钩子机制，特别是在 Session 结束时 (Teardown/Cleanup) 的自动化处理。
旨在解决"Agent 完成任务后环境残留"的问题，确保每次 Session 结束时，工作区都能恢复到干净、预期的状态（如切回主分支、删除临时分支）。

## 架构决策 (Architecture Decision)

### 背景
在设计 Agent Hook System 时，考虑了以下方案：

1. **CLI 工具的 Agent Hooks**
   - 问题：各工具（Kimi CLI, Claude Code, Cursor Agent 等）的 Hook 机制是私有特性，生态碎片化严重
   - 结论：无法依赖外部工具的 Hook 机制

2. **Git Hooks**
   - 问题：Git Hooks 基于 Git 事件（pre-commit, post-checkout 等），与 Agent Session 的生命周期不匹配
   - 结论：无法满足 Session 级别的清理需求

3. **Monoco Native Hook System** ⭐ 选定方案
   - 优势：统一的生命周期管理，与 Session 状态紧密耦合
   - 适用场景：Reviewer 分支清理、日志记录、指标采集等

### 决策
采用 **Monoco Native Hook System**，实现与具体 Agent 工具无关的、基于 Session 生命周期的钩子机制。

## 核心需求 (Core Requirements)
1.  **Reviewer Cleanup**:
    - 在 Reviewer Agent 结束会话前，必须确保当前 git HEAD 已切回 `main` 分支。
    - 必须确保本次 Session 关联的 Issue 分支（如果已合并）被安全删除。
2.  **Hook System**:
    - 在 `monoco/features/scheduler/session.py` 中实现 `on_session_start` 和 `on_session_end` 钩子接口。
    - 支持通过配置文件（`monoco.yml`）注册自定义 Hooks。

## 验收标准 (Acceptance Criteria)

### Phase 1: Hook System 核心
- [x] 实现 `SessionLifecycleHook` 抽象基类，定义 `on_session_start()` 和 `on_session_end()` 方法。
- [x] 实现 `HookRegistry` 用于管理 Hook 的注册与查询。
- [x] 在 `RuntimeSession.start()` 中集成 `on_session_start` Hook 调用。
- [x] 在 `RuntimeSession.terminate()` 中集成 `on_session_end` Hook 调用。
- [x] 实现 Hook 执行的错误处理机制（部分失败不影响其他 Hooks）。

### Phase 2: 内置 Hooks
- [x] 实现 `GitCleanupHook`：
    - [x] `on_session_end`: 检查当前分支状态。
    - [x] `on_session_end`: 如果当前分支不是 `main`，尝试 `git checkout main`。
    - [x] `on_session_end`: 检测关联 Issue 状态，如果已完成/合并，执行 `git branch -D <feature-branch>`。
    - [x] 只有在操作安全（无未提交更改、分支已合并等）时才执行清理，否则发出警告。
- [x] 实现 `LoggingHook`（可选）：记录 Session 启动和结束时间。

### Phase 3: 配置支持
- [x] 在 `monoco.yml` 中支持 `hooks` 配置节点：
    - [x] 支持启用/禁用特定 Hooks。
    - [x] 支持为 Hooks 提供配置参数。
- [x] 在 `SessionManager` 初始化时从配置加载并注册 Hooks。

## 技术任务 (Technical Tasks)

### 设计阶段
- [x] **Design**: 设计 Hook 注册与执行机制（同步 vs 异步、执行顺序、错误处理）。
- [x] **Design**: 定义 Hook Context 对象（传递 Session 信息、Issue 状态等）。

### 实现阶段
- [x] **Impl**: 创建 `monoco/core/hooks/` 模块：
    - [x] `base.py`: 定义 `SessionLifecycleHook` 抽象基类。
    - [x] `registry.py`: 实现 `HookRegistry` 类。
    - [x] `context.py`: 定义 `HookContext` 数据类。
- [x] **Impl**: 修改 `monoco/features/scheduler/session.py` 添加 Hook 调用点。
- [x] **Impl**: 修改 `monoco/features/scheduler/manager.py` 集成 Hook 注册逻辑。
- [x] **Impl**: 实现 `GitCleanupHook`（`monoco/core/hooks/builtin/git_cleanup.py`）。
- [x] **Impl**: 实现 `LoggingHook`（可选）。
- [x] **Impl**: 更新配置模型支持 `hooks` 节点。

### 测试阶段
- [x] **Test**: 编写单元测试覆盖 Hook 注册、执行和错误处理。
- [x] **Test**: 模拟 Session 结束时的分支切换与删除场景。
- [x] **Test**: 测试安全检查逻辑（未提交更改、分支未合并等情况）。

### 文档阶段
- [~] **Docs**: 编写 Hook System 使用文档。（转移至文档专项）
- [~] **Docs**: 提供自定义 Hook 开发指南。（转移至文档专项）

## Review Comments

### 评审结论

- 所有核心功能已实现并通过测试
- Hook System 架构稳定，支持自定义扩展
- 剩余文档任务已记录为技术债务，将在文档专项中处理
- **批准关闭**

### 实现总结

1. **Hook System 核心** (`monoco/core/hooks/`):
   - `base.py`: 定义了 `SessionLifecycleHook` 抽象基类，`HookResult` 结果类，`HookStatus` 枚举
   - `context.py`: 定义了 `HookContext` 数据类，包含 Session、Issue、Git 信息
   - `registry.py`: 实现了 `HookRegistry` 类，支持注册、注销、执行 hooks，提供全局单例

2. **内置 Hooks** (`monoco/core/hooks/builtin/`):
   - `git_cleanup.py`: `GitCleanupHook` - 在 session 结束时执行 git 清理
     - 自动切换回 main 分支（如果安全）
     - 删除已合并的特性分支（如果 issue 已关闭）
     - 安全检查：未提交更改、分支是否已合并
   - `logging_hook.py`: `LoggingHook` - 记录 session 生命周期事件

3. **集成**:
   - `session.py`: `RuntimeSession` 在 `start()` 和 `terminate()` 中调用 hooks
   - `manager.py`: `SessionManager` 初始化时从配置加载 hooks
   - `config.py`: 添加 `session_hooks` 配置项

4. **测试** (`tests/core/hooks/`):
   - `test_base.py`: Hook 基类和结果类的测试
   - `test_context.py`: HookContext 的测试
   - `test_registry.py`: HookRegistry 的测试
   - `test_git_cleanup.py`: GitCleanupHook 的测试
   - `test_logging_hook.py`: LoggingHook 的测试

### 配置示例

```yaml
# .monoco/workspace.yaml
session_hooks:
  git_cleanup:
    enabled: true
    auto_switch_to_main: true
    auto_delete_merged_branches: true
    main_branch: main
    require_clean_worktree: true
  logging:
    enabled: true
    log_level: INFO
    log_start: true
    log_end: true
```

### 自定义 Hook 示例

```python
from monoco.core.hooks import SessionLifecycleHook, HookResult, HookContext

class MyCustomHook(SessionLifecycleHook):
    def on_session_start(self, context: HookContext) -> HookResult:
        # 自定义启动逻辑
        return HookResult.success("Custom hook executed")
    
    def on_session_end(self, context: HookContext) -> HookResult:
        # 自定义结束逻辑
        return HookResult.success("Custom cleanup done")

# 注册
from monoco.core.hooks import get_registry
registry = get_registry()
registry.register(MyCustomHook())
```
