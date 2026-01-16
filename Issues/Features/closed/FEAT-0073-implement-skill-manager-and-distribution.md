---
id: FEAT-0073
uid: 44918e
type: feature
status: closed
stage: done
title: Implement Skill Manager and Distribution
created_at: '2026-01-15T15:56:16'
opened_at: '2026-01-15T15:56:16'
updated_at: '2026-01-15T17:03:40'
closed_at: '2026-01-15T17:03:40'
parent: EPIC-0014
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0073: Implement Skill Manager and Distribution

## 背景 (Context)

通过对 `Cursor`, `Antigravity`, `Gemini CLI`, `Qwen Code` 等主流 Agent 框架的调研，确认 **Agent Skills (SKILL.md)** 已成为事实上的行业标准。

该标准的核心特征（参考 `agentskills.io`）：

1. **统一格式**: 均为包含 YAML Frontmatter 的 `SKILL.md` 文件。
2. **统一结构**: `Skill Folder` -> `SKILL.md` + Resources。
3. **多端分发**: 仅需将 Skill 目录分发到不同框架的约定路径（如 `.cursor/skills`, `.claude/skills`）即可生效。

目前 Monoco 缺乏统一的 Skill 管理与分发机制，且缺乏对 Skill 内容规范性的校验。

## 目标 (Objective)

实现 **Monoco Skill Manager**，作为 Skill 的 "Source of Truth" 和 "Distribution Hub"。

核心能力：

1. **Skill Registry**: 在 Monoco 内部统一管理 Standard Skills (如 `issue_management`, `git_workflow` 等)。
2. **Standard Compliance**: 确保所有内建及分发的 Skill 严格符合 `agentskills.io` 规范（Name, Description 等）。
3. **Multi-Target Sync**: 在 `monoco sync` 时，自动将 Skill 分发到配置指定的所有目标框架目录中。

## 策略 (Strategy)

采用 **"Write Once, Distribute Everywhere"** 策略。

1. **Content Standard**: 严格遵循 `agentskills.io` 规范。
2. **Path Adapter**: `SkillManager` 利用 **Core Integration Registry (FEAT-0074)** 来适配各家 Agent 的路径差异。
3. **Smart Sync**: 使用 Checksum 或 Timestamp 确保仅更新变更的文件，且支持 `monoco uninstall` 清理。

## 验收标准 (Acceptance Criteria)

- [x] **Standard Adherence**: 内建的 `monoco-issue` 技能必须完全符合 `agentskills.io` 规范（包括 YAML Frontmatter 字段检查）。
- [x] **Distribution Logic**: `monoco sync` 能够根据配置将技能文件复制到 `.cursor/skills/monoco_issue/SKILL.md` 等目标路径，且保持目录结构完整。
- [x] **Configuration**: 支持在 `.monoco/config.yaml` 中配置语言（`i18n.source_lang`）和集成（通过 FEAT-0074）。
- [x] **Cleanup**: `monoco uninstall` 能够移除分发出去的技能文件及空目录。

## 技术任务 (Technical Tasks)

- [x] **Core**: 创建 `monoco/core/integrations.py`。（由 FEAT-0074 完成）
  - 定义 `AgentIntegration` 数据类 (prompt_file, skill_dir)。
  - 定义 `DEFAULT_INTEGRATIONS` 常量表。
- [x] **Config**: 更新 `MonocoConfig` 的 `AgentConfig`。（由 FEAT-0074 完成）
  - 增加 `integrations` 字段允许用户覆盖默认路径。
- [x] **Skills**: 创建内置技能（采用分布式架构，每个 Feature 维护自己的 skill）
  - 创建 `monoco-core` 技能 (en + zh)
  - 创建 `monoco-issue` 技能 (en + zh)
  - 创建 `monoco-spike` 技能 (en + zh)
  - 创建 `monoco-i18n` 技能 (en + zh)
- [x] **Core**: 实现 `SkillManager` 类 (`monoco/core/skills.py`)
  - `list_skills()`: 获取所有可用技能
  - `distribute(target_dir, lang)`: 执行分发逻辑（支持语言配置）
  - `cleanup(target_dir)`: 清理逻辑
- [x] **Integration**: 更新 `monoco/core/sync.py`，在 `sync_command` 中调用 `SkillManager.distribute()`
- [x] **Integration**: 更新 `monoco/core/sync.py`，在 `uninstall_command` 中调用 `SkillManager.cleanup()`

## 实现总结 (Implementation Summary)

### 架构设计

采用 **"分布式 Skill 管理"** 架构，而非集中式目录：

1. **每个 Feature 维护自己的 resources**:

   - `monoco/features/{feature}/resources/{lang}/AGENTS.md` - 系统提示词
   - `monoco/features/{feature}/resources/{lang}/SKILL.md` - 完整技能文档
   - `monoco/core/resources/{lang}/` - Core 特殊处理

2. **SkillManager 动态发现**:

   - 从 Feature Registry 收集 skills
   - 从 `monoco/core/resources/` 发现 core skill
   - 验证 metadata 符合 agentskills.io 标准

3. **单语言分发策略**:
   - 根据 `config.i18n.source_lang` 只分发一个语言版本
   - 目标路径: `.{framework}/skills/{skill_name}/SKILL.md`
   - Skill name: kebab-case (如 `monoco-issue`)
   - 目录名: snake_case (如 `monoco_issue`)

### 已创建的 Skills

| Skill | Name (metadata) | Directory      | Languages | Status |
| ----- | --------------- | -------------- | --------- | ------ |
| Core  | `monoco-core`   | `monoco_core`  | en, zh    | ✅     |
| Issue | `monoco-issue`  | `monoco_issue` | en, zh    | ✅     |
| Spike | `monoco-spike`  | `monoco_spike` | en, zh    | ✅     |
| I18n  | `monoco-i18n`   | `monoco_i18n`  | en, zh    | ✅     |

### 分发结果

成功分发到 4 个 agent 框架：

- `.claude/skills/` - Claude Code
- `.gemini/skills/` - Gemini CLI
- `.qwen/skills/` - Qwen Code
- `.agent/skills/` - Antigravity

每个框架接收 4 个 skills，根据配置语言（当前为 `zh`）分发中文版本。

### 关键实现

1. **`monoco/core/skills.py`**:

   - `SkillMetadata`: Pydantic 模型验证 frontmatter
   - `Skill`: 表示单个 skill，支持多语言检测
   - `SkillManager`: 核心管理器，负责发现、分发、清理

2. **集成到 sync 流程**:

   - `monoco sync`: 分发 skills 到所有检测到的框架
   - `monoco uninstall`: 清理分发的 skills

3. **Checksum 增量更新**:
   - 使用 SHA256 校验和避免重复复制
   - 仅在内容变化时更新文件

### 设计亮点

- **Write Once, Distribute Everywhere**: 维护一份源，分发到多个框架
- **Language-Aware**: 根据用户配置自动选择语言版本
- **Standard Compliant**: 严格遵循 agentskills.io 规范
- **Feature-Centric**: 每个 Feature 拥有自己的文档和技能
- **Type-Safe**: 使用 Pydantic 确保 metadata 正确性

## Review Comments

- [x] Self-Review
