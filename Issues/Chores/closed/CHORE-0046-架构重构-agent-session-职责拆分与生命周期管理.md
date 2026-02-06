---
id: CHORE-0046
uid: d2b75a
type: chore
status: closed
stage: done
title: 架构重构：Agent Session 职责拆分与生命周期管理
created_at: '2026-02-06T09:43:48'
updated_at: 2026-02-06 11:01:20
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0046'
- '#EPIC-0000'
files: []
criticality: low
solution: implemented
opened_at: '2026-02-06T09:43:48'
closed_at: '2026-02-06T10:45:00'
---

## CHORE-0046: 架构重构：Agent Session 职责拆分与生命周期管理

## Objective

强化 Agent Session 的职责边界，通过强制回收和工具拦截机制，确保 "开发" 与 "评审/合拢" 职能的物理隔离，符合 Trunk-Based Development 质量门禁要求。

## Acceptance Criteria

- [x] Daemon 监听到 Issue Stage 变更为 `review` 后，能自动识别并强制终止对应的 `Engineer` 角色 Session。
- [x] 实现 Agent 框架层的 Pre-Tool Hook，当角色为 `Engineer` 时拦截 `monoco issue close` 工具的执行。
- [x] 提供明确的拦截反馈，指导 Agent monoco submit issue 而非尝试合拢。

## Technical Tasks

- [x] **Daemon 层增强**:
  - [x] 在 `AgentScheduler` 中添加 `terminate_by_issue_and_role(issue_id, role)` 接口（基于现有 `terminate(session_id)` 封装）。
  - [x] 更新 `IssueStageHandler`，在阶段跃迁至 `review` 时触发强制回收逻辑。
- [x] **拦截层实现**:
  - [x] 在 Agent 执行链路中注入校验逻辑（Pre-Tool Hook）。
  - [x] 定义角色特权指令白名单/黑名单（Engineer 禁止 `issue close`）。
- [x] **验证**:
  - [x] 模拟 Engineer 尝试 `close` 动作，确认被拦截。
  - [x] 验证 `submit` 后 Session 是否被物理销毁。

## Architecture Design

### 1. Daemon Layer Enhancement

基于现有 `AgentScheduler` 架构的扩展：

```python
# src/monoco/core/scheduler/base.py
class AgentScheduler(ABC):
    # 现有接口已满足需求：
    # - terminate(session_id) -> bool
    # - list_active() -> Dict[str, AgentStatus]

    # 新增便利方法（非抽象，有默认实现）
    async def terminate_by_issue_and_role(self, issue_id: str, role_name: str) -> List[str]:
        """
        终止所有匹配 issue_id 和 role_name 的 sessions。

        Returns:
            被终止的 session_id 列表
        """
        terminated = []
        for session_id, session in self._sessions.items():
            if (session.get("issue_id") == issue_id and
                session.get("role_name") == role_name):
                if await self.terminate(session_id):
                    terminated.append(session_id)
        return terminated
```

### 2. IssueStageHandler Enhancement

在 `handlers.py` 中扩展 `IssueStageHandler`：

```python
# src/monoco/core/automation/handlers.py
class IssueStageHandler:
    def _should_handle(self, event: AgentEvent) -> bool:
        # 现有：处理 doing -> Engineer 启动
        # 新增：处理 review -> Engineer 强制回收
        new_stage = event.payload.get("new_stage")
        return new_stage in ["doing", "review"]

    async def _handle(self, event: AgentEvent) -> Optional[ActionResult]:
        new_stage = event.payload.get("new_stage")
        issue_id = event.payload.get("issue_id")

        if new_stage == "doing":
            # 现有逻辑：启动 Engineer
            return await self._spawn_engineer(event)
        elif new_stage == "review":
            # 新增逻辑：强制回收 Engineer Session
            return await self._terminate_engineer_sessions(event)

    async def _terminate_engineer_sessions(self, event: AgentEvent) -> ActionResult:
        """当 Issue 进入 review 阶段时，强制回收所有 Engineer 角色 sessions。"""
        issue_id = event.payload.get("issue_id")

        # 调用 scheduler 的批量终止接口
        terminated = await self.scheduler.terminate_by_issue_and_role(
            issue_id=issue_id,
            role_name="Engineer"
        )

        logger.info(f"Engineer sessions terminated for {issue_id}: {terminated}")

        return ActionResult.success_result(
            output={
                "action": "terminate_engineer_sessions",
                "issue_id": issue_id,
                "terminated_sessions": terminated,
                "reason": "Issue stage changed to review",
            }
        )
```

