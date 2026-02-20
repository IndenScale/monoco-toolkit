<!-- MONOCO_MANAGED_START -->
<!-- From resources -->
# Doc-Extractor: 文档标准化与渲染工具

将各种文档格式转换为标准化 WebP 页面序列的文档提取和渲染系统，适用于 VLM（视觉语言模型）消费。

## 概述

Doc-Extractor 提供了一个内容寻址的文档存储系统，支持自动格式标准化：

- **输入**: PDF、DOCX、PPTX、XLSX、图片（PNG、JPG）、压缩包（ZIP、TAR、RAR、7Z）
- **输出**: 可配置 DPI 和质量的 WebP 页面序列
- **存储**: 基于 SHA256 的内容寻址，存储在 `~/.monoco/blobs/`

## 命令

### 提取文档
```bash
monoco doc-extractor extract <文件> [选项]
```

选项：
- `--dpi, -d`: 渲染 DPI（72-300，默认：150）
- `--quality, -q`: WebP 质量（1-100，默认：85）
- `--pages, -p`: 指定渲染页面（例如："1-5,10,15-20"）

### 列出提取的文档
```bash
monoco doc-extractor list [--category <类别>] [--limit <数量>]
```

### 搜索文档
```bash
monoco doc-extractor search <查询>
```

### 显示文档详情
```bash
monoco doc-extractor show <哈希前缀>
monoco doc-extractor cat <哈希前缀>    # 显示元数据 JSON
monoco doc-extractor source <哈希前缀> # 显示源文件/压缩包信息
```

### 索引管理
```bash
monoco doc-extractor index rebuild   # 从 blobs 重建索引
monoco doc-extractor index stats     # 显示索引统计
monoco doc-extractor index clear     # 清空索引（保留 blobs）
monoco doc-extractor index path      # 显示索引文件路径
```

### 清理
```bash
monoco doc-extractor clean [--older-than <天数>] [--dry-run]
monoco doc-extractor delete <哈希前缀> [--force]
```

## 存储结构

```
~/.monoco/blobs/
├── index.yaml              # 全局元数据索引
└── {sha256_hash}/          # 内容寻址目录
    ├── meta.json           # 文档元数据
    ├── source.{ext}        # 原始文件（保留扩展名）
    ├── source.pdf          # 标准化 PDF 格式
    └── pages/
        ├── 0.webp          # 第 0 页渲染
        ├── 1.webp          # 第 1 页渲染
        └── ...
```

## Python API

```python
from monoco.features.doc_extractor import DocExtractor, ExtractConfig

extractor = DocExtractor()
config = ExtractConfig(dpi=150, quality=85)
result = await extractor.extract("/path/to/document.pdf", config)

print(f"Hash: {result.blob.hash}")
print(f"Pages: {result.page_count}")
print(f"Cached: {result.is_cached}")
```

## 核心原则

1. **内容寻址**: 文件按 SHA256 哈希存储 - 自动去重
2. **格式标准化**: 所有文档先转为 PDF，再渲染为 WebP
3. **压缩包支持**: 自动解压 ZIP 等压缩包，追踪内部文档来源
4. **缓存感知**: 提取结果被缓存；重复提取立即返回缓存结果


---

<!-- From resources -->
## Ralph Loop

> **重生后接力胜过泥泞中挣扎。**

当当前 Agent 遇到瓶颈（上下文不足、陷入局部最优、需要全新视角）时，启动继任 Agent 继续完成 Issue。

## 核心概念

- **Last Words** - 当前 Agent 留给继任者的关键信息：已完成的工作、当前状态、下一步建议
- **接力而非重启** - 继任者继承 Issue 上下文和工作环境，而不是从零开始
- **自愿让贤** - 当当前 Agent 判断自己效率下降时主动触发，而非强行坚持

## 命令

- `monoco ralph --issue {issue-id} --prompt "{last-words}"` - 直接传递遗言字符串
- `monoco ralph --issue {issue-id} --path {last-words-file}` - 从文件读取遗言（用于长内容）
- `monoco ralph --issue {issue-id}` - 让系统自动生成上下文摘要作为 Last Words

