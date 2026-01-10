---
name: issues-management
description: Monoco Issue System 的官方技能定义。将 Issue 视为通用原子 (Universal Atom)，管理 Epic/Feature/Chore/Fix 的生命周期。
---

# 自我管理 (Monoco Issue System)

使用此技能在 Monoco 项目中创建和管理 **Issue** (通用原子)。

## 核心本体论 (Core Ontology)

### 1. 战略层 (Strategy)

- **🏆 EPIC (史诗)**: 宏大目标，愿景的容器。Mindset: Architect。

### 2. 价值层 (Value)

- **✨ FEATURE (特性)**: 用户视角的价值增量。Mindset: Product Owner。
- **原子性原则**: Feature = Design + Dev + Test + Doc + i18n。它们是一体的。

### 3. 执行层 (Execution)

- **🧹 CHORE (杂务)**: 工程性维护，不产生直接用户价值。Mindset: Builder。
- **🐞 FIX (修复)**: 修正偏差。Mindset: Debugger。

## 准则 (Guidelines)

### 目录结构

`Issues/{CapitalizedPluralType}/{lowercase_status}/`

- `{TYPE}`: `Epics`, `Features`, `Chores`, `Fixes`
- `{STATUS}`: `open`, `backlog`, `closed`

### 路径流转

使用 `monoco issue`：

1. **Create**: `monoco issue create <type> --title "..."`
2. **Transition**: `monoco issue open/close/backlog <id>`
3. **View**: `monoco issue scope`
4. **Validation**: `monoco issue lint`
5. **Modification**: `monoco issue start/submit/delete <id>`
