# Git Hooks 标准化方案

> 关联 Issue: [FEAT-0173](../../../Issues/Features/open/FEAT-0173-implement-universal-hooks-registration-and-install.md)

## 1. 核心目标

Git Hooks 是 Monoco 质量门禁的第一道防线。目前的实现较为分散，本方案旨在将 Git Hooks 纳入统一的 `monoco-hook` 协议体系中，实现：

- **声明式配置**：通过脚本 Front Matter 声明 Hook 类型和触发时机。
- **差异化执行**：支持基于文件变更模式（Glob Matcher）的按需触发。
- **项目/功能解耦**：允许 Feature 颗粒度的 Hooks，随功能同步安装与卸载。

## 2. 统一映射 (Git Event Mapping)

Git Hooks 将直接映射到 Monoco 通用协议中，对应 `type: git`。

| Git 事件 (Native)    | Monoco 类比事件          | 典型用途                                  |
| :------------------- | :----------------------- | :---------------------------------------- |
| `pre-commit`         | `ON_BEFORE_COMMIT`       | 运行 Linter (monoco issue lint), 单元测试 |
| `prepare-commit-msg` | `ON_COMMIT_PREPARE`      | 自动插入 Issue ID 到提交消息              |
| `commit-msg`         | `ON_COMMIT_MSG_VALIDATE` | 验证提交消息是否符合标准                  |
| `post-merge`         | `ON_AFTER_MERGE`         | 自动更新依赖, 同步 Issue 状态             |
| `pre-push`           | `ON_BEFORE_PUSH`         | 运行全量集成测试                          |

## 3. 协议定义 (Front Matter)

所有 Git Hook 脚本应包含以下元数据：

```bash
#!/bin/bash
# ---
# type: git
# event: pre-commit
# description: 自动运行 monoco 质量检查
# matcher: "**/*.py"  # 仅当 py 文件变动时触发
# order: 10           # 执行顺序
# ---

# Hook logic starts...
uv run monoco issue lint
```

### 3.1 增强逻辑：Glob Matcher

`UniversalHookManager` 在安装 Git Hooks 时，如果是 `pre-commit` 等支持文件列表的事件，将生成一段包装逻辑：

1. 获取当前 Staged Files。
2. 根据 `matcher` 过滤文件。
3. 如果匹配成功，则执行 Hook 逻辑。
4. 如果匹配为空，则静默跳过（提升开发效率）。

## 4. 安装与生命周期管理

### 4.1 安装路径

- **本地环境**: 始终链接到 `.git/hooks/<event>`。
- **多 Hook 链式调用**: Monoco 会在 `.git/hooks/` 下创建一个 `monoco-runner`。原生 Git 事件文件（如 `pre-commit`）将仅仅是一行：
  ```bash
  #!/bin/sh
  exec monoco hook run git pre-commit "$@"
  ```

### 4.2 Feature 隔离 Hooks

支持在 `Issues/Features/{id}/resources/hooks/` 下存放仅对该 Feature 生效的 Hooks。

- 当 `monoco issue start` 时：安装这些 Hooks。
- 当 `monoco issue close` 时：卸载这些 Hooks。

## 5. 安全与兼容性

- **非破坏性**: 如果 `.git/hooks/pre-commit` 已存在且非 Monoco 创建，Monoco 将采取 **合并执行 (Append)** 或 **手动触发提示** 策略，绝不直接覆盖用户已有的 Husky/pre-commit 配置。
- **执行环境**: Git Hooks 运行在 User Space，应始终使用项目内的虚拟环境（如 `uv run`）。

## 6. 与 Agent Hooks 的协同

在 `monoco issue submit` 场景下，Monoco 可以同时触发：

1. **Agent Hook**: 在 LLM 侧进行代码规范预审。
2. **Git Hook (pre-commit)**: 在本地文件系统执行物理检查。

这种“双重门禁”确保了即使开发者绕过 Agent 直接提交，底层质量标准依然受控。