## 自动触发机制

Ralph Loop 会在以下任一条件满足时自动触发（无需人工干预）：

### 工具调用计数

| 阈值 | 行为 |
|------|------|
| **150 次** | 警告：提示上下文已使用约 75%，建议准备收尾 |
| **175 次** | 严重警告：提示上下文已使用约 87.5%，强烈建议完成当前里程碑或准备接力 |
| **200 次** | **强制接力**：自动启动 `monoco ralph`，当前 Agent 结束会话 |

### 内容长度累计

基于响应内容字符数统计（1 token ≈ 4 字符）：

| 阈值 | 行为 |
|------|------|
| **300k 字符** (~75k tokens) | 警告：建议准备收尾 |
| **350k 字符** (~87.5k tokens) | 严重警告：建议尽快完成或接力 |
| **400k 字符** (~100k tokens) | **强制接力**：自动启动 `monoco ralph` |

### 触发范围

**工具调用计数**追踪以下工具：
- `Bash`, `Write`, `Edit`, `Read`
- `Glob`, `Grep`, `Task`
- `WebFetch`, `WebSearch`

**内容长度**统计以下工具的响应：
- `Read`, `Glob`, `Grep`
- `WebFetch`, `WebSearch`

### 跳过机制

如需临时禁用自动触发（例如正在进行关键原子操作）：

```bash
export MONOCO_SKIP_RALPH=1
```

设置后，即使达到阈值也不会强制接力。

## 工作流

1. **自我评估**：当前 Agent 判断是否遇到瓶颈
   - 上下文窗口即将用尽（自动触发机制会处理）
   - 多次尝试同一问题无果
   - 感觉陷入细节而迷失全局

2. **撰写 Last Words**：总结关键信息
   - ✅ 已完成的工作和验证结果
   - ✅ 当前代码/文件状态
   - ✅ 遇到的障碍或不确定的问题
   - ✅ 建议的下一步方向

3. **执行接力**：运行 `monoco ralph` 启动继任 Agent

4. **平滑过渡**：继任 Agent 读取 Last Words 和 Issue 上下文，继续推进

## 指南

### 何时使用 Ralph

| 适合使用 | 不适合使用 |
|---------|-----------|
| 复杂重构涉及大量文件 | 简单的 bug 修复 |
| 上下文窗口不足（自动触发） | 单文件修改 |
| 多次尝试无果，需要新视角 | 已经接近完成，只剩收尾 |
| 陷入技术细节需要全局审视 | 验证性测试 |

### Last Words 最佳实践

- **简明扼要**：聚焦关键信息，而非完整历史
- **状态优先**：描述"现在在哪里"而非"怎么来的"
- **方向明确**：给继任者一个清晰的下一步建议
- **诚实记录**：不隐瞒失败尝试，避免继任者重复踩坑

### 接力后

- 当前 Agent 正常结束会话
- 继任 Agent 在独立环境中启动，继承 Issue 上下文
- 无需手动同步文件，`monoco ralph` 会自动处理


---

<!-- From resources -->
## Monoco 核心

项目管理的核心命令。遵循 **Trunk Based Development (TBD)** 模式。

- **初始化**: `monoco init` (初始化新的 Monoco 项目)
- **配置**: `monoco config get|set <key> [value]` (管理配置)
- **同步**: `monoco sync` (与 agent 环境同步)
- **卸载**: `monoco uninstall` (清理 agent 集成)

---

## ⚠️ Agent 必读: Git 工作流协议 (Trunk-Branch)

在修改任何代码前,**必须**遵循以下步骤:

### 标准流程

1. **创建 Issue**: `monoco issue create feature -t "功能标题"`
2. **🔒 启动 Branch**: `monoco issue start FEAT-XXX --branch`
   - ⚠️ **强制要求隔离**: 使用 `--branch` 或 `--worktree` 参数
   - ❌ **严禁操作 Trunk**: 禁止在 Trunk (`main`/`master`) 分支直接修改代码
