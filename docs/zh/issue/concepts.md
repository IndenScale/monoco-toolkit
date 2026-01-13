# Monoco Issue 核心概念

本文档定义了 Monoco Issue System 的语义模型，包括 Issue 的分类、状态机以及引用关系。

## 1. 分类体系 (Taxonomy)

Monoco 基于“思维模式”(Mindset) 而非单纯的用户叙事来定义工作单元。

### 1.1 战略层 (Strategy)

#### 🏆 EPIC (史诗)

- **前缀**: `EPIC-`
- **思维模式**: 架构师 (Architect)
- **定义**: 跨越多个周期的宏大目标，是“愿景的容器”。通常包含多个 Feature。
- **产出**: 定义系统的边界与核心价值。

### 1.2 价值层 (Value)

#### ✨ FEATURE (特性)

- **前缀**: `FEAT-`
- **思维模式**: Product Owner / 首席工程师
- **定义**: 系统中具体的、功能性的单元。代表 **价值交付**。
- **原子性原则**: Feature = Design + Dev + Test + Doc + i18n。它们是一个不可分割的整体。
- **注意**: 此概念替代了传统的 "Story"。

### 1.3 执行层 (Execution)

#### 🧹 CHORE (杂务)

- **前缀**: `CHORE-`
- **思维模式**: 构建者 (Builder) / 维护者 (Maintainer)
- **定义**: 工程维护、重构或升级。**不直接产生**用户功能价值，但对系统健康至关重要。
- **场景**: 架构升级、CI/CD 修复、依赖更新。
- **注意**: 此概念替代了传统的 "Task"。

#### 🐛 FIX (修复)

- **前缀**: `FIX-`
- **思维模式**: 调试者 (Debugger)
- **定义**: 修正“预期”与“现实”之间的偏差。
- **注意**: 此概念替代了传统的 "Bug"。

---

## 2. 状态机 (State Machine)

Monoco 使用 **双层状态机** (Two-Layer State Machine) 来管理生命周期：**Status** (物理状态) 和 **Stage** (逻辑阶段)。

### 2.1 物理状态 (Status)

决定 Issue 的**可见性**和**存储位置**。

- **Backlog (搁置)**:

  - **含义**: 尚未排期或暂时搁置的想法。
  - **位置**: `Issues/*/backlog/`
  - **Stage**: 直至被 Pull 前，Stage 锁定为 `Freezed`。

- **Open (开启)**:

  - **含义**: 正在进行或计划近期执行的任务。
  - **位置**: `Issues/*/open/`
  - **Stage**: 可以流转 (Todo -> Doing -> Review)。

- **Closed (关闭)**:
  - **含义**: 生命周期结束。
  - **位置**: `Issues/*/closed/`
  - **Stage**: 强制为 `Done`。

### 2.2 逻辑阶段 (Stage)

描述 Issue 在 `Open` 状态下的**执行进度**。

- **Todo**: 待办。已排期，等待开始。
- **Doing**: 进行中。正在编写代码或设计。通常对应一个 Git 分支或 Worktree。
- **Review**: 评审中。代码已提交，等待合并或验收。
- **Done**: 已完成。仅在 Issue 关闭时达成。

---

## 3. 引用关系 (Topology)

Issue 之间通过三种引用关系连接，构成项目的知识图谱。

### 3.1 引用类型架构

#### Parent (父子关系)

- **语义**: 层级 / 归属。
- **方向**: 多对一 (Many-to-One)。
- **典型场景**: Feature 归属于 Epic; Chore 归属于 Epic。
- **限制**: 不支持循环引用。

#### Dependency (依赖关系)

- **语义**: 阻塞 / 前置条件。
- **方向**: A depends on B (B block A)。
- **限制**: 只有当 B 关闭后，A 才能关闭。

#### Related (关联关系)

- **语义**: 参考 / 上下文。
- **方向**: 双向弱关联。
- **典型场景**: 引用相关的 Issue 以提供背景信息。

### 3.2 跨项目引用 (Workspace Referencing)

支持 Workspace 级的问题追踪。使用命名空间语法引用其他项目的 Issue。

- **语法**: `project_name::ISSUE-ID`
- **示例**: `monoco::EPIC-001`
- **要求**: 需在 `monoco.yaml` 中配置 `members`。
