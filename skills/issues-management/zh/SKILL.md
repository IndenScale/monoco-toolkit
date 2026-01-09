---
name: issues-management
description: Monoco Issue System 的官方技能定义。将 Issue 视为通用原子 (Universal Atom)，管理 Epic/Feature/Chore/Fix 的生命周期。
---

# 自我管理 (Monoco Issue System)

使用此技能在 Monoco 项目中创建和管理 **Issue** (通用原子)。该系统参考 Jira 表达体系，同时保持 "建设者 (Builder)" 和 "调试者 (Debugger)" 思维模式的隔离。

## 核心本体论 (Core Ontology)

Monoco 不仅仅复刻 Jira，而是基于 **"思维模式 (Mindset)"** 重新定义工作单元。

### 1. 战略层 (Strategy)

#### 🏆 EPIC (史诗)

- **Mindset**: _Architect_ (架构师)
- **定义**: 跨越多个周期的宏大目标。它不是单纯的"大任务"，而是"愿景的容器"。
- **产出**: 定义了系统的边界和核心价值。

### 2. 价值层 (Value)

#### ✨ FEATURE (特性)

- **Mindset**: _Product Owner_ (产品负责人)
- **定义**: 用户视角的价值增量。必须是可独立交付 (Shippable) 的垂直切片。
- **Focus**: "Why" & "What" (用户想要什么？)。
- **Prefix**: `FEAT-`

_(取代了 Story 概念)_

### 3. 执行层 (Execution)

#### 🧹 CHORE (杂务)

- **Mindset**: _Builder_ (建设者)
- **定义**: **不产生**直接用户价值的工程性事务。
- **场景**: 架构升级、写构建脚本、修复 CI/CD 流水线。
- **Focus**: "How" (为了支撑系统运转，必须做什么)。
- **Prefix**: `CHORE-`

_(取代了 Task 概念)_

#### 🐞 FIX (修复)

- **Mindset**: _Debugger_ (调试者)
- **定义**: 预期与现实的偏差。它是负价值的修正。
- **Focus**: "Fix" (恢复原状)。
- **Prefix**: `FIX-`

_(取代了 Bug 概念)_

---

**关系链**:

- **主要**: `EPIC` (愿景) -> `FEATURE` (价值交付单元)
- **次要**: `CHORE` (工程维护/支撑) - 通常独立存在。
- **原子性原则**: Feature = Design + Dev + Test + Doc + i18n。它们是一体的。

### 4. 节拍层 (Rhythm) [Optional]

#### 🏁 SPRINT (冲刺)

- **Mindset**: _Scrum Master_ / _Delivery Manager_
- **定义**: 固定的时间盒 (Timebox)。用于同步团队节奏和验收成果。
- **作用**: 将扁平的 Atom 流组织成可管理的"闭环"。它是一个**时间锚点**，而非文件夹。
- **使用**: 可选。适用于需要周期性交付的组织。

## 准则 (Guidelines)

### 1. 命名与存储 (Naming & Storage)

采用 **"Type-first, Status-second"** 的分层存储策略，确保结构清晰且易于通过路径过滤。

> **⚠️ 核心准则**:
>
> - **优先使用 CLI**: 必须尽量使用 `monoco issue` 子命令进行操作，以维持元数据与物理路径的一致性。
> - **强制校验**: 任何对 `.md` 文件的手动修改后，**必须**运行 `monoco issue lint` 进行完整性校验。

#### 作用域与分层 (Scoping)

1. **全局层 (Global)**: 存放在项目根目录的 `ISSUES/`。仅关注跨产品的战略目标、系统级架构变动或 meta 问题。
2. **产品层 (Product)**: 存放在具体产品目录内（如 `Chassis/ISSUES/`, `Toolkit/ISSUES/`）。关注该产品内部的功能迭代、Fix 和 Chore。

#### 目录结构

Issue 按类型和状态分层存储于各自作用域的 `ISSUES/` 目录下：

- `ISSUES/{TYPE}/{STATUS}/`
  - `{TYPE}`: `Epics`, `Features`, `Chores`, `Fixes`
  - `{STATUS}`: `open`, `backlog`, `closed`

例如：

- `Toolkit/ISSUES/Epics/open/EPIC-0001-monoco-toolkit.md` (产品级)
- `ISSUES/Features/open/FEAT-0010-enhanced-init.md` (特性)

#### 路径流转规则

- **状态流转**：当使用 `monoco issue open/close/backlog` 命令更新状态时，文件会自动在 `open/`, `backlog/`, `closed/` 目录间物理移动。
- **全局 ID**: `EPIC-` | `FEAT-` | `CHORE-` | `FIX-`。
- **文件名**: `{ID}-{slug}.md`。

### 2. Issue 模板

所有 Issue 必须包含带有 YAML Frontmatter 的标准格式：

```markdown
---
id: TYPE-XXXX # e.g. FEAT-0001, CHORE-0012
type: feature # epic | feature | chore | fix
status: open # open | backlog | closed
title: "简述标题"
parent: [[FEAT-PARENT-ID]] # 关联父级 Issue ID [Optional]
sprint: "SPRINT-YYYY-WXX" # 关联冲刺 ID [Optional]
created_at: YYYY-MM-DD
solution: implemented # implemented | cancelled | wontfix | duplicate [Required for closed]
tags: [tag1, tag2]
---

# ID: 标题

## Objective

## Acceptance Criteria

## Technical Tasks

- [ ]
```

## 工作流指令 (Workflow Instructions)

使用 `monoco issue` 子命令进行操作：

1. **创建 (Create)**:
   `monoco issue create <type> --title "标题" [--parent <id>] [--backlog]`
   - 自动分配下一个可用 ID。
   - 自动根据类型和状态放入对应目录。
2. **流转 (Transition)**:
   - `monoco issue open <id>`: 移至 `open/` 目录。
   - `monoco issue backlog <id>`: 移至 `backlog/` 目录。
   - `monoco issue close <id> [--solution <type>]`: 移至 `closed/` 目录。必须提供或已存在 `solution`。
   - `monoco issue cancel <id>`: 快速关闭并标记为 `cancelled`。
3. **视图 (View)**:
   - `monoco issue scope [--sprint <id>] [--all]`: 以树状结构展示 Issue 进度。
4. **校验 (Check)**:
   - `monoco issue lint`: 检查 ID 重复、物理位置不匹配、断链等完整性问题。
