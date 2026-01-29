---
id: FEAT-0103
uid: d4e5f6
type: feature
status: closed
stage: done
title: 实现配置驱动的角色加载机制
created_at: '2026-01-25T14:30:00'
updated_at: '2026-01-25T23:19:11'
priority: high
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0008'
- '#FEAT-0103'
files:
- monoco/features/scheduler/config.py
- monoco/features/scheduler/defaults.py
- monoco/features/scheduler/models.py
closed_at: '2026-01-25T23:19:11'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0103-实现配置驱动的角色加载机制
  created_at: '2026-01-25T23:13:37'
---

## FEAT-0103: 实现配置驱动的角色加载机制

### 目标
将 Role 定义从硬编码的 Python 列表迁移到基于 YAML 的配置系统。支持从用户目录和项目目录加载和覆盖角色定义。

### 背景
目前 `DEFAULT_ROLES` 在 `monoco/features/scheduler/defaults.py` 中硬编码。这导致用户无法：
1. 修改现有角色的 System Prompt。
2. 为特定项目添加自定义角色（如 "Rust专家"）。
3. 调整使用的工具集。

### 需求
1. **配置文件格式**: 定义标准的 `roles.yaml` 结构。
2. **加载优先级**:
   - Level 1: 内置默认值 (Fallback)
   - Level 2: 用户全局配置 (`~/.monoco/roles.yaml`)
   - Level 3: 项目本地配置 (`./.monoco/roles.yaml`)
     *Priority: Level 3 > Level 2 > Level 1 (名字相同的 Role 进行覆盖/Merge)。*
3. **命令支持**: `monoco role list` 显示当前生效的所有角色及其来源。

### 任务
- [x] 定义 `roles.yaml` Schema (基于 Pydantic Model)。
- [x] 实现 `RoleLoader` 类，支持层级加载和字典合并。
- [x] 重构 `ApoptosisManager` 和 CLI 使用 `RoleLoader` 而非硬编码 Defaults。
- [x] 添加 `monoco role list` 命令。
- [x] 验证 Level 1-3 覆盖逻辑。

## Review Comments
- 2026-01-25: Implemented `RoleLoader` with tiered support (builtin, home, project). Added `monoco role list` command. Verified override logic via project-local configuration.
