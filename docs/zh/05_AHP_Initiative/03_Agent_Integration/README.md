# 03. 智能体集成

## 摘要

智能体集成层定义 AHP 如何与 LLM 智能体交互。通过 **AGENTS.md** 上下文配置、**Agent Hooks** 触发机制，以及 **Agent Skills** 能力扩展，AHP 将记录系统转化为智能体的可执行环境。

---

## 快速对比：三机制的工作模式

| 维度 | AGENTS.md | Agent Hooks | Agent Skills |
|------|-----------|-------------|--------------|
| **作用时机** | 会话初始化 | 状态转换前/后 | 按需调用 |
| **控制方向** | AHP → Agent（单向注入） | AHP ↔ Agent（双向干预） | Agent → AHP（主动请求） |
| **核心功能** | 定义规则与上下文 | 验证与引导 | 扩展能力工具包 |
| **Metaphor** | 宪法/用户手册 | 交通信号灯 | 工具箱 |
| **文件位置** | `AGENTS.md`（项目根目录） | `.ahp/hooks.yaml` | `.ahp/skills/` 或 `~/.ahp/skills/` |
| **触发方式** | 自动加载 | 事件被动触发 | 智能体主动调用 |
| **典型示例** | "本项目使用 TBD 工作流" | "提交前 checklist 未完成 → 阻止" | `monoco issue start FEAT-001` |
| **性质** | 社区实践* | **AHP 实现的 ACL** | 社区实践* |

> **\*社区实践**：AGENTS.md 和 Agent Skills 是智能体社区的通用实践，非 HAP 专有。不同平台（Claude Code、Kimi CLI、Gemini CLI 等）有各自的具体实现。

### 一句话定义

- **AGENTS.md**：告诉智能体"你是谁，在什么环境，遵循什么规则"
- **Agent Hooks**：在关键节点告诉智能体"停下检查"或"注意风险"（HAP 实现的 **ACL - Agent Control Language**）
- **Agent Skills**：让智能体能够"执行特定领域的操作"

---

## 架构概览

### 集成模型

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Agent (Kimi/Claude/etc.)           │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Context    │    │   Action     │    │   Skill      │  │
│  │   (Prompt)   │◄───┤   Request    │───►│   Execution  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│           ▲                   │                   ▲        │
│           │                   ▼                   │        │
│  ┌────────┴────────┐    ┌──────────┐    ┌────────┴──────┐ │
│  │   AGENTS.md     │    │  Hooks   │    │   Skills      │ │
│  │   (Context)     │    │  (Gate)  │    │   (Tools)     │ │
│  └─────────────────┘    └──────────┘    └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AHP Record System                        │
│              (Issue Tickets + Git + Files)                  │
└─────────────────────────────────────────────────────────────┘
```

### 三层集成

| 层级 | 组件 | 功能 | 触发时机 |
|------|------|------|----------|
| **上下文** | AGENTS.md | 向智能体注入规则与偏好 | 会话初始化 |
| **干预** | Hooks | 在关键点验证与引导 | 状态转换前/后 |
| **能力** | Skills | 扩展智能体工具集 | 按需调用 |

---

## 交互流程示例

```
用户: "实现登录功能"
    │
    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ AGENTS.md   │───►│   Agent     │◄──►│   Skills    │
│ 加载上下文   │    │  理解任务    │    │ 调用工具    │
│ "使用 TBD"  │    │             │    │ issue create│
└─────────────┘    └──────┬──────┘    └─────────────┘
                          │
                    执行中 ▼
            ┌─────────────────────────┐
            │ pre-issue-submit Hook   │◄──── "checklist 未完成？"
            │     检查 checklist      │       Block / Prompt / Allow
            └─────────────────────────┘
```

---

## 子章节

| 章节 | 内容 |
|------|------|
| [3.1 AGENTS.md](./01_AGENTS_md.md) | 上下文配置机制详解 |
| [3.2 Agent Hooks](./02_Agent_Hooks.md) | 过程干预与触发器系统 |
| [3.3 Agent Skills](./03_Agent_Skills.md) | 能力扩展与工具包 |

---

## 设计原则

### 渐进式约束

干预强度应从低到高：

```
Prompt → Control → Block
  ▲         │
  └─────────┘（若控制不可行，回退到提示）
```

### 上下文感知

同一操作在不同上下文可能需要不同干预：

| 上下文 | `rm -rf /` 的响应 |
|--------|-------------------|
| 生产环境 | Block |
| 开发环境 | Prompt |
| 沙箱环境 | Aid（记录即可）|

### 可观测性

所有干预都应可记录、可分析：

```jsonl
{"timestamp": "2026-02-09T10:00:00Z", "hook": "pre-issue-submit", "intensity": "block", "reason": "checklist_incomplete"}
{"timestamp": "2026-02-09T10:05:00Z", "hook": "pre-issue-submit", "intensity": "prompt", "reason": "large_change", "accepted": false}
```

---

## 参考

- [3.1 AGENTS.md](./01_AGENTS_md.md)
- [3.2 Agent Hooks](./02_Agent_Hooks.md)
- [3.3 Agent Skills](./03_Agent_Skills.md)
- [04. 控制协议](../04_Control_Protocol.md)