### 3. Pre-Tool Hook Interception Layer

在 Skill 框架层实现角色权限控制：

```python
# src/monoco/core/skill_framework.py
class RoleBasedToolInterceptor:
    """
    基于角色的工具调用拦截器。

    规则：
    - Engineer: 禁止执行 monoco issue close（必须走 submit -> review 流程）
    - Reviewer: 禁止执行代码修改类工具
    - Principal: 全权限
    """

    # 角色权限黑名单
    ROLE_BLACKLIST = {
        "Engineer": [
            "monoco.issue.close",      # Engineer 必须通过 submit 进入 review
            "monoco.issue.cancel",     # Engineer 不能取消 issue
        ],
        "Reviewer": [
            "bash.git_commit",         # Reviewer 只读
            "write",                   # Reviewer 不修改代码
            "edit",
        ],
    }

    # 友好的拦截提示
    INTERCEPT_MESSAGES = {
        "monoco.issue.close": {
            "Engineer": (
                "🚫 拦截：Engineer 角色不允许直接执行 'monoco issue close'。\n"
                "   正确流程：\n"
                "   1. 完成开发后执行 `monoco issue submit {issue_id}`\n"
                "   2. 进入 review 阶段后由 Reviewer 或系统处理合拢\n"
                "   这是 TBD (Trunk-Based Development) 质量门禁的要求。"
            ),
        }
    }

    def intercept(self, role_name: str, tool_name: str, issue_id: str = None) -> Optional[str]:
        """
        检查是否应该拦截该工具调用。

        Returns:
            如果应该拦截，返回错误消息；否则返回 None
        """
        blacklisted_tools = self.ROLE_BLACKLIST.get(role_name, [])

        for pattern in blacklisted_tools:
            if self._match_tool(pattern, tool_name):
                msg_template = self.INTERCEPT_MESSAGES.get(tool_name, {}).get(
                    role_name,
                    f"🚫 {role_name} 角色不允许执行 '{tool_name}'"
                )
                return msg_template.format(issue_id=issue_id) if issue_id else msg_template

        return None  # 允许执行

    def _match_tool(self, pattern: str, tool_name: str) -> bool:
        """支持通配符匹配，如 'monoco.issue.*'"""
        if pattern.endswith(".*"):
            return tool_name.startswith(pattern[:-2])
        return pattern == tool_name


# 在 Agent 执行链路中注入拦截器
class AgentExecutor:
    def __init__(self):
        self.tool_interceptor = RoleBasedToolInterceptor()

    async def execute_tool(self, role_name: str, tool_call: ToolCall, context: Context):
        # Pre-Tool Hook：权限检查
        if error_msg := self.tool_interceptor.intercept(
            role_name=role_name,
            tool_name=tool_call.name,
            issue_id=context.issue_id
        ):
            raise ToolInterceptionError(error_msg)

        # 继续执行工具
        return await self._do_execute(tool_call)
```

### 4. 事件流时序图

```
User/Agent                    Daemon                        Scheduler                     Session
   |                             |                              |                           |
   |  monoco issue submit FEAT-1 |                              |                           |
   |---------------------------->|                              |                           |
   |                             |  update_issue(stage=review)  |                           |
   |                             |------------------------------|                           |
   |                             |                              |                           |
   |                             |  publish(ISSUE_STAGE_CHANGED)|                           |
   |                             |----------------------------->|                           |
   |                             |                              |                           |
   |                             |                              |  terminate(engineer-sid)  |
   |                             |                              |-------------------------->|
   |                             |                              |                           | [Kill Process]
   |                             |                              |<--------------------------|
   |                             |<-----------------------------|  SESSION_TERMINATED       |
   |                             |                              |                           |
   |                             |  spawn(Reviewer)             |                           |
   |                             |----------------------------->|                           |
   |                             |                              |  schedule(Reviewer task)  |
   |                             |                              |-------------------------->|
   |                             |                              |                           | [New Process]
   |                             |                              |                           |
   |<----------------------------|  Issue submitted, Engineer   |                           |
   |  "FEAT-1 submitted for       |  session terminated,         |                           |
   |   review"                    |  Reviewer assigned           |                           |
   |                             |                              |                           |
```

