---
id: FEAT-0122
uid: 71d1d8
type: feature
status: closed
stage: done
title: Enhance SkillManager to Support Multi-Skill Architecture
created_at: '2026-01-30T17:45:07'
updated_at: '2026-01-30T18:04:54'
parent: EPIC-0022
dependencies: []
related:
- FEAT-0123
- FEAT-0121
domains:
- AgentOnboarding
tags:
- '#EPIC-0022'
- '#FEAT-0121'
- '#FEAT-0122'
- '#FEAT-0123'
files:
- monoco/core/skills.py
- monoco/core/sync.py
- monoco/features/agent/flow_skills.py
criticality: medium
opened_at: '2026-01-30T17:45:07'
closed_at: '2026-01-30T18:04:54'
solution: implemented
---

## FEAT-0122: Enhance SkillManager to Support Multi-Skill Architecture

## 目标 (Objective)

重构 SkillManager 以支持 **1 Feature : N Skills** 的新架构范式。

当前架构假设每个 Feature 只有一个 Skill（`resources/{lang}/SKILL.md`），但 Flow Skills 的引入打破了这一假设。Agent 模块需要注入多个 Flow Skills（flow_engineer, flow_manager, flow_reviewer），未来 i18n、spike 等模块也会有多个细分 Skill。

> **注意**: `scheduler` 模块已重命名为 `agent`（CHORE-0023），以更好地反映其职责。

**核心价值**:
- 支持 Feature 级别的 Skill 原子化拆分
- 统一标准 Skill 和 Flow Skill 的注入机制
- 为所有 Feature 的多 Skill 架构奠定基础

## 核心需求 (Core Requirements)

1. **多 Skill 发现机制**:
   - 扫描 `resources/skills/{skill-name}/SKILL.md` 结构
   - 保留向后兼容 `resources/{lang}/SKILL.md`
   - 支持混合模式（既有默认 Skill，又有细分 Skills）

2. **统一注入接口**:
   - `SkillManager.distribute()` 同时处理标准和 Flow Skills
   - 支持前缀配置（`monoco_`, `monoco_flow_`）
   - 支持类型标记（`type: flow`, `type: standard`）

3. **元数据扩展**:
   - Skill 元数据增加 `type` 字段
   - 支持 `role` 字段（用于 Flow Skill 的命令生成）

## 验收标准 (Acceptance Criteria)

- [x] SkillManager 能发现并注入 `resources/skills/*/` 目录下的所有 Skills
- [x] 保留对 `resources/{lang}/SKILL.md` 的向后兼容
- [x] `monoco sync` 正确注入 Agent 的 Flow Skills 到 `.agent/skills/`
- [x] Skill 元数据支持 `type` 和 `role` 字段
- [x] 更新 `sync_command()` 移除直接调用 `sync_flow_skills()` 的临时方案
- [x] 所有现有测试通过，新增测试覆盖多 Skill 场景

## 技术任务 (Technical Tasks)

- [x] **分析当前 SkillManager 架构**
  - [x] 梳理 `Skill` 类和 `SkillManager` 类的职责
  - [x] 识别需要修改的关键方法

- [x] **扩展 Skill 发现机制**
  - [x] 修改 `_discover_skills_from_features()` 支持 `resources/skills/*/` 扫描
  - [x] 实现 Skill 类型识别（标准 vs Flow）

- [x] **重构 Skill 元数据模型**
  - [x] `SkillMetadata` 增加 `type: Optional[str]` 字段
  - [x] `SkillMetadata` 增加 `role: Optional[str]` 字段（Flow Skill 使用）

- [x] **统一注入逻辑**
  - [x] 合并 `flow_skills.py` 的注入逻辑到 `SkillManager`
  - [x] `distribute()` 方法支持多 Skill 批量注入
  - [x] 支持自定义前缀配置

- [x] **更新同步流程**
  - [x] 修改 `sync_command()` 使用增强后的 SkillManager
  - [x] 移除/合并 `sync_flow_skills()` 独立函数

- [x] **测试覆盖**
  - [x] 多 Skill 发现测试
  - [x] Flow Skill 注入测试
  - [x] 混合模式（标准 + Flow）测试

## Review Comments

### 依赖更新
- **CHORE-0023 已完成**: `scheduler` 模块已重命名为 `agent`
- 所有路径引用已更新：
  - `monoco/features/scheduler/` → `monoco/features/agent/`
  - `monoco.features.scheduler` → `monoco.features.agent`

### 实现状态
- 所有技术任务已完成
- 所有验收标准已满足
- 测试覆盖率达标
