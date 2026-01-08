---
id: EPIC-0001
type: epic
status: open
title: "Monoco Toolkit: Agent Management Best Practices & Dogfooding"
created_at: 2026-01-08
tags: [toolkit, agent-native, dogfood, architecture]
---

## EPIC-0001: Monoco Toolkit & Dogfooding

## Context (背景)

为了彻底解决 "Bootstrap Paradox" 并验证 Monoco 的 "Agent Native" 理念，我们需要构建一套标准化的 CLI 工具箱 (`Monoco Toolkit`)。
这套工具箱不仅是开发的辅助工具，更是 Agent 的感官延伸。
我们需要通过 "Dogfooding" (吃自己的狗粮) 的方式，在开发 Monoco 自身的过程中验证并固化这套最佳实践。

## Design Philosophy (设计哲学)

1. **Determinism (确定性)**: 消除输出的随机性，确保 Agent 每次调用都能获得预期的结构。
2. **Structured I/O (结构化 I/O)**: 所有命令必须支持机器可读的输出格式 (JSON)，优先服务 Agent，其次服务人类。
3. **Context Awareness (上下文感知)**: 自动识别 Project Root，加载 User Context 和 Workspace Context。

## Objectives (目标)

1. **Toolkit Construction**: 构建功能完备的 `monoco` CLI，涵盖 Issue, Spike, Runtime 等核心领域。
2. **Standardization**: 固化 Agent 协作的最佳实践 (Protocol, I/O, Workflow)。
3. **Dogfooding**: 开发团队 (Human & Agent) 全面切换到使用 Toolkit 进行日常开发。

## Technical Architecture (技术架构)

基于 Python (PDM/Poetry) 构建，使用 `Typer` 作为 CLI 框架。

```text
Toolkit/
├── pyproject.toml      # Package definition
├── monoco/
│   ├── main.py         # Entry point (Typer App)
│   ├── core/           # Shared Infrastructure
│   │   ├── config.py   # Config loading
│   │   ├── output.py   # JSON/Rich output strategies
│   │   └── ioc.py      # Dependency Injection
│   ├── features/       # Modular Features
│   │   ├── issue/      # Local: Task & Story management
│   │   ├── spike/      # Local: Knowledge & Reference management
│   │   ├── check/      # Local: Quality Control
│   │   └── runtime/    # Remote: VCS/Ops interactions (gRPC/HTTP)
```

## Agent Native Standard (交互标准)

### Command Interface

所有涉及数据输出的命令必须实现 `--json` flag。

- **Human Mode (Default)**: 使用 `rich` 库渲染表格、树状图，提供良好的阅读体验。
- **Agent Mode (`--json`)**: 输出纯净的 JSON 字符串，无额外日志干扰。

### Error Handling

- **Exit Codes**:
  - `0`: Success
  - `1`: General Error (Details in stderr)
  - `2`: Invalid Usage

## Key Results (关键结果)

- [x] 确保 Monoco CLI 工具箱的基础架构搭建。发布 v0.1.0，支持 Local Domain (Issue/Spike).
- [ ] 所有开发任务通过 `ISSUES/` 目录管理，不再依赖散乱的 Markdown。
- [ ] Agent 能够通过 CLI 自主读取上下文、创建 Issue 并提交代码。

## Child Stories (子故事)

- [x] [[STORY-0002]]: Toolkit Core Infrastructure (Done)
- [x] [[STORY-0003]]: Feature: Issue Management (Done)
- [ ] [[STORY-0004]]: Feature: Spike Management
- [ ] [[STORY-0005]]: Feature: Quality Control (Check)
- [ ] [[STORY-0006]]: Feature: Runtime (Remote Interaction)
