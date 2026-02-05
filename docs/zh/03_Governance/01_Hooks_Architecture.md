# 钩子架构 (Hooks Architecture)

Monoco 的治理能力建立在一套灵活且强大的 Hooks 体系之上。通过在关键生命周期节点插入钩子，我们实现了自动化的规范检查与流程控制。

Monoco 区分了三个维度的 Hooks：

## 1. Git Hooks (版本控制层)

这些 Hook 由 Git 原生触发，拦截 Git 操作。Monoco 提供了开箱即用的配置（通常通过 `pre-commit` 框架管理）。

| Hook | 触发时机 | 作用 | 典型场景 |
| :--- | :--- | :--- | :--- |
| `pre-commit` | `git commit` 前 | 检查暂存区文件 | 运行 Linter, Formatter, 检查大文件 |
| `commit-msg` | 填写提交信息后 | 检查 Commit Message | 强制关联 Issue ID (e.g., "feat(FEAT-101): ...") |
| `pre-push` | `git push` 前 | 检查即将推送的分支 | 运行轻量级单元测试 |

**Monoco 特性**: 默认的 Git Hooks 会自动检查是否处于 `monoco issue start` 激活的上下文中，并阻止在受保护分支（如 `main`）上的直接提交。

## 2. Issue Hooks (任务管理层)

这些 Hook 由 `monoco issue` CLI 触发，拦截任务状态变更。

| Hook | 触发时机 | 作用 | 典型场景 |
| :--- | :--- | :--- | :--- |
| `on-create` | `issue create` 后 | 初始化 | 自动分配 Owner, 填充模板默认值 |
| `pre-submit` | `issue submit` 前 | 准入检查 | 检查 Checkbox 是否全勾选, `files` 是否非空 |
| `on-stage-change` | Stage 变更时 | 联动 | 发送通知到 Slack/Discord, 同步状态到外部系统 |

**配置方式**: 在 `.monoco/project.yaml` 中定义 Shell 脚本或 Python 脚本路径。

## 3. Agent Hooks (运行时层)

这些 Hook 由 Agent Runtime 触发，介入 Agent 的思考与执行循环。

| Hook | 触发时机 | 作用 | 典型场景 |
| :--- | :--- | :--- | :--- |
| `system-prompt` | 构建 Prompt 时 | 动态注入 | 注入当前时间、天气、数据库 Schema |
| `tool-call` | Agent 调用工具前 | 安全拦截 | 阻止 `rm -rf`, 阻止访问敏感域名 |
| `tool-result` | 工具返回结果后 | 结果修正 | 截断过长的输出, 格式化 JSON |

## 4. 治理哲学：拦截优于回滚

Monoco 的 Hooks 哲学是 **Fail Fast**。
我们宁愿在开发者 Commit 时报错阻止他，也不愿让他提交了错误代码后再去 Revert。Hooks 是保障系统熵减的第一道防线。
