# Agent Native Stack：重构后 SaaS 时代的数字基础设施

## 摘要

当前软件行业正处于范式转移的前夜。大多数观点认为 AI Agent 将取代应用层的中间逻辑，留下 "Agent + Database" 的结构。Monoco Toolkit 提出了更激进的终局判断：**数据库（RDBMS）与独立应用界面（Standalone UI）也将消亡**。未来的数字工作环境将收敛为 **FS + Git + IDE + Agent** 的极简原生堆栈。软件工程的最佳实践（DevOps、GitOps）将泛化为所有知识行业的通用工作流。

---

## 1. 激进的收敛：超越 "Agent + Database"

关于 AI 时代的软件架构，存在一种渐进式的观点：Agent 取代 GUI 和 API 胶水层，直接操作现有的数据库（如 PostgreSQL）。这就是所谓的 "Agent + Database" 模式。

然而，我们认为这种收敛还不够彻底。

### 1.1 数据库的解构：为什么是文件系统？

关系型数据库（RDBMS）是 Web 2.0 时代高并发、结构化查询需求的产物。但在 Agent 驱动的知识工作（Knowledge Work）场景中，它存在**三重结构性缺陷**：

#### 缺陷一：Context 的永久性丢失

RDBMS 的写入操作是**无上下文的**：

```sql
UPDATE tasks SET status = 'done' WHERE id = 123;
```

这条 SQL 只记录了"状态变成了 done"，但没有记录：
- **为什么**这个任务被标记完成？
- **谁**做出的决定？
- **基于什么**信息？
- **之前尝试过什么**方案？

> 在知识工作中，**"为什么"往往比"是什么"更重要**。RDBMS 的设计哲学是"当前状态即真理"，这导致了 Context 的永久性丢失。

Monoco 的 **Issue Tracing + Git** 则天然携带上下文：

```markdown
---
id: FEAT-0042
status: closed
stage: done
closed_at: '2026-01-31T15:30:00'
---

## FEAT-0042: 重构用户认证模块

### 决策记录
- **方案选择**: 基于 SPIKE-0012 的调研，放弃 JWT 改用 Session
- **原因**: 团队对 JWT 安全边界理解不一致，Session 更可控
- **风险**: 需要引入 Redis，增加运维复杂度

### 关联文件
- `src/auth/session.py`
- `tests/unit/test_session.py`
```

**整个决策过程、思考脉络、放弃的方案，都被完整保留**。

#### 缺陷二：时间旅行的不可能性

RDBMS 的备份机制是**快照式**的：
- 要么全量备份（成本高）
- 要么增量日志（恢复复杂）

想要回答"三个月前这个任务是什么状态？"需要：
1. 找到当时的备份
2. 恢复到一个临时实例
3. 执行查询

而在 Git 中：

```bash
git log --all --source --full-history -- Issues/Features/done/FEAT-0042.md
```

**时间旅行是原生的、低成本的、即时的**。

更重要的是，Git 的**内容寻址**（Content-Addressable）特性意味着：相同的内容永远有相同的哈希。这提供了**不可篡改的历史**——RDBMS 的 `updated_at` 字段可以被随意修改，但 Git 的 Commit Hash 无法伪造。

#### 缺陷三：平行世界的缺失

RDBMS 是**单线程的、线性的**：
- 没有原生的"分支"概念
- 无法低成本地"假设-推演-回滚"
- 不支持并行探索多个方案

想象一下这个场景：
> 产品经理想尝试 A/B 两种方案，让两个 Agent 分别实现，最后对比选择。

在 RDBMS 中，这需要：
1. 创建两套完全独立的数据库实例
2. 维护复杂的同步逻辑
3. 合并时手动解决冲突

在 Git + Issue Tracing 中：

```bash
# Agent A 在分支 feature/A 工作
git checkout -b feature/A
monoco issue start FEAT-0042

# Agent B 在分支 feature/B 工作  
git checkout -b feature/B
monoco issue start FEAT-0042

# 最后对比合并
git diff feature/A feature/B
```

**Branch 即沙盒，Commit 即快照，Merge 即决策**。

---

**RDBMS vs Git + Issue Tracing 对比**：

| 维度 | RDBMS | Git + Issue Tracing |
|------|-------|---------------------|
| **Context** | 丢失 | 完整保留（决策记录、关联文件） |
| **时间旅行** | 快照备份，恢复成本高 | 原生支持，即时回溯 |
| **平行世界** | 不支持 | Branch 即沙盒，低成本推演 |
| **审计溯源** | 依赖外部日志系统 | Commit Log 即审计链 |
| **Agent 友好度** | SQL 转译成本高 | Text is Native API |

RDBMS 是为**高并发、结构化查询、当前状态**设计的。而知识工作需要**过程记录、历史回溯、分支推演**——这正是 Git 的强项。

Monoco 倡导 **FS (File System) First** 策略。对 Agent 而言，**文本即原生 API（Text is the Native API）**。

