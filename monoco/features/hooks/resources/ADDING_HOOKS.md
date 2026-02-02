# 为 Feature 添加自定义 Git Hooks

本文档介绍如何为 Monoco Feature 添加自定义 Git Hooks。

## 概述

Monoco 使用**分布式 Hooks + 聚合器**架构：

1. **分布式**：每个 Feature 在 `resources/hooks/` 目录存放自己的 hook 脚本
2. **聚合器**：`features/hooks/` 负责收集、排序、生成最终 hook

## 快速开始

### 1. 创建 Hooks 目录

在你的 Feature 目录下创建 hooks 目录：

```
monoco/features/{your_feature}/
└── resources/
    └── hooks/
        ├── pre-commit.sh
        ├── pre-push.sh
        └── post-checkout.sh
```

### 2. 编写 Hook 脚本

创建 shell 脚本文件，例如 `pre-commit.sh`：

```bash
#!/bin/sh
# Your Feature Pre-Commit Hook
# Description of what this hook does

echo "[Monoco] Running your-feature pre-commit check..."

# Your logic here
# Use $MONOCO_CMD to call monoco commands
$MONOCO_CMD your-command

if [ $? -ne 0 ]; then
    echo "[Monoco] Your check failed!"
    exit 1
fi

echo "[Monoco] Your check passed."
exit 0
```

### 3. 可用的环境变量

在 hook 脚本中，以下环境变量可用：

| 变量 | 说明 | 示例 |
|------|------|------|
| `$MONOCO_CMD` | Monoco 命令的完整调用路径 | `python -m monoco` 或 `/path/to/python -m monoco` |
| `$PYTHON_CMD` | Python 解释器路径 | `./.venv/bin/python` |

### 4. 支持的 Hook 类型

| Hook 类型 | 触发时机 | 典型用途 |
|-----------|----------|----------|
| `pre-commit` | 执行 `git commit` 前 | 代码检查、Issue 验证 |
| `pre-push` | 执行 `git push` 前 | 关键 Issue 检查、测试运行 |
| `post-checkout` | 执行 `git checkout` 后 | 同步 Issue 状态、更新隔离环境 |
| `pre-rebase` | 执行 `git rebase` 前 | 防止在特定状态下 rebase |
| `commit-msg` | 提交信息编辑后 | 验证提交信息格式 |

## 最佳实践

### 保持脚本简洁

Hook 脚本应该快速执行，避免长时间阻塞开发者工作流：

```bash
# ✅ 好的做法：快速检查
echo "[Monoco] Running quick validation..."
$MONOCO_CMD quick-check

# ❌ 避免：长时间运行的任务
# $MONOCO_CMD run-all-tests  # 这可能需要几分钟
```

### 提供清晰的错误信息

当检查失败时，提供可操作的错误信息：

```bash
if [ $RESULT -ne 0 ]; then
    echo ""
    echo "[Monoco] ❌ Check failed!"
    echo "[Monoco] Reason: Specific explanation of what went wrong"
    echo "[Monoco] Fix: Suggest how to fix the issue"
    exit 1
fi
```

### 处理没有变更的情况

对于只检查特定文件类型的 hooks，优雅处理没有相关变更的情况：

```bash
# 获取暂存的特定类型文件
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "[Monoco] No Python files staged. Skipping check."
    exit 0
fi
```

### 设置优先级

如果需要控制 hook 执行顺序，可以在 Feature 的 `adapter.py` 中设置优先级：

```python
from monoco.core.loader import FeatureModule, FeatureMetadata

class YourFeature(FeatureModule):
    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="your_feature",
            priority=50,  # 数字越小优先级越高，默认 100
            ...
        )
```

执行顺序：按优先级升序（数字小的先执行）。

## 示例

### 示例 1：简单的代码风格检查

```bash
#!/bin/sh
# Lint Feature Pre-Commit Hook

STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$STAGED_PY" ]; then
    exit 0
fi

echo "[Monoco] Running linter on staged Python files..."
$MONOCO_CMD lint --files $STAGED_PY
exit $?
```

### 示例 2：检查测试覆盖率

```bash
#!/bin/sh
# Coverage Feature Pre-Push Hook

echo "[Monoco] Checking test coverage..."
$MONOCO_CMD coverage check --min 80

if [ $? -ne 0 ]; then
    echo "[Monoco] ❌ Coverage check failed!"
    echo "[Monoco] Run 'monoco coverage report' to see details."
    exit 1
fi

echo "[Monoco] ✓ Coverage check passed."
exit 0
```

### 示例 3：分支切换后同步状态

```bash
#!/bin/sh
# Sync Feature Post-Checkout Hook

BRANCH_SWITCH="$3"

if [ "$BRANCH_SWITCH" != "1" ]; then
    exit 0
fi

echo "[Monoco] Syncing after branch switch..."
$MONOCO_CMD sync
exit 0
```

## 调试 Hooks

### 查看生成的 Hook

```bash
# 查看当前安装的 pre-commit hook
cat .git/hooks/pre-commit
```

### 手动运行 Hook

```bash
# 手动运行 pre-commit hook
sh .git/hooks/pre-commit
```

### 临时禁用 Hooks

```bash
# 跳过 pre-commit hook
git commit --no-verify -m "Your message"

# 跳过 pre-push hook
git push --no-verify
```

## 故障排除

### Hook 没有执行

1. 检查 hook 是否已安装：`monoco hooks status`
2. 检查 hook 文件权限：`ls -la .git/hooks/`
3. 检查 Feature 是否启用：`monoco config get hooks.features.your_feature`

### Hook 执行失败

1. 检查 `$MONOCO_CMD` 是否可用
2. 查看详细的错误输出
3. 手动运行命令测试：`python -m monoco your-command`

### 多个 Feature 的 Hook 冲突

使用优先级控制执行顺序，或检查其他 Feature 的 hook 逻辑。

## 参考

- [Git Hooks 官方文档](https://git-scm.com/docs/githooks)
- Monoco Issue Feature 的 hooks 实现：`monoco/features/issue/resources/hooks/`