3. **实现功能**: 正常编码和测试
4. **同步文件**: `monoco issue sync-files` (提交前必须运行)
5. **提交审查**: `monoco issue submit FEAT-XXX`
6. **合拢至 Trunk**: `monoco issue close FEAT-XXX --solution implemented`

### 质量门禁

- Git Hooks 会自动运行 `monoco issue lint` 和测试
- 不要使用 `git commit --no-verify` 绕过检查
- Linter 会阻止在受保护的 Trunk 分支上的直接修改

> 📖 详见 `monoco-issue` skill 获取完整工作流文档。


---

<!-- From last_word -->
# Last-Word: Simplified Knowledge Update System

## Overview

The knowledge update system has been **significantly simplified**. The complex YAML-based workflow has been replaced with a direct, manual approach using `mdp` tool.

## Architecture

```
PreSessionStop Event
        ↓
   Hook Triggered
        ↓
  Show Guidance
        ↓
Agent Uses mdp → Direct Edit to MD
```

## Hook

**Path**: `resources/hooks/pre-session-stop`

Triggers on `PreSessionStop` event, outputs guidance reminding the agent
to consider updating knowledge bases.

## Knowledge Bases

| File | Path | Purpose |
|------|------|---------|
| USER.md | `~/.config/agents/USER.md` | User identity, preferences, background |
| SOUL.md | `~/.config/agents/SOUL.md` | AI personality, values, thinking framework |
| AGENTS.md | `~/.config/agents/AGENTS.md` | Global best practices across projects |
| ./AGENTS.md | `./AGENTS.md` | Project-specific context |

## Usage

When you see the guidance at session end:

1. Decide if any knowledge bases need updates
2. Use `mdp` tool to edit directly:

```bash
# Append
mdp patch -f ~/.config/agents/USER.md -H '## Research Interests' \
    -i 0 --op append -c '- New item'

# Replace
mdp patch -f ~/.config/agents/USER.md -H '## Notes' \
    -i 0 --op replace -c 'New content' -p 'Old.*'

# Delete
mdp patch -f ~/.config/agents/USER.md -H '## Temp' -i 0 --op delete
```

## Why Simplified?

Old system: `plan() → Buffer → YAML → Validate → Staging → Apply → MD`

New system: `Hook → Guidance → mdp → MD`

- No hidden state
- No intermediate files
- Direct and transparent
- Agent has full control


---

<!-- From resources -->
## Issue 管理 & Trunk Based Development

Monoco 遵循 **Trunk Based Development (TBD)** 模式。所有的开发工作都在短平快的分支（Branch）中进行，并最终合并回干线（Trunk）。

使用 `monoco issue` 管理任务生命周期。

- **创建**: `monoco issue create <type> -t "标题"`
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint`
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]`
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (如 `Issues/Features/open/`)

## 标准工作流 (Trunk-Branch)

1. **创建 Issue**: `monoco issue create feature -t "标题"`
2. **开启 Branch**: `monoco issue start FEAT-XXX --branch` (隔离环境)
3. **实现功能**: 正常编码与测试。
4. **同步变更**: `monoco issue sync-files` (更新 `files` 字段)。
5. **提交审查**: `monoco issue submit FEAT-XXX`。
6. **合并至 Trunk**: `monoco issue close FEAT-XXX --solution implemented` (进入 Trunk 的唯一途径)。

## Git 合并策略

- **禁止手动操作 Trunk**: 严禁在 Trunk (`main`/`master`) 分支直接执行 `git merge` 或 `git pull`。
- **原子合并**: `monoco issue close` 仅根据 Issue 的 `files` 列表将变更从 Branch 合并至 Trunk。
- **冲突处理**: 若产生冲突，请遵循 `close` 命令产生的指引进行手动 Cherry-Pick。
- **清理策略**: `monoco issue close` 默认执行清理（删除 Branch/Worktree）。


---

<!-- From resources -->
## 信号队列模型

轻量级笔记，用于快速记录想法。

