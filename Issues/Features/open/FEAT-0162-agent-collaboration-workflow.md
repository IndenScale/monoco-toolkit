---
id: FEAT-0162
uid: c3d4e5
type: feature
status: open
stage: doing
title: Agent 联调工作流 - 端到端自动化
created_at: '2026-02-03T09:30:00'
updated_at: '2026-02-03T11:19:06'
parent: EPIC-0025
dependencies:
- FEAT-0160
- FEAT-0161
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0162'
- workflow
- automation
- collaboration
files:
- Memos/agent-scheduler-architecture-assessment.md
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T09:30:00'
---

## FEAT-0162: Agent 联调工作流 - 端到端自动化

## 背景与目标

当前 Agent 调度存在链式调用问题：Engineer 完成后直接触发 Reviewer，导致 Agent 间强耦合。根据架构评估，应改为**文件状态驱动**：Agent 之间没有直接调度关系，而是通过检测文件状态变化触发。

本任务旨在实现完整的 Agent 联调工作流。

**架构决策**: 参见 Memos/agent-scheduler-architecture-assessment.md

**核心原则**:
1. **Filesystem as API**: 所有触发通过文件状态变化
2. **去链式化**: Agent 不直接调用 Agent
3. **IM 为未来工作**: 当前聚焦核心文件驱动架构

## 目标

1. 实现 `TaskFileHandler` (监听 tasks.md 变化)
2. 实现 `IssueStageHandler` (监听 Issue stage=doing)
3. 实现 `MemoThresholdHandler` (监听 Memo 累积)
4. 实现 `PRCreatedHandler` (监听 PR 创建)
5. 完整 workflow 集成测试

## 验收标准

- [ ] **TaskFileHandler**: 监听 tasks.md 变化，触发 Architect
- [ ] **IssueStageHandler**: 监听 Issue stage=doing，触发 Engineer
- [ ] **MemoThresholdHandler**: 监听 Memo 累积阈值，触发 Architect
- [ ] **PRCreatedHandler**: 监听 PR 创建，触发 Reviewer
- [ ] **Workflow A**: tasks.md → Architect → Issue (draft)
- [ ] **Workflow B**: Issue (doing) → Engineer → PR
- [ ] **Workflow C**: PR → Reviewer → 审查报告

## 技术任务

### Phase 1: Handler 实现

- [ ] 实现 `TaskFileHandler`
  - 监听 `tasks.md` 或特定任务文件
  - 检测新任务添加
  - 触发 `SpawnAgentAction` (Architect role)
  - Architect 直接创建 Issue (stage=draft)
- [ ] 实现 `IssueStageHandler`
  - 监听 `Issues/` 目录变化
  - 检测 YAML Front Matter `stage` 字段变为 `doing`
  - 触发 `SpawnAgentAction` (Engineer role)
  - 传递 Issue 内容给 Agent
- [ ] 实现 `MemoThresholdHandler`
  - 监听 `Memos/inbox.md` 变化
  - 检测 pending memo 数量超过阈值
  - 触发 `SpawnAgentAction` (Architect role)
  - Architect 分析后创建 Issue
- [ ] 实现 `PRCreatedHandler`
  - 监听 PR 创建事件 (通过 Git webhook 或文件变化)
  - 触发 `SpawnAgentAction` (Reviewer role)
  - 传递 PR 信息给 Agent

### Phase 2: 工作流实现

- [ ] **Workflow A: Task → Architect → Issue**
  ```
  tasks.md 更新 → TaskFileHandler → 调度 Architect
                                        │
                                        ▼
                              Architect 分析需求
                                        │
                                        ▼
                              创建 Issue (stage=draft)
  ```

- [ ] **Workflow B: Issue → Engineer → PR**
  ```
  Issue stage=doing → IssueStageHandler → 调度 Engineer
                                              │
                                              ▼
                                    Engineer 编码实现
                                              │
                                              ▼
                                    提交 PR
  ```

- [ ] **Workflow C: PR → Reviewer → 报告**
  ```
  PR 创建 → PRCreatedHandler → 调度 Reviewer
                                    │
                                    ▼
                          Reviewer 代码审查
                                    │
                                    ▼
                          输出审查报告 (到文件/Memos)
  ```

### Phase 3: 集成测试

- [ ] 测试 Workflow A: tasks.md → Architect → Issue 创建
- [ ] 测试 Workflow B: Issue doing → Engineer → PR
- [ ] 测试 Workflow C: PR → Reviewer → 审查报告
- [ ] 测试完整链路: Task → Issue → Engineer → PR → Reviewer

### Phase 4: 文档

- [ ] 编写 Workflow 设计文档
- [ ] 编写 Handler 扩展指南
- [ ] 编写故障排查指南

## 架构设计

### Handler 与 Action 映射

```python
# TaskFileHandler -> SpawnAgentAction(Architect)
router.register("TASK_FILE_CHANGED", SpawnAgentAction(
    scheduler=agent_scheduler,
    role="Architect"
))

# IssueStageHandler -> SpawnAgentAction(Engineer)
router.register("ISSUE_STAGE_CHANGED", ConditionalAction(
    condition=lambda p: p.get("stage") == "doing",
    action=SpawnAgentAction(scheduler=agent_scheduler, role="Engineer")
))

# MemoThresholdHandler -> SpawnAgentAction(Architect)
router.register("MEMO_THRESHOLD_REACHED", SpawnAgentAction(
    scheduler=agent_scheduler,
    role="Architect"
))

# PRCreatedHandler -> SpawnAgentAction(Reviewer)
router.register("PR_CREATED", SpawnAgentAction(
    scheduler=agent_scheduler,
    role="Reviewer"
))
```

## 依赖

- FEAT-0160: AgentScheduler 抽象层
  - `SpawnAgentAction` 依赖
- FEAT-0161: 文件系统事件自动化框架
  - `ActionRouter`, `FilesystemWatcher` 依赖

## 被依赖

- 无直接依赖

## 未来工作 (非当前范围)

- IM 集成 (钉钉/飞书): 作为额外的文件输入源
- Proposal 机制: 如需预创建确认，未来再评估
- 索引层: 当文件数量影响性能时引入

## Review Comments

*2026-02-03: 移除 IM 和 Proposal 相关内容，聚焦核心文件驱动架构*
