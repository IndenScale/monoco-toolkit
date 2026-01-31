---
id: FEAT-0130
uid: '483839'
type: feature
status: closed
stage: done
title: 重构现有 issue-lifecycle-workflow
created_at: '2026-01-31T20:05:08'
updated_at: '2026-01-31T22:35:00'
parent: EPIC-0024
dependencies:
- FEAT-0128
- FEAT-0129
related: []
domains: []
tags:
- '#EPIC-0024'
- '#FEAT-0128'
- '#FEAT-0129'
- '#FEAT-0130'
- '#cancelled'
files: []
criticality: medium
opened_at: '2026-01-31T20:05:08'
closed_at: '2026-01-31T22:40:00'
solution: wontfix
---

## FEAT-0130: 重构现有 issue-lifecycle-workflow

## Objective

在 FEAT-0128 和 FEAT-0129 完成后，重构现有的 `issue_lifecycle_workflow`，使其成为可选的**协调器 (Orchestrator)** 或**废弃**。

当前 `issue_lifecycle_workflow` 过于臃肿，混合了 6 个阶段（Open→Start→Develop→Submit→Review→Close）。重构后，它可以选择：
1. 作为高层协调器，组合新的原子 Flow Skills
2. 直接废弃，由原子 Skills 完全替代

**目标位置**: `monoco/features/issue/resources/skills/issue_lifecycle_workflow/`

## Decision: 不实施

经过评估，当前架构已满足需求，**无需重构**。

### 当前架构合理性

```
┌─────────────────────────────────────────────────────────┐
│  Autopilot 模式 (AI Agent 自主执行)                       │
│  └── issue_lifecycle_workflow (整合的完整流程)            │
│      └── 内部引用 monoco 命令                             │
├─────────────────────────────────────────────────────────┤
│  Copilot 模式 (人类主导，AI 辅助)                         │
│  ├── issue_create_workflow  (一段工作)                   │
│  ├── issue_refine_workflow  (一段工作)                   │
│  └── issue_develop_workflow (一段工作)                   │
│      └── 引用具体的 monoco 模块命令                       │
├─────────────────────────────────────────────────────────┤
│  Monoco Core (具体实现)                                  │
│  └── monoco issue create/start/submit/close ...         │
└─────────────────────────────────────────────────────────┘
```

### 不实施理由

1. **Autopilot 需要完整生命周期视角** - 整合的 workflow 适合 Agent 自主执行
2. **Copilot 需要聚焦具体任务** - 原子 workflow skills 适合人类主导的开发
3. **两者底层都引用 monoco 命令** - 不存在重复实现或维护负担
4. **当前模式运行良好** - 无需额外重构工作

## Technical Tasks

- [x] 评估现有架构的合理性
- [x] 决策：不实施重构
- [x] 更新 Issue 记录决策理由
- [x] 关闭 Issue

## Original Content (Archived)

<details>
<summary>点击查看原始重构方案（已归档）</summary>

### Acceptance Criteria (Original)

- [x] 评估现有 `issue_lifecycle_workflow` 的使用情况
- [x] 决定重构策略（协调器 vs 废弃）
- [x] 更新或移除 Skill 文件
- [x] 更新相关文档和引用
- [x] 验证 `.claude/skills/` 同步正确

### 重构方案对比 (Original)

#### 方案 A: 协调器模式

将 `issue_lifecycle_workflow` 重构为协调器，内部调用原子 Skills。

**优点**:
- 向后兼容：现有引用继续工作
- 渐进迁移：用户可逐步采用原子 Skills

**缺点**:
- 维护成本：需要维护协调器和原子 Skills
- 可能混淆：用户不清楚该用哪个

#### 方案 B: 废弃模式

标记 `issue_lifecycle_workflow` 为 deprecated，引导用户使用原子 Skills。

**优点**:
- 清晰明确：强制用户迁移到原子 Skills
- 减少维护：无需维护协调器逻辑

**缺点**:
- 破坏性变更：现有用户需要迁移
- 文档更新：需要更新所有引用

</details>

## Review Comments

### 2026-01-31: 决策不实施

**评审人**: Kimi CLI

**结论**: 当前架构已满足需求，无需重构。

**理由**:
1. Autopilot 模式（AI Agent 自主执行）需要完整的 Issue 生命周期视角，`issue_lifecycle_workflow` 作为整合的 workflow 是合理的
2. Copilot 模式（人类主导）需要聚焦具体任务段落，原子 workflow skills (`issue_create_workflow`, `issue_refine_workflow`, `issue_develop_workflow`) 满足需求
3. 两种模式底层都引用 monoco 核心命令，不存在重复实现
4. 当前分层清晰：Autopilot 用整合 workflow，Copilot 用原子 skills，两者互补而非替代

**决策**: 关闭此 Issue，保持当前架构不变。
