# Issue 追踪系统的架构设计

## 1. 核心范式：Task as Code

Monoco Issue 系统采用 "Task as Code" 范式，将任务管理从传统的 SaaS 数据库模型迁移至基于版本控制的文件系统模型。

### 1.1 架构对比

| 特性 | 传统模型 (Jira/Linear) | Monoco 模型 |
| :--- | :--- | :--- |
| **存储后端** | 专有数据库 (RDBMS) | 文件系统 (Markdown) + Git |
| **状态可见性** | 黑盒 (仅 API 可访问) | 白盒 (文本可读/可解析) |
| **版本控制** | 独立于代码库 | 与代码库原子性提交 |
| **一致性保障** | 依赖应用层逻辑 | 依赖 CI/CD 与 Hooks |
| **离线能力** | 不支持 | 原生支持 |

### 1.2 核心优势

1.  **原子性提交 (Atomic Commits)**: 需求文档的变更与代码实现处于同一个 Git Commit 中，确保了“需求-实现”在时间维度上的绝对一致性。
2.  **单一真理源 (Single Source of Truth)**: 所有的任务状态、上下文与决策记录均持久化为仓库中的文本文件，不依赖外部系统的存活。
3.  **可编程性 (Programmability)**: Issue 文件即数据，可被标准 Unix 工具 (grep, sed) 或高级语言解析库直接处理，无需对接专有 API。

## 2. 数据模型 (Schema)

Issue 实例化为结构化的 Markdown 文件，由 YAML Front Matter (元数据) 和 Markdown Body (描述) 组成。

### 2.1 元数据定义

```yaml
---
id: FEAT-0137
type: feature
status: open       # 物理状态：决定文件存储位置
stage: doing       # 逻辑状态：决定工作流阶段
files:             # 作用域边界：受影响文件列表
  - monoco/core/loader.py
  - monoco/core/registry.py
parent: EPIC-0028  # 层级关系
dependencies: []   # 阻塞性依赖
---
```

### 2.2 关键字段解析

#### `files` (Scope Definition)
该字段定义了当前工作单元的**上下文边界 (Context Boundary)** 与 **写操作白名单 (Write ACL)**。

*   **上下文注入**: Agent 启动时，仅加载列表中文件的上下文，减少 Token 消耗与噪音。
*   **影响范围控制**: 配合 Hooks 系统，限制 Agent 仅能修改声明在列表中的文件，防止副作用溢出。
*   **评审契约**: 向 Code Reviewer 承诺变更仅限于此范围，提升评审效率。

#### `status` vs `stage` (State Machine)
Monoco 采用双字段状态机解耦存储与逻辑：

*   **Status (物理状态)**: `open`, `closed`, `backlog`。决定文件在 `Issues/{Type}/{status}/` 目录下的物理位置。
*   **Stage (逻辑状态)**: `draft`, `doing`, `review`, `done`, `freezed`。描述任务在工作流中的精确位置，触发不同的 Hooks 检查规则。

## 3. 可校验性 (Verifiability)

基于文本的存储使得系统状态可以被静态分析工具严格校验。

### 3.1 结构校验 (Linting)
系统内置 Linter 基于 Pydantic Schema 对 Issue 文件进行静态扫描：
*   **完整性检查**: 确保所有必填字段存在且类型正确。
*   **状态矩阵检查**: 验证 `status` 与 `stage` 的组合是否合法 (例如 `status: closed` 时 `stage` 必须为 `done`)。

### 3.2 引用完整性
Linter 自动构建 Issue 间的依赖图谱 (DAG)，校验：
*   `parent` 指向的 Epic 是否存在。
*   `dependencies` 是否形成循环依赖。
*   `files` 中的路径在文件系统中是否真实存在。
