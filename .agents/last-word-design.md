# last-word: Session-End Knowledge Delta Protocol

> 命名寓意：模型在会话结束前留下的"遗言"——对知识库的最后一次更新。

## 1. 功能概述

`last-word` 是一个声明式知识增量更新机制。模型在会话结束时，通过声明 `path/url + heading + content` 三元组，更新以下知识库：

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

---

## 2. 文件布局

```text
~/.config/agents/
├── AGENTS.md                   # 全局最佳实践（可手动编辑）
├── SOUL.md                     # 自我人格（可手动编辑）
├── USER.md                     # 用户画像（可手动编辑）
└── last-word/                  # last-word 核心目录
    ├── schema.yaml             # 官方 Schema 定义
    ├── config.yaml             # 默认知识库配置
    ├── AGENTS.md.yaml          # 待应用的全局更新
    ├── SOUL.md.yaml            # 待应用的自我更新
    ├── USER.md.yaml            # 待应用的用户更新
    └── staging/                # 冲突/失败暂存
        └── 20260220-143022-xxxx.yaml

./
├── AGENTS.md                   # 项目知识（可手动编辑）
└── .agents/
    └── AGENTS.md.yaml          # 待应用的项目更新（无 last-word 子目录）
```

> **设计决策**：项目级直接放在 `.agents/` 下，减少目录层级，符合常见工具习惯（如 `.github/workflows/`）。

---

## 3. Schema 定义

### 3.1 文件结构

```yaml
version: "1.0.0" # 协议版本
source: "session_xxx" # 会话标识
entries: # 更新条目列表
  - key:
      path: "~/.config/agents/USER.md" # 或 url: "https://..."
      heading: "Research Interests" # 精确匹配，区分大小写
      level: 2 # 可选，用于验证
    operation: "update" # no-op | update | delete | clear
    content: | # null = 不更新, "" = 清空, "..." = 内容
      - AI Agents
      - Domain Modeling
    meta: # 可选元数据
      confidence: 0.95 # 模型确信度 0-1
      reason: "用户深入讨论了..."
```

### 3.2 Key 规则

- `path` 或 `url` 必须存在一个
- `path` 支持 `~` 展开和相对路径
- `heading` 精确匹配（区分大小写）
- `level` 可选，若提供则参与唯一性校验

### 3.3 重复 Heading 检测

**规则**：同一文件内，`(heading_text, level)` 组合必须唯一。

```yaml
# ❌ 错误示例：同一文件，相同 heading，相同 level
entries:
  - key: { path: "USER.md", heading: "Projects", level: 2 }
    operation: update
    content: "A"
  - key: { path: "USER.md", heading: "Projects", level: 2 }  # 重复！
    operation: update
    content: "B"

# ✅ 允许：相同 heading，不同 level
entries:
  - key: { path: "USER.md", heading: "Projects", level: 2 }
    content: "## Projects 总览"
  - key: { path: "USER.md", heading: "Projects", level: 3 }
    content: "### Projects 详细列表"
```

**未指定 level 的处理**：
若 `level: null`，校验时假设其可能为任意 level（1-6），与所有已存在的 `(heading, level)` 冲突即报错。

---

## 4. 语义详解

### 4.1 no-op（默认）

```yaml
- key:
    path: "~/.config/agents/SOUL.md"
    heading: "Values"
  operation: no-op
  content: null
```

表示该 heading 在本次会话中**无需更新**。用于显式声明"我已考虑但决定不修改"。

### 4.2 update

```yaml
- key:
    path: "~/.config/agents/USER.md"
    heading: "Research Interests"
  operation: update
  content: |
    - AI Agents
    - Domain Modeling
```

- heading 存在：覆盖内容
- heading 不存在：创建 heading（若指定 `level`，使用该级别；否则默认 `##`）

### 4.3 clear

```yaml
- key:
    path: "~/.config/agents/USER.md"
    heading: "Temporary Notes"
  operation: clear
  content: ""
```

保留 heading，但清空其下所有内容。用于"标记此处曾有内容"。

### 4.4 delete

```yaml
- key:
    path: "~/.config/agents/USER.md"
    heading: "Outdated Project"
  operation: delete
  content: null
```

完全删除该 heading 及其内容。

---

## 5. 默认知识库配置

```yaml
# ~/.config/agents/last-word/config.yaml
default_knowledge_bases:
  - id: global-agents
    file: "~/.config/agents/AGENTS.md"
    description: "跨项目最佳实践与工具约定"

  - id: soul
    file: "~/.config/agents/SOUL.md"
    description: "自我人格、价值观、思考框架"

  - id: user
    file: "~/.config/agents/USER.md"
    description: "用户身份、偏好、背景"

project_knowledge:
  enabled: true
  auto_detect: ["./AGENTS.md", "./.agents/AGENTS.md"]

session_bootstrap:
  - global-agents
  - soul
  - user
  - project # 若存在
```

---

## 6. 工作流程

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

### 并发控制

- **场景**：16 并发，15 分钟间隔
- **策略**：文件级锁 + 指数退避（3 次重试）
- **锁实现**：`filelock.FileLock` 或原子 `rename`

---

## 7. 扩展：URL 支持（未来）

```yaml
- key:
    url: "https://agent-network.org/kb/common/python.md"
    heading: "Preferred Patterns"
  operation: update
  content: |
    - 使用 `pathlib` 而非 `os.path`
```

用于分布式场景，多个 agent 共享远程知识库。

---

## 8. CLI 接口（预留）

```bash
# 查看待处理更新
agents last-word status

# 手动触发 apply
agents last-word apply [--dry-run] [--file USER.md]

# 解决冲突
agents last-word resolve USER.md.yaml

# 验证语法
agents last-word validate USER.md.yaml
```

---

## 9. 与相关项目的关系

- **agenthooks**: 依赖其 `pre_session_stop` 事件触发
- **Typedown**: 知识库 `.md` 文件可使用 Typedown 进行结构化验证
- **monoco-toolkit**: 可作为 Monoco Issue 的 Knowledge Update 工作单元

---

_Design Date: 2026-02-20_
_Status: Draft_
