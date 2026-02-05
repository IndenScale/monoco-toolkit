# Issue 生命周期钩子 (Lifecycle Hooks)

Issue 生命周期钩子是 Monoco 核心治理机制的一部分。它允许在执行 `monoco issue` 相关命令的特定阶段（如执行前和执行后）注入自动化逻辑。

## 核心价值

1. **统一控制**：无论是通过 CLI 命令、Git Hooks 还是 Agent 触发，所有 Issue 状态变更都经过相同的准入和准出检查。
2. **自动化校验**：在 `submit` 前自动运行 Lint，或在 `start` 后自动初始化分支。
3. **结构化反馈**：向 Agent 提供具体的修复建议（Suggestions），提升自动化成功率。

## 支持的事件 (Events)

Monoco 遵循严格的 `pre-` 和 `post-` 命名规范：

- `pre-create` / `post-create`
- `pre-start` / `post-start`
- `pre-submit` / `post-submit`
- `pre-close` / `post-close`
- `pre-open` / `post-open`
- `pre-cancel` / `post-cancel`
- `pre-delete` / `post-delete`

## 钩子类型

### 1. 内置钩子 (Built-in Hooks)

位于 `monoco/features/issue/hooks/builtin/`。这些是 Monoco 核心功能的一部分，默认对所有项目生效。

- **pre-submit**: 校验 Issue 的 Lint 状态。
- **post-start**: 自动显示当前工作的分支信息及后续操作建议。

### 2. 用户自定义钩子 (User Hooks)

位于项目根目录下的 `.monoco/hooks/issue/`。开发者可以放置 Python 脚本或 Shell 脚本来实现项目特定的规则。

- **Python 脚本**: `.monoco/hooks/issue/my-rule.py`
- **Shell 脚本**: `.monoco/hooks/issue/check-branch.sh`

## 钩子决策 (Decisions)

钩子执行后必须返回以下三种决策之一：

- **ALLOW**: 检查通过，继续执行命令。
- **WARN**: 检查通过，但向用户显示警告信息和建议。
- **DENY**: 检查失败。如果是 `pre-` 事件，将**阻断**后续命令的执行。

## 跳过与调试

- **跳过钩子**: 使用 `--no-hooks` 参数。
  ```bash
  monoco issue start FEAT-0181 --no-hooks
  ```
- **调试模式**: 使用 `--debug-hooks` 查看每个钩子的耗时和详细执行细节。
  ```bash
  monoco issue submit FEAT-0181 --debug-hooks
  ```

## 开发者 API (Python)

如果你正在开发内置钩子，可以使用以下模型：

```python
from monoco.features.issue.hooks.models import IssueHookContext, IssueHookResult

def my_custom_hook(context: IssueHookContext) -> IssueHookResult:
    if context.issue_id == "SECRET-1":
        return IssueHookResult.deny("This issue is restricted.")
    return IssueHookResult.allow()
```
