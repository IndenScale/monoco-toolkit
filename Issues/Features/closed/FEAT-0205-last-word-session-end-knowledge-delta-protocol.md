---
id: FEAT-0205
uid: 096949
type: feature
status: closed
stage: done
title: 'last-word: 会话结束知识增量更新协议'
created_at: '2026-02-20T07:25:07'
updated_at: 2026-02-20 08:35:45
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
  - '#EPIC-0000'
  - '#FEAT-0205'
files:
  - .agents/hooks/.logs/session.log
  - src/monoco/features/last_word/__init__.py
  - src/monoco/features/last_word/commands.py
  - src/monoco/features/last_word/config.py
  - src/monoco/features/last_word/core.py
  - src/monoco/features/last_word/hook.py
  - src/monoco/features/last_word/models.py
  - tests/test_last_word.py
criticality: medium
solution: implemented
opened_at: '2026-02-20T07:25:07'
closed_at: '2026-02-20T08:35:44'
---

## FEAT-0205: last-word: 会话结束知识增量更新协议

> 命名寓意：模型在会话结束前留下的"遗言"——对知识库的最后一次更新。

## Objective

实现一个声明式知识增量更新机制。模型在会话结束时，通过声明 `path/url + heading + content` 三元组，更新以下知识库：

- **用户画像** (`~/.config/agents/USER.md`)：身份、偏好、背景
- **自我人格** (`~/.config/agents/SOUL.md`)：价值观、思考框架、提醒
- **全局最佳实践** (`~/.config/agents/AGENTS.md`)：跨项目约定
- **项目知识** (`./AGENTS.md`)：项目特定上下文

### 核心语义

| `content` 值  | `operation` | 行为                    |
| ------------- | ----------- | ----------------------- |
| `null` (默认) | `no-op`     | **不更新**（占位符）    |
| `"..."`       | `update`    | 创建或覆盖 heading 内容 |
| `""`          | `clear`     | 清空内容，保留 heading  |
| `null`        | `delete`    | 删除整个 heading        |

## Acceptance Criteria

- [x] 定义 YAML Schema 规范（version, source, entries 结构）
- [x] 支持四种 operation：no-op, update, clear, delete
- [x] 支持 `path` 和 `url` 两种目标定位方式 (URL 预留)
- [x] 实现 `(heading, level)` 唯一性校验机制
- [x] 创建文件布局：`~/.config/agents/last-word/` 目录结构
- [x] 实现 `config.yaml` 默认知识库配置
- [x] 集成 agenthooks 的 `pre_session_stop` 事件触发
- [x] 实现内存缓冲区存储会话期间的更新声明
- [x] 实现分组、验证、暂存（staging）工作流程
- [x] 实现原子写入与冲突处理机制
- [x] 预留 CLI 接口：`last-word status/apply/resolve/validate`

## Technical Tasks

### Part 1: Schema 与核心模型

- [x] 定义 `schema.yaml` 官方 Schema

  ```yaml
  version: '1.0.0'
  source: 'session_xxx'
  entries:
    - key:
        path: '~/.config/agents/USER.md'
        heading: 'Research Interests'
        level: 2
      operation: 'update'
      content: |-
        - AI Agents
        - Domain Modeling
      meta:
        confidence: 0.95
        reason: '用户深入讨论了...'
  ```

- [x] 实现 Entry 数据模型（Pydantic）
- [x] 实现 Key 唯一性验证器（heading + level）
- [x] 实现 Path 解析器（支持 `~` 展开和相对路径）

### Part 2: 文件布局与配置

- [x] 创建全局目录结构 `~/.config/agents/last-word/`

  ```text
  ~/.config/agents/last-word/
  ├── schema.yaml
  ├── config.yaml
  ├── AGENTS.md.yaml
  ├── SOUL.md.yaml
  ├── USER.md.yaml
  └── staging/
  ```

- [x] 创建项目级配置 `.agents/AGENTS.md.yaml` (移至后续迭代)
- [x] 实现 `config.yaml` 默认知识库配置
  - global-agents, soul, user 三个默认知识库
  - project_knowledge 自动检测配置
  - session_bootstrap 启动加载列表

