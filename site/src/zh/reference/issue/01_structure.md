# 构造解剖 (Structure)

Monoco Issue 本质上是一个 **可执行的 Markdown 文件**。它的结构设计旨在同时满足人类的可读性和 Agent 的可解析性。

## 1. 物理组成

一个标准的 Issue 文件 (例如 `Issues/Features/open/FEAT-001.md`) 由三部分组成：

```markdown
---
# YAML Front Matter (元数据层)
id: FEAT-001
type: feature
status: open
stage: doing
title: 实现深色模式
files:
  - src/theme.ts
  - src/components/Toggle.tsx
---

## FEAT-001: 实现深色模式

<!-- Body (内容层) -->

## Acceptance Criteria

- [ ] 支持 System Preference 自动切换
- [ ] 支持手动 Toggle 切换

## Technical Tasks

- [x] 定义 Theme Interface
- [/] 实现 Context Provider
```

### 1.1 YAML Front Matter (机器可读)

这是 Agent 理解任务的主要接口。

- **Identity**: `id`, `uid` (唯一标识)。
- **Lifecycle**: `status` (物理位置), `stage` (逻辑进度)。
- **Topology**: `parent`, `dependencies`, `related` (构建知识图谱)。
- **Context (New)**: `files` 列表。记录了该 Issue 修改了哪些代码文件。这允许 Agent 在恢复任务时瞬间加载必要的上下文。

### 1.2 Markdown Body (人机共读)

- **Heading**: `## {ID}: {Title}`。必须与元数据严格匹配，作为一致性锚点。
- **Checkbox Matrix**:
  - `[ ]` To Do
  - `[/]` Doing
  - `[x]` Done
  - `[-]` Cancelled
  - Agent 通过解析这些 checkbox 来更新任务进度。

## 2. 静态校验 (Static Linting)

为了防止 Agent（或人类）写出格式错误的任务，Monoco 引入了 **Schema-on-Read** 的强校验机制。

运行 `monoco issue lint` 会检查：

1.  **完整性**: 是否缺少必填字段（如 `title`）？是否缺少 `Technical Tasks`？
2.  **一致性**: 文件名、ID、Heading 是否一致？
3.  **合规性**: 处于 `Closed` 状态的 Issue 是否已经完成了所有 Checkbox？是否存在未解决的 `Review Comments`？
4.  **环境策略**: 是否意外修改了主分支代码？

只有通过 Lint 的 Issue，才被认为是**“可执行的”**。

---

[上一章: 00. 总览](./00_overview.md) | **下一章**: [02. 循环: 生命周期](./02_lifecycle.md)
