---
id: FEAT-0174
uid: 41571d
type: feature
status: open
stage: draft
title: 'Universal Hooks: Core Models and Parser'
created_at: '2026-02-04T13:27:07'
updated_at: '2026-02-04T14:50:00'
parent: EPIC-0034
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0034'
- '#FEAT-0174'
files: []
criticality: high
solution: null
opened_at: '2026-02-04T13:27:07'
---

## FEAT-0174: Universal Hooks: Core Models and Parser

## 目标

实现通用 Hooks 系统的基础模型和 Front Matter 解析器，为 Git/Agent/IDE 三种类型的 Hooks 提供统一的元数据定义和解析能力。

## 验收标准

- [ ] 定义 `HookType` Enum: `git`, `ide`, `agent`
- [ ] 实现 `HookMetadata` Pydantic 模型：
  - [ ] 基础字段：`type`, `event`, `matcher`, `priority`, `description`
  - [ ] 条件字段：`provider` (当 type=agent/ide 时必填)
- [ ] 实现 `HookParser`，支持从脚本头部解析 YAML Front Matter
- [ ] 支持多语言注释风格：`#` (Shell/Python), `//` (JS/TS), `--` (Lua/SQL)
- [ ] 实现 `UniversalHookManager` 核心类框架：
  - [ ] `scan(directory)`: 递归扫描并按 `type` + `provider` 分组
  - [ ] `validate(hook)`: 校验元数据完整性

## 技术任务

### 模型定义
- [ ] 定义 `HookType` Enum: `git`, `ide`, `agent`
- [ ] 定义 `HookMetadata` Pydantic 模型：
  - [ ] 基础字段：`type` (HookType), `event`, `matcher`, `priority`, `description`
  - [ ] Provider 字段：`provider` (Optional[str], 当 type=agent/ide 时必填)
- [ ] 定义各类型的事件枚举：
  - [ ] `GitEvent`: pre-commit, prepare-commit-msg, commit-msg, post-merge, pre-push
  - [ ] `AgentEvent`: session-start, before-tool, after-tool, before-agent, after-agent
  - [ ] `IDEEvent`: on-save, on-open, on-close, on-build

### Front Matter 解析器
- [ ] 实现 `HookParser` 类
  - [ ] 从脚本头部提取 YAML Front Matter
  - [ ] 支持多行注释边界检测 (`# ---` / `# ---`)
  - [ ] 支持多语言注释风格检测
- [ ] 实现解析错误处理和行号定位
- [ ] 编写单元测试覆盖各种注释风格

### UniversalHookManager 框架
- [ ] 创建 `monoco/features/hooks/core.py`
- [ ] 实现 `UniversalHookManager` 类框架
  - [ ] `scan(directory)`: 递归扫描 Hook 脚本，按 `type` + `provider` 分组返回
  - [ ] `validate(hook)`: 校验元数据（如 type=agent 时 provider 必填）
  - [ ] `register_dispatcher(type, dispatcher)`: 注册类型分发器（为后续 Feature 预留）

## Review Comments
<!-- 评审阶段时填写 -->
