# Monoco Issue 核心概念

本文档定义了 Monoco Issue System 的语义模型与架构设计。

Monoco Issue System 不仅仅是一个任务列表，而是一个 **通用原子 (Universal Atom)** 和 **可配置状态机 (Configurable State Machine)** 的结合体，旨在为人类工程师和 AI 智能体提供统一的协作界面。

## 1. 架构哲学 (Architecture)

### 1.1 通用原子 (Universal Atom)

在 Monoco 中，所有的工作单元——无论是宏大的史诗 (Epic)、具体的特性 (Feature)，还是琐碎的杂务 (Chore)——都被视为同构的 **Issue**。

- **物理层**: 每一个 Issue 都是一个标准的 Markdown 文件，包含 YAML Frontmatter (元数据) 和 Body (内容)。
- **持久化**: 所有状态变更直接映射到文件系统，无需依赖外部数据库。这使得 Git 成为唯一的真理来源 (Single Source of Truth, SSOT)。

### 1.2 双层状态机 (Two-Layer State Machine)

Monoco 使用一种独特的双层状态机来管理 Issue 的生命周期，以平衡物理存储的稳定性和逻辑流转的灵活性。

#### 物理状态 (Status)

决定 Issue 在文件系统中的**物理位置**和**可见性**。

- **Open**: 活跃状态。文件位于 `Types/open/`。
- **Closed**: 终结状态。文件位于 `Types/closed/`。
- **Backlog**: 冻结状态。文件位于 `Types/backlog/`。

#### 逻辑阶段 (Stage)

决定 Issue 在 Open 状态下的**执行进度**。Stage 的流转完全在内存中进行，不涉及文件移动。

- _Default_: Draft, Doing, Review, Done, Freezed (可配置)

## 2. 核心模型 (Core Model)

### 2.1 分类体系 (Taxonomy) -> 可配置

虽然 Monoco 默认提供了一套基于“思维模式”的分类（Epic/Feature/Chore/Fix），但这完全是**可配置**的。你可以定义自己的类型:

- **Name**: 内部标识符 (e.g., `story`)
- **Label**: 显示名称 (e.g., `User Story`)
- **Prefix**: ID 前缀 (e.g., `STORY`)
- **Folder**: 存储目录 (e.g., `Stories`)

### 2.2 状态流转 (Transitions)

Issue 的生命周期由状态流转驱动。Monoco 倾向于作为一个灵活的追踪系统，而非强制执行工具。

- **Status Transition**: 物理文件的移动 (e.g. Open -> Closed)。
- **Stage Transition**: 逻辑进度的更新 (e.g. Doing -> Review)。

这种设计允许团队灵活定义自己的协作模式，而不被硬编码的规则束缚。

## 3. 引用拓扑 (Topology)

Issue 之间通过三种强类型的引用关系连接，构成项目的知识图谱。

| 关系类型       | 语义        | 方向   | 约束                   |
| :------------- | :---------- | :----- | :--------------------- |
| **Parent**     | 归属/层级   | 多对一 | 子项必须在父项上下文内 |
| **Dependency** | 阻塞/前置   | 任意   | B 未关闭前，A 无法关闭 |
| **Related**    | 参考/上下文 | 双向   | 无强约束               |

### 跨项目引用 (Workspace Referencing)

支持引用同一 Workspace 下其他项目的 Issue: `project_name::ISSUE-ID` (e.g., `backend::API-102`)。
