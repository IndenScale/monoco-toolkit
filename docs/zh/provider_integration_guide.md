# Agent Provider 接入指南

本指南介绍如何为 Monoco 接入新的 Agent Provider (LLM 引擎) 或新的调度环境 (Scheduler)。

## 1. 核心概念

Monoco 的调度架构分为三个层次：

1.  **AgentScheduler (调度器)**: 负责任务的生命周期管理、资源配额和环境隔离（如 `LocalProcessScheduler`）。
2.  **EngineAdapter (引擎适配器)**: 负责将 Agent 任务转换为特定 Provider 的执行指令（如 `GeminiAdapter`）。
3.  **AgentTask (任务描述)**: 包含角色、指令、引擎偏好等信息的标准化数据结构。

## 2. 添加新的 Agent Provider (LLM 引擎)

要支持新的 LLM 引擎（例如 OpenAI 或 DeepSeek），你需要实现一个新的 `EngineAdapter`。

### 步骤 1: 实现 EngineAdapter

在 `monoco/core/scheduler/engines.py` 中添加新的适配器类：

```python
class DeepSeekAdapter(EngineAdapter):
    @property
    def name(self) -> str:
        return "deepseek"

    def build_command(self, prompt: str) -> List[str]:
        # 返回启动该 Agent 的命令行指令
        return ["uv", "run", "monoco", "agent", "run", "--engine", "deepseek", "--prompt", prompt]

    @property
    def supports_yolo_mode(self) -> bool:
        return True
```

### 步骤 2: 注册到 EngineFactory

在 `EngineFactory._adapters` 字典中添加你的新引擎：

```python
class EngineFactory:
    _adapters = {
        "gemini": GeminiAdapter,
        "claude": ClaudeAdapter,
        # ...
        "deepseek": DeepSeekAdapter,
    }
```

## 3. 实现新的调度环境 (Scheduler)

如果你需要将 Agent 运行在不同的环境中（例如 Docker 容器或远程 K8s 集群），你需要实现 `AgentScheduler` 接口。

### 步骤 1: 继承 AgentScheduler

在 `monoco/core/scheduler/` 下创建新的实现文件（例如 `docker.py`）：

```python
from monoco.core.scheduler.base import AgentScheduler, AgentTask, AgentStatus

class DockerScheduler(AgentScheduler):
    async def schedule(self, task: AgentTask) -> str:
        # 1. 启动 Docker 容器
        # 2. 映射任务 ID 到容器 ID
        # 3. 返回 session_id
        pass

    async def terminate(self, session_id: str) -> bool:
        # 停止并删除容器
        pass

    def get_status(self, session_id: str) -> Optional[AgentStatus]:
        # 查询项目容器状态
        pass

    def list_active(self) -> Dict[str, AgentStatus]:
        # 列出所有运行中的容器
        pass

    def get_stats(self) -> Dict[str, Any]:
        # 返回资源使用统计
        pass
```

### 步骤 2: 在 Daemon 中配置

修改 `monoco/daemon/scheduler.py` 或通过配置项将 `SchedulerService` 切换到新的实现。

## 4. 测试你的接入

### 引擎测试

参考 `tests/test_scheduler_engines.py` 添加针对新适配器的单元测试。

### 调度器测试

参考 `tests/test_scheduler_local.py` 实现针对新环境的功能测试，确保满足接口契约。
