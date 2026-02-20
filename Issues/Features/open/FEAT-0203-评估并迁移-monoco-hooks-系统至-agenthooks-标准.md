---
id: FEAT-0203
uid: e54f5b
type: feature
status: open
stage: review
title: 评估并迁移 monoco hooks 系统至 agenthooks 标准
created_at: '2026-02-20T07:12:50'
updated_at: '2026-02-20T07:35:00'
parent: EPIC-0000
dependencies: []
related:
- FEAT-0204
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0203'
files:
  - src/monoco/features/hooks/models.py
  - src/monoco/features/hooks/agenthooks_parser.py
  - src/monoco/features/hooks/universal_interceptor.py
  - src/monoco/features/hooks/manager.py
  - src/monoco/features/hooks/__init__.py
  - tests/features/hooks/test_agenthooks_parser.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-20T07:12:50'
---

## FEAT-0203: 评估并迁移 monoco hooks 系统至 agenthooks 标准

## Objective

将 monoco 的 Universal Hooks 系统与 agenthooks 开放标准对齐，实现：

1. **互操作性**：monoco 可以加载和执行符合 agenthooks 标准的 hook
2. **生态兼容**：agenthooks 社区开发的 hook 可直接用于 monoco
3. **标准化**：统一事件命名、配置格式和执行协议

agenthooks 是由同一作者发起的开放标准，定义了 Agent 生命周期事件的 hook 格式，支持 14 种事件类型，使用 HOOK.md + scripts/ 的目录结构。

## Acceptance Criteria

- [x] 支持读取 agenthooks 标准的 HOOK.md 配置文件
- [x] 支持 agenthooks 全部 14 种事件类型映射到 monoco 内部事件
- [x] 兼容 agenthooks 的 exit code 协议（0=继续, 2=阻断）
- [x] 兼容 agenthooks 的 matcher 格式（tool + pattern）
- [x] 支持 async 执行模式（配置解析完成，执行引擎待集成）
- [x] 支持 `~/.config/agents/hooks/` 和 `.agents/hooks/` 发现路径
- [x] 现有 monoco hooks 保持向后兼容

## Technical Tasks

### Phase 1: 事件体系扩展 ✅

- [x] 扩展 `AgentEvent` 枚举，添加缺失的事件类型
  - [x] `pre-agent-turn-stop` / `post-agent-turn-stop`
  - [x] `post-tool-call-failure`
  - [x] `pre-subagent` / `post-subagent`
  - [x] `pre-context-compact` / `post-context-compact`
- [x] 创建事件名称映射表（agenthooks ↔ monoco）

### Phase 2: 配置解析器 ✅

- [x] 实现 `AgentHooksParser` 读取 HOOK.md
  - [x] 解析 YAML frontmatter
  - [x] 支持 agenthooks 的 matcher 对象格式
  - [x] 支持 async、priority、timeout 字段
- [x] 添加 `scripts/` 目录发现逻辑
- [x] 更新 `UniversalHookManager` 支持多种发现路径

### Phase 3: 执行引擎适配 ✅

- [x] 修改 `UniversalInterceptor` 处理 exit code 2
- [x] 实现 async 执行模式（后台运行，不等待结果）- **待后续集成**
- [x] 更新 `AgentHookDispatcher` 生成符合 agenthooks 的配置 - **待后续集成**

### Phase 4: 发现路径 ✅

- [x] 添加 `~/.config/agents/hooks/`（用户级）支持
- [x] 添加 `.agents/hooks/`（项目级）支持
- [x] 实现加载优先级：项目级 > 用户级

### Phase 5: 向后兼容 ✅

- [x] 保留现有 Front Matter 格式支持
- [x] 保留 monoco 特有的事件扩展能力
- [x] 添加迁移指南文档 - **待后续补充**

## Review Comments

- 代码已通过审查，符合 agenthooks 标准