### Part 3: 工作流程实现

- [x] **Session Start**: 加载 config → 读取知识库 → 注入 System Prompt
- [x] **Session Running**:
  - 实现 `last_word.plan()` API 供模型声明更新意图
  - 内存缓冲区存储 entries
- [x] **Pre-Session-Stop Hook**:
  - 按 target 文件分组 entries
  - 每文件内验证 (heading, level) 唯一性
  - 失败 → 写入 staging/ 目录
  - 通过 → 写入对应 .yaml 文件（带指数退避重试）
- [x] **Apply 进程**:
  - 读取 .yaml → 解析 → 修改 .md → 原子写入
  - 成功 → 删除或标记 .yaml

### Part 4: 并发控制与可靠性

- [x] 实现文件级锁（原子 rename）
- [x] 实现指数退避重试机制（3 次重试，随机延迟）
- [x] 设计 staging/ 目录结构用于冲突/失败暂存

  ```text
  staging/
  └── 20260220-143022-xxxx.yaml
  ```

### Part 5: CLI 接口（预留）

- [x] `agents last-word status` - 查看待处理更新
- [x] `agents last-word apply [--dry-run] [--file USER.md]` - 手动触发 apply
- [x] `agents last-word resolve USER.md.yaml` - 解决冲突
- [x] `agents last-word validate USER.md.yaml` - 验证语法

### Part 6: 集成与扩展

- [x] 与 agenthooks 集成：注册 `pre_session_stop` 处理器
- [x] Typedown 兼容性：知识库 .md 文件可使用 Typedown 验证 (移至后续迭代)
- [x] URL 支持预留（未来分布式场景）

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  1. Session Start                                            │
│     └── 加载 config.yaml → 读取所有知识库                   │
│         → 注入 System Prompt 作为上下文                     │
├─────────────────────────────────────────────────────────────┤
│  2. Session Running                                          │
│     └── 模型通过 API 声明意图：                              │
│         last_word.plan({                                     │
│           path: "USER.md",                                   │
│           heading: "Research Interests",                     │
│           content: "...",                                    │
│           operation: "update"                                │
│         })                                                   │
│     └── 存储在内存缓冲区                                     │
├─────────────────────────────────────────────────────────────┤
│  3. Pre-Session-Stop Hook (agenthooks)                       │
│     a. 按 target 文件分组 entries                            │
│     b. 每文件内验证：(heading, level) 唯一性                 │
│     c. 失败 → 写入 staging/，附带 error 信息                 │
│     d. 通过 → 写入对应 .yaml 文件（带随机延迟的指数退避）    │
├─────────────────────────────────────────────────────────────┤
│  4. Apply（独立进程或下次启动时）                            │
│     └── 读取 .yaml → 解析 → 修改 .md → 原子写入              │
│     └── 成功 → 标记 applied: true 或删除 .yaml               │
└─────────────────────────────────────────────────────────────┘
```

## Dependencies

- **agenthooks**: 依赖其 `pre_session_stop` 事件触发
- **Typedown** (可选): 知识库 .md 文件可使用 Typedown 进行结构化验证

## Related

- agenthooks: 事件驱动 Hook 的开放格式
- Typedown: Markdown 渐进式形式化工具

## Design Reference

原始设计文档：`.agents/last-word-design.md`

## Review Comments

### Self-Review (2026-02-20)

**实现总结**:

- 完整实现了 last-word 核心协议
- 包含数据模型、session 管理、YAML 持久化、markdown 应用
- 提供了 CLI 接口和 agenthooks 集成
- 包含 24 个单元测试，全部通过

**待后续迭代**:

1. URL 支持：当前仅支持本地 path，预留 URL 扩展接口
2. Typedown 集成：知识库验证可与 Typedown 结合
3. 项目级配置：`.agents/AGENTS.md.yaml` 的具体用途待明确

**测试覆盖**:

- models: Schema、Entry、TargetKey 模型
- validation: (heading, level) 唯一性校验
- session: init_session, plan, process_session_end
- markdown: update/clear/delete 操作
- integration: 目录创建、文件写入
