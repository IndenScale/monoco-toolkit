---
id: FEAT-0154
uid: e3f844
type: feature
status: open
stage: review
title: 优化 Git 合并策略与增强 Issue 关闭流程
created_at: '2026-02-02T13:41:00'
updated_at: '2026-02-02T14:44:43'
parent: EPIC-0030
dependencies: []
related:
- FEAT-0145
domains:
- IssueSystem
tags:
- '#EPIC-0030'
- '#FEAT-0154'
- '#FEAT-0145'
files:
- monoco/features/issue/commands.py
- monoco/features/issue/resources/zh/AGENTS.md
- monoco/features/issue/resources/en/AGENTS.md
- .qwen/skills/monoco_workflow_issue_management/SKILL.md
criticality: high
opened_at: '2026-02-02T13:41:00'
isolation:
  type: branch
  ref: feat/feat-0154-优化-git-合并策略与增强-issue-关闭流程
  created_at: '2026-02-02T13:45:11'
---

## FEAT-0154: 优化 Git 合并策略与增强 Issue 关闭流程

## 背景与目标

当前 `monoco` 工作流中，Agent 在关闭 Issue 时的 Git 操作策略过于粗糙，容易导致“旧状态污染主线”的问题。具体表现为 Feature 分支可能包含对其他 Issue 文件（非本 Feature 范围）的意外回滚或修改，直接合并会覆盖主线上的最新进展。

**目标**:
1.  **安全合并**: 通过工具链约束，确保 `close` 操作时的合并是原子的、基于 Issue 范围的 (Issue-Bounded)。
2.  **默认清理**: `closed` 状态应意味着物理资源的释放，减少陈旧分支堆积。
3.  **明确规范**: 更新 Agent 行为准则，确立 `monoco issue close` 为唯一权威的合并途径。

## 验收标准

- [x] `monoco issue close` 默认执行 `--prune` 操作（删除分支/Worktree），除非显式指定 `--no-prune`。
- [x] `monoco issue close` 支持（或建议）自动化合并流程，优先尝试智能合并。
- [x] 完成对 `touched files` (Issue `files` 字段) 追踪机制的深度调查报告，评估其作为“智能合并”依据的可行性。
- [x] 更新 `monoco/features/issue/resources/zh/AGENTS.md` 和相关 Skill 文档，明确合并规范和 Fallback 策略。

## 技术任务

### Phase 1: 机制增强 (Implementation)
- [x] 修改 `monoco issue close` 命令参数，将 `prune` 默认设为 `True`。
- [x] 增强 `monoco issue close` 的交互提示，在删除分支前给出明确的最终状态确认。

### Phase 2: 规范文档 (Documentation)
- [x] 更新 `AGENTS.md`：
    - 明确禁止 Agent 手动执行 `git merge` 合并 Feature 分支。
    - 说明必须使用 `monoco issue close` 进行闭环。
    - 阐述冲突处理原则：优先使用 Cherry-Pick 挑选有效变更，而非全量 Merge。
- [x] 更新 `skills/monoco_workflow_issue_management/SKILL.md` 中的 Close 阶段检查点。

### 调研发现 (Investigation Findings)

针对 **"Smart Atomic Merge"** 的可行性，我们对 `monoco` 现有的 `files` (touched files) 追踪机制进行了 Spike 测试，结论如下：

1.  **捕捉准确性 (Accuracy)**:
    - `sync-files` 使用 `git diff --name-only base...target` 逻辑。
    - **优点**: 能够精准捕捉 Feature Branch 自创建以来引入的所有增量文件（新增/修改/删除）。
    - **验证**: 经测试，能够正确识别新创建的代码文件、Issue 元数据文件以及对现有文件的修改。

2.  **边界与风险 (Boundaries & Risks)**:
    - **双刃剑**: 它会捕捉到 Feature 分支内发生的所有变更。如果分支被“污染”（如无意中格式化了其他 Issue 文件），这些文件也会进入 `files` 列表。
    - **结论**: `files` 列表是 Feature 的 **"真实影响范围" (Actual Impact Scope)**。作为合并白名单是可行的，能有效过滤单纯因“旧版本基线”导致的隐性覆盖，但无法防御显式的误操作修改。

3.  **智能合并可行性 (Feasibility)**:
    - 可以基于 `files` 列表实现 `git checkout main && git checkout feature -- <files>` 的选择性合并逻辑。
    - **冲突处理原则**: 如果 `touched files` 与主线产生冲突，自动化工具**必须立即停止合并**，并抛出明确错误。
    - **Fallback 指引**: 错误信息需明确指示 Agent 转入手动 Cherry-Pick 模式，并强调核心原则：**“仅挑选属于本 Feature 的有效变更，严禁覆盖主线上无关 Issue 的更新”**。
    - 这将成为未来 "Smart Merge Strategy" 的核心基础。

## Review Comments

- **Implementation**: `monoco issue close` command updated to default to `--prune=True`.
- **Documentation**: Updated `AGENTS.md` and `SKILL.md` to reflect the new strict merge strategy.
- **Verification**: Technical tasks checked off.
