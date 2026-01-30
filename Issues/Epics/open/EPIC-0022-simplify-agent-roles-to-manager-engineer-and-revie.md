---
id: EPIC-0022
uid: 5e0f82
type: epic
status: open
stage: doing
title: 简化 Agent 角色为 Manager, Engineer 和 Reviewer
created_at: '2026-01-30T16:42:46'
updated_at: '2026-01-30T16:42:46'
parent: EPIC-0000
dependencies: []
related: []
domains:
- AgentScheduling
tags:
- '#EPIC-0022'
- '#EPIC-0000'
files: []
opened_at: '2026-01-30T16:42:46'
progress: 2/4
files_count: 0
---

## EPIC-0022: 简化 Agent 角色为 Manager, Engineer 和 Reviewer

## 目标 (Objective)
将当前的 Agent 角色划分简化为三个核心角色：**Manager**、**Engineer** 和 **Reviewer**。这种精简的结构旨在理清责任并提高开发工作流的效率。

角色定义如下：
1.  **Manager**: 负责需求分析。将来自用户或 Memo Inbox 的模糊需求转化为结构化、清晰的 Issue Ticket。及时与用户交互以澄清歧义。
2.  **Engineer**: 负责执行。实现 Issue Ticket 中约定的工作，编写单元测试以验证功能，并提交 Issue 进行审查。
3.  **Reviewer**: 负责质量保证和集成。独立审查实现进度。根据 Issue 的重要性，可选择性地等待人工确认，然后合并到主分支并清理 Issue 分支。

## 验收标准 (Acceptance Criteria)
- [ ] 系统中的 Agent 角色定义已更新为仅包含 Manager, Engineer 和 Reviewer。
- [ ] **Manager Role**:
    - [ ] 能够访问和处理 Memo Inbox 中的条目。
    - [ ] 能够与用户交互以澄清需求。
    - [ ] 能够从模糊输入创建结构化的 Issue Ticket。
- [ ] **Engineer Role**:
    - [ ] 能够阅读并理解 Issue Ticket。
    - [ ] 能够实现代码更改并编写单元测试。
    - [ ] 能够提交 Issue（流转至审查状态）。
- [ ] **Reviewer Role**:
    - [ ] 能够审查代码更改和测试结果。
    - [ ] 能够将更改合并到主分支。
    - [ ] 能够在合并后清理特性分支。
    - [ ] 支持在合并关键 Issue 前进行可选的“等待人工确认”步骤。
- [ ] 移除现有角色（Planner, Builder, Merger, Coroner 等）或将其映射到新的三个角色。
- [ ] 与 Agent 相关的 CLI 命令反映这些更改（例如 `monoco agent role list`）。

## 技术任务 (Technical Tasks)
- [ ] **角色定义更新 (Role Definition Update)**:
    - [ ] 修改 `monoco/core/agent/roles.py` (或等效配置) 以定义 Manager, Engineer 和 Reviewer。
    - [ ] 移除已弃用的角色 (Planner, Builder, Merger, Coroner)。
- [ ] **Manager 实现 (Manager Implementation)**:
    - [ ] 实现获取 Memo 并将其转换为草稿 Issue 的逻辑。
    - [ ] 实现需求澄清的交互循环。
- [ ] **Engineer 实现 (Engineer Implementation)**:
    - [ ] 更新 Engineer 的 Prompt/Context，专注于基于特定 Issue Ticket 的实现和测试。
- [ ] **Reviewer 实现 (Reviewer Implementation)**:
    - [ ] 更新 Reviewer 的 Prompt/Context，专注于代码审查、安全检查和合并。
    - [ ] 实现关键 Issue 的“人工确认”关卡逻辑。
- [ ] **工作流集成 (Workflow Integration)**:
    - [ ] 确保 `monoco agent` 工作流中 Manager -> Engineer -> Reviewer 的切换顺畅。
- [ ] **CLI 更新 (CLI Updates)**:
    - [ ] 更新 `monoco agent role list` 以显示新角色。
    - [ ] 更新任何其他引用硬编码角色的 CLI 命令。
- [ ] **文档 (Documentation)**:
    - [ ] 更新系统文档以反映新的 3 角色结构。

## Review Comments
<!-- Recommended for Review/Done stage. Record review feedback here. -->
