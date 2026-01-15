---
name: monoco-issue
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

## 准则 (Guidelines)

### 目录结构

`Issues/{CapitalizedPluralType}/{lowercase_status}/`

- `{TYPE}`: `Epics`, `Features`, `Chores`, `Fixes`
- `{STATUS}`: `open`, `backlog`, `closed`

### 路径流转

使用 `monoco issue`：

1. **Create**: `monoco issue create <type> --title "..."`

   - Params: `--parent <id>`, `--dependency <id>`, `--related <id>`, `--sprint <id>`, `--tags <tag>`

2. **Transition**: `monoco issue open/close/backlog <id>`

3. **View**: `monoco issue scope`

4. **Validation**: `monoco issue lint`

5. **Modification**: `monoco issue start/submit/delete <id>`

6. **Commit**: `monoco issue commit` (Atomic commit for issue files)