## Implementation Notes

### 现有架构兼容性

1. **AgentScheduler 架构**（FEAT-0160）：
   - `terminate(session_id)` 接口已存在
   - `LocalProcessScheduler` 已实现进程级终止
   - 新增 `terminate_by_issue_and_role` 是便利封装，不影响现有接口

2. **Handler 架构**（FEAT-0162）：
   - `IssueStageHandler` 已订阅 `ISSUE_STAGE_CHANGED` 事件
   - 扩展 `_should_handle` 和 `_handle` 即可支持 review 阶段处理

3. **EventBus 架构**（FEAT-0155）：
   - 所有事件通过 `event_bus.publish()` 发布
   - `SESSION_TERMINATED` 事件已定义，可被其他组件监听

### 关键设计决策

1. **物理隔离 vs 逻辑隔离**：
   - 选择**物理隔离**（强制终止进程）而非逻辑隔离（标记无效）
   - 理由：防止 Engineer Agent 在 review 阶段继续修改代码

2. **拦截层位置**：
   - 选择在 **Skill 框架层** 而非单个 Skill 中实现
   - 理由：统一管控，避免每个 Skill 重复实现权限检查

3. **反馈策略**：
   - 拦截时返回明确的操作指引（如 "请使用 monoco issue submit"）
   - 而非简单的 "Permission Denied"

### 测试策略

```python
# tests/features/test_agent_session_lifecycle.py

async def test_engineer_session_terminated_on_review():
    """Test: Engineer session 在 issue 进入 review 时被终止。"""
    scheduler = LocalProcessScheduler()
    handler = IssueStageHandler(scheduler)

    # 模拟 Engineer session 运行中
    session_id = await scheduler.schedule(AgentTask(
        task_id="test-1",
        role_name="Engineer",
        issue_id="FEAT-1",
        prompt="Implement feature"
    ))

    # 模拟 issue stage 变为 review
    event = AgentEvent(
        type=AgentEventType.ISSUE_STAGE_CHANGED,
        payload={
            "issue_id": "FEAT-1",
            "new_stage": "review",
            "old_stage": "doing"
        }
    )

    await handler(event)

    # 验证 session 被终止
    assert scheduler.get_status(session_id) == AgentStatus.TERMINATED


def test_engineer_cannot_close_issue():
    """Test: Engineer 角色不能执行 monoco issue close。"""
    interceptor = RoleBasedToolInterceptor()

    result = interceptor.intercept(
        role_name="Engineer",
        tool_name="monoco.issue.close",
        issue_id="FEAT-1"
    )

    assert result is not None
    assert "submit" in result  # 提示中包含 submit 指引
```

## References

- `src/monoco/core/scheduler/base.py` - AgentScheduler 抽象定义
- `src/monoco/core/scheduler/local.py` - LocalProcessScheduler 实现
- `src/monoco/core/automation/handlers.py` - IssueStageHandler 实现
- `src/monoco/core/scheduler/events.py` - EventBus 和事件类型定义
- `src/monoco/features/issue/domain/lifecycle.py` - Issue 生命周期状态机

## Review Comments

Architecture design completed. The implementation plan leverages existing FEAT-0160 (AgentScheduler) and FEAT-0162 (Handler framework) infrastructure, requiring minimal additions:

1. **terminate_by_issue_and_role()** - Convenience method on existing scheduler
2. **_terminate_engineer_sessions()** - New handler method for review stage transitions
3. **RoleBasedToolInterceptor** - Pre-Tool Hook for role-based permission control

All components are backward compatible with current Monoco architecture.