- **Memo 是信号，不是资产** - 其价值在于触发行动
- **文件存在 = 信号待处理** - Inbox 有未处理的 memo
- **文件清空 = 信号已消费** - Memo 在处理后被删除
- **Git 是档案** - 历史记录在 git 中，不在应用状态里

## 命令

- **添加**: `monoco memo add "内容" [-c 上下文]` - 创建信号
- **列表**: `monoco memo list` - 显示待处理信号（已消费的 memo 在 git 历史中）
- **删除**: `monoco memo delete <id>` - 手动删除（通常自动消费）
- **打开**: `monoco memo open` - 直接编辑 inbox

## 工作流

1. 将想法捕获为 memo
2. 当阈值（5个）达到时，自动触发 Architect
3. Memo 被消费（删除）并嵌入 Architect 的 prompt
4. Architect 从 memo 创建 Issue
5. 不需要"链接"或"解决" memo - 消费后即消失

## 指南

- 使用 Memo 记录** fleeting 想法** - 可能成为 Issue 的事情
- 使用 Issue 进行**可操作的工作** - 结构化、可跟踪、有生命周期
- 永远不要手动将 memo 链接到 Issue - 如果重要，创建一个 Issue


---

<!-- From resources -->
## 核心架构隐喻: "Linux 发行版"

| 术语             | 定义                                                                     | 隐喻                              |
| :--------------- | :----------------------------------------------------------------------- | :-------------------------------- |
| **Monoco**       | 智能体操作系统发行版。管理策略、工作流和包系统。                         | **发行版** (如 Ubuntu, Arch)      |
| **Kimi CLI**     | 核心运行时执行引擎。处理 LLM 交互、工具执行和进程管理。                  | **内核** (Linux Kernel)           |
| **Session**      | 由 Monoco 管理的智能体内核初始化实例。具有状态和上下文。                 | **初始化系统/守护进程** (systemd) |
| **Issue**        | 具有状态（Open/Done）和严格生命周期的原子工作单元。                      | **单元文件** (systemd unit)       |
| **Skill**        | 扩展智能体功能的工具、提示词和流程包。                                   | **软件包** (apt/pacman package)   |
| **Context File** | 定义环境规则和行为偏好的配置文件（如 `GEMINI.md`, `AGENTS.md`）。        | **配置** (`/etc/config`)          |
| **Agent Client** | 连接 Monoco 的用户界面（CLI, VSCode, Zed）。                             | **桌面环境** (GNOME/KDE)          |
| **Trunk**        | 稳定的主干代码流（通常是 `main` 或 `master` 分支）。所有功能的最终归宿。 | **主干/干线**                     |
| **Branch**       | 为解决特定 Issue 而开启的临时隔离开发环境。                              | **分支**                          |

## Context File

像 `GEMINI.md` 这样的文件，为智能体提供"宪法"。它们定义了特定上下文（根目录、目录、项目）中智能体的角色、范围和行为策略。

## Headless

Monoco 设计为无需原生 GUI 即可运行。它通过标准协议（LSP, ACP）暴露其能力，供各种客户端（IDE、终端）使用。

## Universal Shell

CLI 是所有工作流的通用接口的概念。Monoco 作为 shell 的智能层。


---

<!-- From resources -->
### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。


---

<!-- From resources -->
# Artifacts

Monoco Artifacts 系统提供了多模态产物的生命周期管理能力，基于内容寻址存储 (CAS) 实现。

## 核心功能

1. **内容寻址存储 (CAS)**: 所有产物存储在全局池 `~/.monoco/artifacts` 中，基于内容的 SHA256 哈希值进行寻址和去重。
2. **元数据管理**: 项目本地维护 `manifest.jsonl`，记录所有产物的类型、哈希及创建时间。

## 常用操作

- **查看产物**: 检查 `.monoco/artifacts/manifest.jsonl` 获取当前可用的产物列表。
- **引用产物**: 在多模态分析时，可以使用产物的 ID 或本地软链接路径。


---

<!-- From resources -->
### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

<!-- MONOCO_MANAGED_END -->