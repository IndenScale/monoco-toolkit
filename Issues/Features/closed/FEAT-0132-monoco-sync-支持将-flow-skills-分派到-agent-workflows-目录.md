---
id: FEAT-0132
uid: fa578a
type: feature
status: closed
solution: implemented
stage: done
title: monoco sync 支持将 flow skills 分派到 .agent/workflows 目录以兼容 Antigravity IDE
created_at: '2026-01-31T22:36:09'
updated_at: 2026-01-31 22:36:36
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0132'
files:
- monoco/core/workflow_converter.py
- monoco/core/skills.py
- monoco/core/sync.py
criticality: medium
opened_at: '2026-01-31T22:36:09'
isolation:
  type: branch
  ref: feat/feat-0132-monoco-sync-支持将-flow-skills-分派到-agent-workflows-目录
  path: null
  created_at: '2026-01-31T22:36:36'
---

## FEAT-0132: monoco sync 支持将 flow skills 分派到 .agent/workflows 目录以兼容 Antigravity IDE

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->

Antigravity IDE 支持 Workflows 功能，允许用户通过 `/workflow-name` 命令触发预定义的工作流。Monoco Toolkit 的 Flow Skills 与 Antigravity Workflows 概念相似，但格式不同。本功能旨在让 `monoco sync` 命令能够将 Flow Skills 自动转换为 Antigravity Workflows 格式并分派到 `.agent/workflows/` 目录，使用户可以在 Antigravity IDE 中使用 Monoco 的工作流。

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] `monoco sync` 命令新增 `--workflows` 或 `-w` 选项，用于启用 Workflow 分派
- [x] Flow Skills 被正确转换为 Antigravity Workflow 格式（简化 frontmatter，保留核心步骤）
- [x] 转换后的 Workflows 保存到 `.agent/workflows/` 目录，文件名为 `flow-{role}.md`
- [x] 支持所有现有的 Flow Skills（flow-engineer, flow-planner, flow-manager, flow-reviewer 等）
- [x] 转换过程中丢弃不必要的元数据（type, role, version, author），仅保留 description
- [x] 内容结构从状态机图转换为简单的步骤列表
- [x] `monoco uninstall` 能够清理分派到 `.agent/workflows/` 的 flow skills

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

- [x] 调研 Antigravity Workflow 格式要求（参考 `.references/antigravity-docs/workflows.md`）
- [x] 设计 Flow Skill 到 Workflow 的转换逻辑
  - [x] 创建 `monoco/core/workflow_converter.py` 模块
  - [x] 实现 frontmatter 转换（保留 description，丢弃其他元数据）
  - [x] 实现内容转换（Mermaid 状态机 → 步骤列表，检查点 → 简单列表）
- [x] 修改 `monoco/core/skills.py` 中的 `SkillManager`
  - [x] 添加 `distribute_workflows()` 方法
  - [x] 添加 `cleanup_workflows()` 方法
- [x] 修改 `monoco/core/sync.py`
  - [x] 在 `sync_command` 中添加 `--workflows` / `-w` 选项
  - [x] 在 `uninstall_command` 中添加 workflows 清理逻辑
- [x] 测试验证
  - [x] 运行 `monoco sync --workflows` 验证 workflows 被正确生成
  - [x] 验证生成的 workflow 文件格式符合 Antigravity 要求
  - [x] 运行 `monoco uninstall` 验证 workflows 被正确清理

## Implementation Notes

### Antigravity Workflow 格式示例
```markdown
---
description: Engineer 角色的标准化工作流。定义从需求调研到代码提交的标准操作流程。
---

## 工作流步骤

1. **Investigate (调研)**
   - 阅读并理解 Issue 描述
   - 识别相关代码文件
   - 检查依赖 Issue 状态
   - 评估技术可行性

2. **Code (编码)**
   - 遵循项目代码规范
   - 编写/更新必要的文档
   - 处理边界情况
...
```

### 转换规则
1. **Frontmatter**: 只保留 `description`，丢弃 `name`, `type`, `role`, `version`, `author`
2. **文件名**: `monoco_flow_engineer/SKILL.md` → `flow-engineer.md`
3. **内容**: 移除 Mermaid 状态机图，将阶段和检查点转换为简单列表
4. **目录**: 输出到 `.agent/workflows/`（而非 `.agent/skills/`）

## Related Files
- `.references/antigravity-docs/workflows.md` - Antigravity Workflow 文档
- `.references/antigravity-docs/skills.md` - Antigravity Skills 文档
- `monoco/core/skills.py` - SkillManager 实现
- `monoco/core/sync.py` - sync 命令实现
- `monoco/core/workflow_converter.py` - Flow Skill 到 Workflow 转换器（新增）
- `monoco/features/*/resources/*/skills/flow_*/SKILL.md` - Flow Skills 源文件

## Implementation Summary

### 新增文件
- `monoco/core/workflow_converter.py` - 实现 Flow Skill 到 Antigravity Workflow 的转换逻辑

### 修改文件
- `monoco/core/skills.py` - 添加 `distribute_workflows()` 和 `cleanup_workflows()` 方法
- `monoco/core/sync.py` - 添加 `--workflows` / `-w` 选项和 uninstall 清理逻辑

### 转换规则
1. **Frontmatter**: 只保留 `description`，丢弃 `name`, `type`, `role`, `version`, `author`
2. **文件名**: `flow_engineer/SKILL.md` → `flow-engineer.md`
3. **内容**: 移除 Mermaid 状态机图，将阶段和检查点转换为简单列表
4. **目录**: 输出到 `.agent/workflows/`

## Review Comments

### 验收结果 (2026-01-31)

**验收人**: 当前 Agent
**状态**: ✅ 通过

**验收项目**:
1. ✅ `monoco sync --workflows` 选项正常工作
2. ✅ Flow Skills 正确转换为 Antigravity Workflow 格式
3. ✅ 生成的 workflows 保存到 `.agent/workflows/` 目录
4. ✅ 所有 11 个 Flow Skills 成功转换
5. ✅ Frontmatter 只保留 description，其他元数据已丢弃
6. ✅ Mermaid 状态机图被移除，内容转换为步骤列表
7. ✅ `monoco uninstall` 正确清理 workflows

**合并信息**:
- 分支: `feat/feat-0132-monoco-sync-支持将-flow-skills-分派到-agent-workflows-目录`
- 合并提交: `main` 分支已合并
- 新增文件: `monoco/core/workflow_converter.py`
- 修改文件: `monoco/core/skills.py`, `monoco/core/sync.py`
