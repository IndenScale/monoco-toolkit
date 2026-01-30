---
id: FEAT-0121
uid: 7b2d4f
type: feature
status: closed
stage: done
closed_at: '2026-01-30T17:15:00'
solution: implemented
title: Define Standard Agent Workflows via Flow Skills
created_at: '2026-01-30T16:55:10'
updated_at: '2026-01-30T16:55:10'
parent: EPIC-0022
dependencies: []
related: []
domains:
- Guardrail
tags:
- '#FEAT-0121'
- '#EPIC-0022'
files:
- monoco/features/scheduler/flow_skills.py
- monoco/features/scheduler/resources/skills/flow_engineer/SKILL.md
- monoco/features/scheduler/resources/skills/flow_manager/SKILL.md
- monoco/features/scheduler/resources/skills/flow_reviewer/SKILL.md
- tests/test_flow_skills.py
- AGENTS.md
opened_at: '2026-01-30T16:55:10'
---

## FEAT-0121: Define Standard Agent Workflows via Flow Skills

## 目标 (Objective)
为核心角色 (Manager, Engineer, Reviewer) 定义标准化的操作流程 (SOP)。
防止 Agent 在执行复杂任务时“发散”或跳过关键步骤（如跳过测试直接提交）。
利用 **Flow Skills (Mermaid/D2)** 作为统一的工作流定义语言，实现“设计即代码”。

## 核心需求 (Core Requirements)
1.  **Unified Flow Definition (Flow Skills)**:
    - 采用 **Kimi CLI Flow Skill** 格式 (`type: flow` + Mermaid) 定义所有核心角色的工作流。
    - **Free Lunch 策略**:
        - **Kimi CLI 环境**: 使用 `/flow:<role>` 强制执行状态机，确保步骤原子性和顺序性。
        - **通用 Agent 环境**: 将 Mermaid 流程图作为 `Context` 注入 System Prompt。利用 LLM 对结构化图形的理解能力，实现隐式约束。
    - **Single Source of Truth**: 同一份 `SKILL.md` 既是 Agent 的执行代码，也是人类阅读的 SOP 文档。

2.  **Standard Workflows**:
    - **Engineer Flow**:
        ```mermaid
        Investigate -> Code -> Test -> Report -> Submit
        ```
        必须包含循环测试机制。
    - **Manager Flow**:
        Inbox 整理 -> 需求澄清 -> 任务拆解 -> 指派。
    - **Reviewer Flow**:
        Checkout -> Test -> Review (Diff) -> Approve/Reject -> Cleanup。

3.  **Implementation Architecture**:
    - **Storage**: 定义在 `monoco/features/scheduler/resources/skills/`，采用多目录结构：
        - `flow_engineer/SKILL.md` (type: flow)
        - `flow_manager/SKILL.md` (type: flow)
        - `flow_reviewer/SKILL.md` (type: flow)
    - **Injection Mechanism (Multi-Skill Sync)**:
        - 由于 Kimi Flow Skill 限制（一个文件对应一个 Flow），我们需要注入多个独立的 Skill 目录。
        - 启动时，遍历 resource 目录，将每个子目录复制到用户项目的 `.agent/skills/` 下，并添加 `monoco_` 前缀（如 `monoco_flow_engineer`）。
        - 这样 Kimi CLI 可以识别出 `/flow:engineer`, `/flow:manager` 等多个命令。
        - `.gitignore` 配置忽略 `monoco_flow_*/`。

## 验收标准 (Acceptance Criteria)
- [x] 核心角色 (Engineer, Manager, Reviewer) 分别拥有独立的 Flow Skill 目录。
- [x] **Injection Test**: 运行后，`.agent/skills/` 下出现 `monoco_flow_engineer/`, `monoco_flow_manager/` 等目录。
- [x] **Kimi Compatibility**: Kimi CLI 能正确识别所有注入的 `/flow:*` 命令。
- [x] 流程图包含必要的决策分支。

## 技术任务 (Technical Tasks)
- [x] **Resource Structure**: 在 `monoco/features/scheduler/resources/skills/` 下建立 `flow_engineer`, `flow_manager`, `flow_reviewer` 三个子目录。
- [x] **Design Flows**: 分别绘制三个角色的 Mermaid 状态机图。
- [x] **Implement Scaffolding Injection**: 编写 `sync_flow_skills` 函数，支持遍历复制多个目录并在目标端添加前缀。
- [x] **Gitignore Handling**: 自动将 `monoco_flow_*` 添加到 `.gitignore`。
- [x] **Unit Tests**: 编写完整的单元测试 (30 个测试用例全部通过)。
- [x] **Docs**: 更新 `AGENTS.md` 列出所有可用的 Standard Flows。

## Review Comments

- 所有 30 个单元测试通过
- Flow Skills 结构符合 Kimi CLI Flow Skill 规范
- Gitignore 自动处理已验证
- AGENTS.md 已更新，包含 Standard Flows 文档
