---
id: FEAT-0123
uid: 6ad2dd
type: feature
status: open
stage: draft
title: Migrate Core Features to Flow Skills Pattern
created_at: '2026-01-30T17:45:07'
updated_at: '2026-01-30T17:45:07'
parent: EPIC-0022
dependencies:
- FEAT-0122
related:
- FEAT-0122
- FEAT-0121
domains:
- Guardrail
tags:
- '#EPIC-0022'
- '#FEAT-0123'
files:
- monoco/features/i18n/resources/skills/
- monoco/features/spike/resources/skills/
- monoco/features/issue/resources/skills/
- monoco/features/memo/resources/skills/
opened_at: '2026-01-30T17:45:07'
---

## FEAT-0123: Migrate Core Features to Flow Skills Pattern

## 目标 (Objective)

将核心 Feature（i18n, spike, issue, memo）从 **Command Reference 模式** 升级为 **双模式架构**（Command Reference + Flow Skills）。

当前这些 Feature 的 AGENTS.md 只提供命令参考（What），缺乏标准化工作流程（How & When）。通过引入 Flow Skills，为每个 Feature 定义标准操作流程（SOP），实现 Agent 工作流的约束和编排。

**依赖**: 必须等待 FEAT-0122（SkillManager 增强）完成后才能实施。

**核心价值**:
- 从"工具集合"升级为"工作流编排"
- 防止 Agent 在使用 Feature 时跳过关键步骤
- 统一所有 Feature 的交互模式

## 核心需求 (Core Requirements)

1. **i18n Flow Skills**:
   - `i18n-scan-workflow`: 扫描 → 识别缺失 → 生成翻译任务
   - `i18n-sync-workflow`: 翻译 → 验证 → 同步

2. **Spike Flow Skills**:
   - `research-workflow`: 添加仓库 → 同步 → 分析 → 提取知识 → 归档
   - `spike-maintenance-workflow`: 定期同步 → 过期检测 → 清理

3. **Issue Flow Skills**:
   - `issue-lifecycle-workflow`: Open → Start → Develop → Submit → Review → Close
   - `issue-planning-workflow`: Epic 拆解 → 依赖分析 → 任务分配

4. **Memo Flow Skills**:
   - `note-processing-workflow`: 捕获 → 处理 → 组织 → 归档/转化

## 验收标准 (Acceptance Criteria)

- [ ] i18n Feature 包含至少 1 个 Flow Skill
- [ ] spike Feature 包含至少 1 个 Flow Skill
- [ ] issue Feature 包含至少 1 个 Flow Skill（复用 scheduler 的 flow）
- [ ] memo Feature 包含至少 1 个 Flow Skill
- [ ] 每个 Flow Skill 都有完整的状态机图（Mermaid）
- [ ] 每个 Flow Skill 都有明确的检查点（Checkpoints）
- [ ] `monoco sync` 正确注入所有 Flow Skills
- [ ] AGENTS.md 保留作为 Command Reference

## 技术任务 (Technical Tasks)

- [ ] **i18n Flow Skills**
  - [ ] 创建 `monoco/features/i18n/resources/skills/i18n-scan-workflow/SKILL.md`
  - [ ] 定义扫描 → 识别 → 任务生成的状态机
  - [ ] 定义检查点和合规要求

- [ ] **Spike Flow Skills**
  - [ ] 创建 `monoco/features/spike/resources/skills/research-workflow/SKILL.md`
  - [ ] 定义研究流程状态机
  - [ ] 定义知识提取和归档的检查点

- [ ] **Issue Flow Skills**
  - [ ] 评估是否复用 scheduler 的 flow_engineer
  - [ ] 或创建 issue 专属的 `issue-lifecycle-workflow`
  - [ ] 定义 Issue 生命周期状态机

- [ ] **Memo Flow Skills**
  - [ ] 创建 `monoco/features/memo/resources/skills/note-processing-workflow/SKILL.md`
  - [ ] 定义备忘录处理流程（Inbox → Process → Organize）

- [ ] **验证与测试**
  - [ ] 运行 `monoco sync` 验证所有 Flow Skills 被正确注入
  - [ ] 验证 `.agent/skills/` 目录结构正确
  - [ ] 验证 Kimi CLI 能识别 `/flow:*` 命令

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
