# Monoco 工作流最佳实践 (Best Practices)

本文档定义了 Monoco 推荐的标准化开发工作流。通过遵循这些实践，您可以最大化地利用 Agent 的能力，同时确保代码库的稳定性和可追踪性。

> 核心原则：**Issue 驱动开发** (Issue-Driven Development)。

## 全景图

```mermaid
graph LR
    Create[1. 创建 Issue (Create)] --> Start[2. 启动开发 (Start)]
    Start --> Dev[3. 编码与测试 (Implement)]
    Dev --> Check[4. 原子提交 (Commmit)]
    Check --> Review[5. 提交审查 (Submit)]
    Review --> Close[6. 完成与归档 (Close)]
```

---

## 1. 启动阶段 (Inception)

### 1.1 创建 Issue (Create)

一切始于 Issue。不要直接修改代码。

```bash
# 创建一个特性
monoco issue create feature -t "支持深色模式"
```

如果你有明确的上级任务（如 Epic），请务必关联：

```bash
monoco issue create feature -t "支持深色模式" --parent EPIC-001
```

### 1.2 启动工作 (Start)

**这是最关键的一步**。使用 `start` 命令不仅是更改状态，更是建立开发环境的快照。

```bash
monoco issue start FEAT-001 --branch
```

- **--branch**: 强制创建特性分支（推荐）。分支名会自动规范化为 `feat/feat-001-support-dark-mode`。
- **自动上下文切换**: Monoco 可以在启动时自动加载相关的上下文信息（未来特性）。

---

## 2. 实施阶段 (Implementation)

在此阶段，你在特性分支上进行开发。

### 2.1 编码与验证

像往常一样编码。但需要遵循：

- **测试先行**: 在编写实现代码前，先运行测试确保环境正常。
- **Lint 检查**: 随时运行 `monoco issue lint` 确保元数据健康。

### 2.2 原子提交 (Atomic Commit) ✨

Monoco 提供了增强版的提交命令，它会在提交前强制运行质量门禁。

```bash
# 自动检测关联的 Issue（基于分支名），运行 Lint，然后提交
monoco issue commit -m "feat: implement dark mode toggle"
```

如果是传统的 Git 提交，你可能会忘记关联 Issue ID，或者提交了不符合规范的代码。`monoco issue commit` 解决了这个问题。

---

## 3. 交付阶段 (Delivery)

### 3.1 同步上下文 (Sync Context)

在准备提交审查前，确保 Issue 的 `files` 字段列出了所有你修改过的文件。这对于 Agent 理解变更范围至关重要。

```bash
# 自动同步 Git 变更文件列表到 Issue 元数据
monoco issue sync-files FEAT-001
```

### 3.2 提交审查 (Submit)

当你认为工作已完成：

```bash
monoco issue submit FEAT-001
```

此命令会：

1. 将 Issue 状态变更为 `Review`。
2. 生成一份交付报告（Delivery Report），包含变更摘要、关联文件等。
3. （可选）触发 CI 流水线。

---

## 4. 验收阶段 (Acceptance)

Reviewer（或者是扮演 Reviewer 的 Agent）检查代码。

### 4.1 关闭 Issue (Close)

验证通过后，合并代码并关闭 Issue。

```bash
# 标记为已实现
monoco issue close FEAT-001 --solution implemented
```

这会自动：

- 将状态设为 `Closed`。
- 记录 `closed_at` 时间戳。
- 将文件归档到 `Issues/Features/closed/` 目录。

### 4.2 清理

```bash
# 删除本地特性分支并切回主分支
git checkout main
git branch -d feat/feat-001-support-dark-mode
```
