---
id: FEAT-0174
uid: 41571d
type: feature
status: open
stage: review
title: 'Universal Hooks: Core Models and Parser'
created_at: '2026-02-04T13:27:07'
updated_at: '2026-02-04T14:10:11'
parent: EPIC-0034
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0034'
- '#FEAT-0174'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T13:27:07'
isolation:
  type: branch
  ref: branch:FEAT-0174-universal-hooks-core-models-and-parser
  created_at: '2026-02-04T13:56:58'
---

## FEAT-0174: Universal Hooks: Core Models and Parser

## 目标

实现通用 Hooks 系统的基础模型和 Front Matter 解析器，为 Git/Agent/IDE 三种类型的 Hooks 提供统一的元数据定义和解析能力。

## 验收标准

- [x] 定义 `HookType` Enum: `git`, `ide`, `agent`
- [x] 实现 `HookMetadata` Pydantic 模型：
  - [x] 基础字段：`type`, `event`, `matcher`, `priority`, `description`
  - [x] 条件字段：`provider` (当 type=agent/ide 时必填)
- [x] 实现 `HookParser`，支持从脚本头部解析 YAML Front Matter
- [x] 支持多语言注释风格：`#` (Shell/Python), `//` (JS/TS), `--` (Lua/SQL)
- [x] 实现 `UniversalHookManager` 核心类框架：
  - [x] `scan(directory)`: 递归扫描并按 `type` + `provider` 分组
  - [x] `validate(hook)`: 校验元数据完整性

## 技术任务

### 模型定义
- [x] 定义 `HookType` Enum: `git`, `ide`, `agent`
- [x] 定义 `HookMetadata` Pydantic 模型：
  - [x] 基础字段：`type` (HookType), `event`, `matcher`, `priority`, `description`
  - [x] Provider 字段：`provider` (Optional[str], 当 type=agent/ide 时必填)
- [x] 定义各类型的事件枚举：
  - [x] `GitEvent`: pre-commit, prepare-commit-msg, commit-msg, post-merge, pre-push
  - [x] `AgentEvent`: session-start, before-tool, after-tool, before-agent, after-agent
  - [x] `IDEEvent`: on-save, on-open, on-close, on-build

### Front Matter 解析器
- [x] 实现 `HookParser` 类
  - [x] 从脚本头部提取 YAML Front Matter
  - [x] 支持多行注释边界检测 (`# ---` / `# ---`)
  - [x] 支持多语言注释风格检测
- [x] 实现解析错误处理和行号定位
- [x] 编写单元测试覆盖各种注释风格 (74 个测试通过)

### UniversalHookManager 框架
- [x] 创建 `monoco/features/hooks/universal_manager.py`
- [x] 实现 `UniversalHookManager` 类框架
  - [x] `scan(directory)`: 递归扫描 Hook 脚本，按 `type` + `provider` 分组返回
  - [x] `validate(hook)`: 校验元数据（如 type=agent 时 provider 必填）
  - [x] `register_dispatcher(type, dispatcher)`: 注册类型分发器（为后续 Feature 预留）

## Review Comments

验收通过。

1. **模型定义**: 完整实现了 `HookType`, `HookMetadata`, 以及 `GitEvent`/`AgentEvent`/`IDEEvent` 枚举。Pydantic 模型包含必要的校验逻辑（如 `provider` 必填项和 `event` 类型校验）。
2. **解析器**: `HookParser` 能够正确识别不同注释风格（`#`, `//`, `--`, `<!--`）并提取 YAML Front Matter。处理了 Shebang 跳过和解析错误定位。
3. **管理器**: `UniversalHookManager` 实现了递归扫描、分组管理和验证能力，并预留了 `HookDispatcher` 接口。
4. **测试**: 74 个单元测试全部通过，覆盖了各种边界情况和注释风格。

文件名微调：
- 实际实现的文件名为 `models.py` 和 `manager.py`（去掉了 `universal_` 前缀，更符合包内命名惯例）。
- 未使用计划中的 `core.py` 和 `adapter.py`，相关功能已整合至上述核心模块中。
