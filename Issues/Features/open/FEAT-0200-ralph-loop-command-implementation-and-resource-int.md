---
id: FEAT-0200
uid: 982bbc
type: feature
status: open
stage: review
title: Ralph Loop command implementation and resource integration
created_at: '2026-02-10T17:45:51'
updated_at: '2026-02-10T17:58:21'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0200'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- src/monoco/features/ralph/__init__.py
- src/monoco/features/ralph/cli.py
- src/monoco/features/ralph/core.py
- src/monoco/features/ralph/models.py
- src/monoco/main.py
criticality: medium
solution: implemented
opened_at: '2026-02-10T17:45:51'
isolation:
  type: branch
  ref: FEAT-0200-ralph-loop-command-implementation-and-resource-int
  created_at: '2026-02-10T17:45:57'
---

## FEAT-0200: Ralph Loop command implementation and resource integration

## Objective
实现 Ralph Loop 的胶水代码，将已设计的资源（AGENTS.md、hooks）与 Monoco CLI 集成。提供 `monoco ralph` 命令，允许当前 Agent 在上下文不足或遇到瓶颈时，启动继任 Agent 继续完成 Issue。

## Acceptance Criteria
- [x] `monoco ralph --issue FEAT-XXX --prompt "last words"` 命令可正常执行
- [x] `monoco ralph --issue FEAT-XXX --path last-words.md` 支持从文件读取遗言
- [x] `monoco ralph --issue FEAT-XXX` 可自动生成上下文摘要作为 Last Words
- [x] 继任 Agent 启动时自动加载 Issue 上下文和 AGENTS.md 资源
- [x] 资源分发集成：自动将 zh/AGENTS.md 或 en/AGENTS.md 注入 Agent 上下文
- [x] Last Words 文件正确生成并传递给继任 Agent
- [x] 支持 `MONOCO_SKIP_RALPH=1` 环境变量禁用自动触发

## Technical Tasks

- [x] 创建 Ralph Loop 数据模型 (`models.py`)
  - [x] `LastWords` 类：遗言数据结构
  - [x] `RalphRelay` 类：接力记录状态
- [x] 实现核心逻辑 (`core.py`)
  - [x] `prepare_last_words()`: 生成遗言文档
  - [x] `spawn_successor_agent()`: 启动继任 Agent
  - [x] `relay_issue()`: 执行完整接力流程
  - [x] `get_relay_status()`: 查询接力状态
- [x] 实现 CLI 命令 (`cli.py`)
  - [x] `monoco ralph --issue` 主命令
  - [x] `--prompt` 参数支持直接传入遗言
  - [x] `--path` 参数支持从文件读取
  - [x] 无参数时自动生成摘要
- [x] 资源分发集成
  - [x] 读取 `resources/zh/AGENTS.md` 或 `resources/en/AGENTS.md`
  - [x] 将资源内容注入继任 Agent 的启动上下文
- [x] 在 `main.py` 中注册 `ralph` 子命令
- [x] 测试验证
  - [x] 手动测试命令执行
  - [x] 验证资源正确加载

## Review Comments
- 已实现 Ralph Loop 完整功能
- 命令解析、资源分发、独立进程启动均已验证
- 接受并合并到主干