- **零阻抗**：Markdown、YAML、JSON 是 LLM 的母语。Agent 阅读文件几乎零成本。
- **物理局域性（Locality of Context）**：代码在哪里，需求文档就在哪里。数据不再隔离在远端的 DB 实例中，而是与工作上下文物理共存。

### 1.2 UI 的消亡：IDE 即通用工作台

应用（App）本质上是功能的孤岛。每个 SaaS 软件都试图构建自己的围墙花园。在 Agent 时代，这种割裂是不可接受的。

未来的交互将收敛到 **IDE（Integrated Development Environment）** 这一通用形态：

- **统一界面**：编辑器（Editor）、终端（Terminal）、文件树（Explorer）构成了知识工作的"铁三角"。
- **按需可视化（Ephemeral GUI）**：当需要图表、看板或复杂表单时，通过 **Webview** 动态加载。这是数据的"投影"，用完即走，不留痕迹。

---

## 2. 新的核心堆栈：Agent Native Infrastructure

在这个被压扁的新世界里，剩下的不再是繁杂的 SaaS 服务，而是一套通用的基础设施堆栈：

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌──────────────────────┐  ┌─────────────────────────────┐  │
│  │         IDE          │  │       Webview (On-Demand)   │  │
│  │ (VSCode, Zed, Cursor)│  │   (Charts, Kanban, Forms)   │  │
│  └──────────┬───────────┘  └──────────────┬──────────────┘  │
└─────────────┼─────────────────────────────┼─────────────────┘
              │                             │
┌─────────────▼─────────────────────────────▼─────────────────┐
│                    Agent Runtime Layer                      │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │  Protocols   │      │   Skills     │      │   CLI     │  │
│  │ (Schema/Lint)│      │  (Logic)     │      │ (Action)  │  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                    Data Persistence Layer                   │
│  ┌──────────────────────┐  ┌─────────────────────────────┐  │
│  │    File System       │  │            Git              │  │
│  │ (Markdown/YAML/Code) │  │ (Version/Transaction/Audit) │  │
│  └──────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Storage: FS + Git

Git 不仅仅是代码版本控制工具，它是**世界上最强大的分布式数据库**：

- **事务隔离（Transactions）**：Branch 即沙盒。Agent 可以自由尝试，失败则丢弃分支（Rollback）。
- **审计与溯源（Audit Log）**：Commit Log 提供了免费且不可篡改的操作记录。原子性提交保证了状态与内容的一致性。
- **分布式协作**：无论是离线工作还是异步合并，Git 的冲突解决机制是多人协作的最优解。

### 2.2 Logic: Agent + CI/CD + Guardrails

业务逻辑不再硬编码在后端服务中，而是解耦为：

- **Agent Skills**：封装特定任务的执行逻辑（"如何写代码"、"如何写周报"）。
- **Guardrails**：以 Linter 和 Validator 的形式存在的**代码化规则（Policy as Code）**。
- **CI/CD**：自动化的流水线，将文件变更转化为业务结果（如：提交 Markdown 合同 -> 自动生成 PDF 并发送邮件）。

---

## 3. 软件工程的泛化：DevOps for Everyone

这一愿景的本质，是**软件工程（Software Engineering）范式对所有知识行业的吞噬**。

我们正在见证 "DevOps" 的泛化：

- **LegalOps**：律师不再在 Word 中来回修订，而在 Git 上提交合同。CI 检查条款合规性，Agent 辅助起草。
- **FinOps**：财务数据是仓库中的 JSON 文件。Linter 检查账目平衡，Webview 展示实时报表。
- **DesignOps**：设计资产由 Git 管理，不仅是图片，更是可复用的组件代码。

在这个未来，**所有人都是工程师**。不是说他们都要写 Python，而是他们都将使用**版本控制、自动化流水线、结构化文本**作为工作的基本载体。

---

## 4. Monoco Toolkit 的历史定位

Monoco Toolkit 是这种 **Agent-Native Architecture** 的原型机与探索者。

我们构建这一套工具链（CLI, LSP, Skills, Hooks），目的不是为了做一个更好的 Jira，而是为了验证这套新范式的可行性：

1.  **抛弃 DB**：证明复杂的状态管理完全可以在 Markdown + Git 上跑通。
2.  **抛弃 App**：证明 CLI + IDE + Webview 足以覆盖从管理到开发的全流程体验。
3.  **定义协议**：探索人与 Agent 协作所需的标准接口（Schema, Frontmatter, Context Structure）。

我们不生产软件，我们定义**协议**（Protocol）与**运行时**（Runtime）。这是构建下一个时代的基础设施所需的全部。

---

## 5. 结语

SaaS 已死，应用将亡。但软件永生。

软件将回归其最纯粹的形态：**数据（Files）、逻辑（Agent）与界面（IDE）**。在这个激进收敛的过程中，中间层消失了，阻碍人机协作的高墙倒塌了。我们终于有机会构建一个真正**以知识为中心（Knowledge-Centric）**而非以应用为中心（App-Centric）的数字世界。
