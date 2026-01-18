---
id: FEAT-0074
uid: 840b6c
type: feature
status: closed
stage: done
title: Core Integration Registry
created_at: "2026-01-15T16:32:44"
opened_at: "2026-01-15T16:32:44"
updated_at: "2026-01-15T17:03:45"
closed_at: "2026-01-15T17:03:45"
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0074: Core Integration Registry

## 背景 (Context)

随着 Monoco 支持的 Agent 框架日益增多（Cursor, Claude, Gemini, Qwen, Antigravity），各框架的配置文件路径（如 `.cursorrules`, `GEMINI.md`）和技能目录路径（如 `.cursor/skills`, `.gemini/skills`）目前在代码中处于硬编码或分散状态，缺乏统一管理。

这导致:

1. **维护困难**: 新增支持一个框架需要修改多处代码。
2. **配置僵化**: 用户无法轻易覆盖默认路径。

## 目标 (Objective)

建立一个统一的 **Core Integration Registry**，作为 Monoco 与外部 Agent 环境交互的 "地图"。

## 策略 (Strategy)

1. **Centralized Registry**: 在 `monoco.core.integrations` 中维护一份全量映射表 `INTEGRATION_MAP`。
2. **Config Override**: 允许用户在 `.monoco/config.yaml` 中通过 `agent.integrations` 覆盖默认映射。
3. **Smart Detection**: 提供工具函数 `detect_active_frameworks(root)`，根据文件存在性自动判断当前项目适用的框架。

### 默认集成表 (Default Registry)

| Framework       | Key      | System Prompt File | Skill Root Dir    |
| :-------------- | :------- | :----------------- | :---------------- |
| **Cursor**      | `cursor` | `.cursorrules`     | `.cursor/skills/` |
| **Claude Code** | `claude` | `CLAUDE.md`        | `.claude/skills/` |
| **Gemini CLI**  | `gemini` | `GEMINI.md`        | `.gemini/skills/` |
| **Qwen Code**   | `qwen`   | `QWEN.md`          | `.qwen/skills/`   |
| **Antigravity** | `agent`  | `GEMINI.md`        | `.agent/skills/`  |

## 验收标准 (Acceptance Criteria)

- [x] **Data Structure**: 定义清晰的 `AgentIntegration` 数据类。
- [x] **Registry**: 实现包含所有主流框架默认配置的 Registry。
- [x] **Configuration**: `MonocoConfig` 支持加载和合并用户自定义的集成配置。
- [x] **Detection**: 能够自动检测当前目录下存在的框架特征文件。

## 技术任务 (Technical Tasks)

- [x] **Core**: 创建 `monoco/core/integrations.py`。
  - class `AgentIntegration(BaseModel)`
  - const `DEFAULT_INTEGRATIONS: Dict[str, AgentIntegration]`
  - func `get_integration(name: str, config: Config) -> AgentIntegration`
  - func `detect_frameworks(root: Path) -> List[str]`
- [x] **Config**: 更新 `monoco/core/config.py`。
  - 在 `AgentConfig` 中添加 `integrations: Dict[str, AgentIntegration]` 字段。
- [x] **Refactor**: 标记 `monoco/core/sync.py` 中的硬编码逻辑为 Deprecated (将在后续 Feature 中替换)。

## 实现总结 (Implementation Summary)

### 已完成的工作

1. **核心模块** (`monoco/core/integrations.py`):
   - 定义了 `AgentIntegration` Pydantic 模型
   - 创建了包含 5 个主流框架的 `DEFAULT_INTEGRATIONS` 注册表
   - 实现了 `get_integration()` 函数,支持配置覆盖
   - 实现了 `get_all_integrations()` 函数,支持合并和过滤
   - 实现了 `detect_frameworks()` 函数,基于文件存在性自动检测
   - 实现了 `get_active_integrations()` 函数,结合检测和配置

2. **配置支持** (`monoco/core/config.py`):
   - 在 `AgentConfig` 中添加了 `integrations` 字段
   - 支持用户通过 `.monoco/config.yaml` 自定义集成配置

3. **代码重构** (`monoco/core/sync.py`):
   - 标记硬编码的默认文件列表为 Deprecated
   - 添加 TODO 注释,指向集成注册表的使用

4. **测试覆盖** (`tests/test_integrations.py`):
   - 创建了完整的单元测试套件
   - 覆盖所有核心功能和边界情况

5. **文档** (`docs/core-integration-registry.md`):
   - 编写了详细的使用文档
   - 包含概念说明、使用示例和 API 参考

### 设计亮点

- **三层优先级**: 默认注册表 < 用户配置 < 运行时检测
- **类型安全**: 使用 Pydantic 确保配置结构正确
- **向后兼容**: 保留现有 `sync.py` 逻辑,仅标记为 Deprecated
- **可扩展性**: 轻松添加新框架或自定义集成

## Review Comments

- [x] Self-Review
