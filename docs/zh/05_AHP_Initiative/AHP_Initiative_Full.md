<!-- BEGIN FILE: 01_Motivation.md -->

# File: 01_Motivation.md

# 01. 问题定义与动机

## 摘要

自主智能体在软件工程任务中的质量保障面临三个结构性约束：产物形式化验证的不可行性、质量左移的经济性要求，以及过程可观测性的缺失。本文分析这些约束的技术根源，并推导对过程干预框架的需求。

---

## 1. 引言

自主智能体（Autonomous Agents）指能够感知环境、进行决策并执行行动以实现特定目标的计算系统。近年来，基于大型语言模型（LLM）的智能体在代码生成、重构、调试等软件工程任务中展现出显著能力。

然而，将这些智能体部署于生产环境时，**质量保障**（Quality Assurance）成为核心挑战。传统软件工程依赖形式化验证和自动化测试确保正确性，但对于智能体生成的代码和决策，这些手段面临根本性限制。

本文识别出三个约束自主智能体质量保障的结构性问题，并分析其对干预框架的设计启示。

---

## 2. 约束一：产物验证的可行性

### 2.1 问题陈述

**对于复杂软件工程任务，形式化自动验证在理论上和实践中均不可行。**

### 2.2 理论根源

程序正确性判定在一般情况下是图灵不可判定的（Turing, 1936）。即使限于有限状态系统，状态空间爆炸问题使得模型检验（Model Checking）在工业规模代码库中的应用受限（Clarke et al., 1994）。

自主智能体执行的软件工程任务——代码生成、重构、调试——具有以下特征：

- **开放语义**：行为依赖于外部环境（API、库、运行时状态）
- **动态决策**：执行路径在运行时确定，难以预先完全枚举
- **创造性输出**：对于同一需求，可能存在多个合法实现

这些特征使得穷举验证在理论上不可行。

### 2.3 实践后果

生产系统被迫依赖**有限抽样验证机制**：

| 机制           | 抽样对象    | 典型覆盖率 | 局限                 |
| -------------- | ----------- | ---------- | -------------------- |
| 人工代码审查   | Commit / PR | < 1%       | 人力瓶颈，延迟高     |
| 自动化测试     | 执行路径    | 30-70%     | 无法覆盖所有边界条件 |
| 静态分析       | 代码模式    | 语法级     | 无法验证语义正确性   |
| Model-as-Judge | 输出样本    | 孤立评估   | 缺乏上下文感知       |

这些机制受限于**有限理性**（Bounded Rationality, Simon, 1957），即决策者的信息处理能力和时间资源是有限的。

对于可靠性要求为 99.9%（三个九）至 99.999%（五个九）的生产系统，抽样验证无法提供足够的置信度。

### 2.4 设计启示

> **如果结果验证无法提供足够的质量保证，质量保障策略必须前移至执行过程。**

这要求建立一种机制，在智能体执行过程中识别潜在偏差，而非仅依赖事后检验。

---

## 3. 约束二：质量左移的经济性

### 3.1 问题陈述

**智能体执行轨迹的时间和计算成本极高，事后修正模式在经济上不可持续。**

### 3.2 成本结构分析

自主智能体的执行轨迹具有以下成本特征：

- **时间成本**：复杂软件工程任务的执行周期可达数小时
- **调用成本**：单次任务涉及数百至数千次工具调用（文件操作、代码搜索、测试执行、LLM 推理）
- **外部性成本**：执行过程中可能产生不可逆副作用（代码提交、文件删除、资源分配）

### 3.3 事后修正的成本模型

设单次轨迹执行成本为 $C_t$，预期失败重试次数为 $n$，则事后修正（Fail-Diagnose-Retry）模式的总成本为：

$$C_{post} = (n + 1) \cdot C_t$$

其中：

- $C_t$ 包含时间成本、计算成本、外部性成本
- $n$ 取决于任务复杂度和智能体能力，对于探索性任务可能 $n \gg 1$

### 3.4 过程干预的成本模型

若能在执行过程中识别偏差并进行干预，设：

- 干预次数为 $m$
- 单次干预成本为 $C_i$（通常 $C_i \ll C_t$，因为干预不涉及完整重执行）
- 干预成功率为 $p$

则过程干预模式的总成本为：

$$C_{proc} = C_t + m \cdot C_i + (1-p) \cdot n' \cdot C_t$$

其中 $n'$ 为干预失败后仍需重试的次数。

当满足以下条件时，过程干预优于事后修正：

$$m \cdot C_i + (1-p) \cdot n' \cdot C_t < n \cdot C_t$$

由于 $C_i \ll C_t$，即使 $m$ 较大且 $p < 1$，过程干预通常仍具经济优势。

### 3.5 设计启示

> **需要一种机制，在轨迹执行过程中识别偏差并引导修正，而非等待最终结果。**

这要求干预框架具备**实时性**（Real-time）和**渐进性**（Gradual）——既能在早期捕获偏差，又能根据偏差严重程度采取不同强度的响应。

---

## 4. 约束三：过程可观测性的缺失

### 4.1 问题陈述

**当前智能体系统缺乏标准化的过程可观测性框架，导致失效分析依赖个案研究且难以规模化。**

### 4.2 现状分析

当前智能体系统的可观测性实践存在以下局限：

| 维度     | 现状                   | 结构性缺陷                                               |
| -------- | ---------------------- | -------------------------------------------------------- |
| **记录** | 文本级日志             | 缺乏结构化语义，难以机器解析和聚合分析                   |
| **分析** | 个案研究（Case Study） | 依赖人工复盘，无法识别系统性失效模式                     |
| **防护** | 朴素启发式规则         | 仅能检测表层失败（无限循环、超时），无法捕获领域特定模式 |
| **知识** | 领域专家经验           | 以非形式化方式存在，无法编码为自动化规则                 |

### 4.3 失效模式示例

考虑以下领域特定的失效模式：

**模式 A：过早抽象**

- 现象：智能体在需求未完全理解前即创建抽象接口
- 后果：后续需求变更导致接口频繁修改
- 当前检测：无自动化检测，依赖事后代码审查

**模式 B：测试遗漏**

- 现象：智能体实现功能但遗漏边界条件测试
- 后果：生产环境出现未覆盖的异常路径
- 当前检测：依赖代码覆盖率工具，滞后且噪音高

**模式 C：依赖漂移**

- 现象：智能体修改公共 API 但未检查下游调用者
- 后果：破坏性变更引入隐性缺陷
- 当前检测：依赖 CI 失败，延迟高

这些模式具有以下共同特征：

- 可在执行过程中被识别（非事后才能判断）
- 可通过特定信号触发（有明确的前置条件）
- 存在已知的缓解策略（领域知识可编码）

但由于缺乏标准化的**信号协议**，这些知识无法被系统化地捕获和应用。

### 4.4 设计启示

> **需要一种标准化的信号协议，使过程事件可被结构化捕获、语义化分析、规则化响应和历史化沉淀。**

这要求干预框架具备：

- **可扩展性**：允许定义领域特定的信号类型和响应规则
- **可追溯性**：记录信号生成、消费、响应的完整历史
- **可学习性**：支持基于历史数据优化信号规则和响应策略

---

## 5. 综合：问题空间与需求

上述三个约束定义了 AHP 的问题空间：

```
┌─────────────────────────────────────────────────────────────┐
│                       问题空间                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  约束1: 验证不可行  ──────►  需要从"结果验证"转向"过程干预"   │
│       (Feasibility)                                        │
│                          │                                  │
│                          ▼                                  │
│  约束2: 经济不可持续  ◄───  需要"过程信号"实现及时修正        │
│       (Economy)                                           │
│                          │                                  │
│                          ▼                                  │
│  约束3: 观测不可用  ◄──────  需要"结构化信号协议"沉淀知识     │
│       (Observability)                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.1 设计需求推导

从三约束可推导出干预框架的核心需求：

| 约束       | 需求           | 设计目标                           |
| ---------- | -------------- | ---------------------------------- |
| 验证不可行 | **连续干预**   | 在无法完全验证时，提供渐进式控制   |
| 经济不可行 | **实时反馈**   | 在轨迹执行中及时生成和消费信号     |
| 观测不可用 | **结构化协议** | 为过程事件提供统一的描述和交换格式 |

### 5.2 研究问题

基于上述分析，本文提出以下研究问题：

**RQ1（干预强度）**：如何形式化从"完全阻止"到"主动赋能"的连续控制空间，替代二元的允许/拒绝模型？

**RQ2（干预时机）**：如何在智能体执行轨迹中识别适当的干预时点，实现及时修正而非事后重试？

**RQ3（知识沉淀）**：如何建立标准化的信号协议，使领域特定的失效模式可被定义、测量、识别和自动响应？

---

## 6. 相关工作

### 6.1 智能体评估框架

**Braintrust Evaluation Harness** 提供了对智能体输出的后置评估能力，通过模型评判（Model-as-Judge）和人工标注对输出质量进行评分。然而，该框架聚焦于**事后评估**而非**过程干预**，无法解决本文识别的经济性约束。

### 6.2 智能体安全与对齐

**AI Safety** 领域的研究关注智能体的价值对齐（Alignment）和有害行为预防，主要采用**硬性约束**（Hard Constraints）如 RLHF、Constitutional AI 等。这些工作在防止灾难性后果方面有效，但缺乏对**渐进式干预**的支持。

### 6.3 软件工程过程改进

**持续集成/持续交付（CI/CD）** 实践强调自动化测试和快速反馈，但其反馈循环粒度为**代码提交级别**，而非**执行过程级别**。

---

## 7. 结论

本文识别了制约自主智能体质量保障的三个结构性约束：

1. **可行性约束**：产物形式化验证在理论上和实践中的不可行性，迫使质量保障前移至执行过程
2. **经济约束**：智能体执行轨迹的高成本使得事后修正模式在经济上不可持续
3. **可观测性约束**：当前系统缺乏标准化的过程可观测性框架，导致失效分析难以规模化

基于这些约束，后续章节将提出 **Agent Harness Protocol**，一种面向自主智能体执行过程的干预框架。

---

## 参考

- Turing, A. M. (1936). On computable numbers, with an application to the Entscheidungsproblem.
- Rice, H. G. (1953). Classes of recursively enumerable sets and their decision problems.
- Clarke, E. M., Grumberg, O., & Peled, D. A. (1999). Model Checking. MIT Press.
- Simon, H. A. (1957). Models of Man: Social and Rational. Wiley.

<!-- END FILE: 01_Motivation.md -->

================================================================================

<!-- BEGIN FILE: 02_Record_System.md -->

# File: 02_Record_System.md

# 02. 记录系统：Issue Ticket

## 摘要

Issue Ticket 是 AHP 的基础数据单元，采用 Markdown + YAML 的本地文本化格式，作为任务代理协作的共享上下文载体。本文定义 Issue Ticket 的结构、协作模型、关联机制，以及其与 Git 工作流的集成方式。

---

## 1. 设计哲学：文本即记录

### 1.1 为什么选择本地文本

AHP 采用文件系统作为数据存储层，而非数据库或 Web 服务：

| 维度         | 文本文件               | 数据库/Web 服务 |
| ------------ | ---------------------- | --------------- |
| **版本控制** | 原生支持 Git 历史追溯  | 需额外实现      |
| **离线可用** | 完全离线               | 依赖网络连接    |
| **可观测性** | 文件即状态，可直接查看 | 需查询接口      |
| **工具生态** | 通用编辑器、grep、awk  | 专用客户端      |
| **长期存档** | 纯文本，无格式过时风险 | 需迁移维护      |

### 1.2 Markdown + YAML 分离

每个 Issue Ticket 是一个 Markdown 文件，采用 YAML Front Matter 存储结构化数据：

```markdown
---
id: FEAT-0123
type: feature
status: open
---

# 实现用户登录功能

## 背景

...

## 任务清单

- [x] 设计数据库 Schema
- [ ] 实现登录 API
```

**分离原则**：

- **YAML Front Matter**：机器消费的结构化字段（状态、元数据、关联）
- **Markdown Body**：人类阅读的自然语言描述（需求、讨论、决策）

---

## 2. 协作模型：Draft → Doing → Review → Done

### 2.1 状态机定义

Issue Ticket 的生命周期遵循四阶段模型：

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  draft  │───►│  doing  │───►│ review  │───►│  done   │
│ (草稿)   │    │ (进行中) │    │ (审查中) │    │ (已完成) │
└────┬────┘    └────┬────┘    └────┬────┘    └─────────┘
     │              │              │
     └──────────────┴──────────────┘
              (可回退到 draft)
```

| 状态       | 含义             | 准入条件     | 准出条件       |
| ---------- | ---------------- | ------------ | -------------- |
| **draft**  | 待启动的工作单元 | Issue 已创建 | 智能体接受任务 |
| **doing**  | 正在实现中       | 前置依赖满足 | 代码实现完成   |
| **review** | 待审查验证       | 自检清单完成 | 审查通过       |
| **done**   | 已完成并归档     | 审查通过     | -              |

### 2.2 状态转换触发

状态转换由特定事件触发：

| 转换             | 触发事件             | 系统行为                 |
| ---------------- | -------------------- | ------------------------ |
| `draft → doing`  | 智能体 `start` 命令  | 创建工作分支，加载上下文 |
| `doing → review` | 智能体 `submit` 命令 | 运行预提交检查           |
| `review → done`  | 审查者批准           | 合并到主干，清理分支     |
| `review → doing` | 审查者驳回           | 返回修改，记录反馈       |
| `* → draft`      | 任务取消或重置       | 保留历史，重置状态       |

### 2.3 与 Git 的集成

状态映射到 Git 工作流：

```
draft    →  Issue 文件存在于工作目录
          （Git 状态：未追踪或已提交）

doing    →  开发分支活跃
          （Git 状态：branch 存在，有未提交变更）

review   →  PR/MR 已创建（或等效的本地标记）
          （Git 状态：分支已推送，等待合并）

done     →  已合并到主干，Issue 归档
          （Git 状态：commit 在主分支，Issue 移动至归档目录）
```

---

## 3. Schema 设计

### 3.1 核心字段

#### 身份标识

```yaml
id: FEAT-0123 # 人类可读标识
uid: uuid-v4-string # 机器唯一标识
type: feature # issue 类型
```

**类型枚举**：

- `feature`：新功能
- `fix`：缺陷修复
- `chore`：维护任务
- `docs`：文档更新
- `refactor`：代码重构
- `test`：测试补充
- `spike`：技术调研
- `arch`：架构决策

#### 生命周期状态

```yaml
status: doing # 当前状态
stage: implementing # 执行阶段细化
```

**stage 细分**（可选）：

- `investigating`：调研分析
- `designing`：设计阶段
- `implementing`：实现阶段
- `reviewing`：审查阶段
- `verifying`：验证阶段

#### 内容描述

```yaml
title: "实现用户登录功能"
description: |
  作为用户，我希望能够使用邮箱和密码登录系统。
---

## 背景
...

## 目标
...

## 验收标准
- [ ] 标准 1
- [ ] 标准 2
```

### 3.2 爆炸范围记录

`files` 字段记录 Issue 涉及的文件，用于：

- 快速定位相关代码
- 变更影响分析
- 自动同步到 Git

```yaml
files:
  - src/auth/login.py
  - src/auth/models.py
  - tests/auth/test_login.py
```

**自动更新**：通过 `monoco issue sync-files` 命令，系统基于 `git diff` 自动更新此列表。

---

## 4. 关联建模

### 4.1 关联类型

Issue Ticket 支持多种关联机制：

| 关联类型      | 字段         | 用途         | 示例                         |
| ------------- | ------------ | ------------ | ---------------------------- |
| **父子**      | `parent`     | 分解大任务   | Epic → Story                 |
| **依赖**      | `depends_on` | 执行顺序约束 | A 依赖 B 完成                |
| **标签**      | `tags`       | 分类与筛选   | `priority:high`, `area:auth` |
| **Wiki 链接** | `[[ID]]`     | 知识关联     | `[[ARCH-001]]`               |

### 4.2 依赖语义

```yaml
depends_on:
  - FEAT-0120 # 依赖其他 Issue
  - 'config:db' # 依赖配置就绪
```

**依赖解析规则**：

- 被依赖项必须达到 `done` 状态，才能启动依赖项
- 循环依赖被禁止（验证时检测）
- 软依赖（建议性）与硬依赖（强制性）区分

### 4.3 Wiki 链接语法

在 Markdown Body 中使用双括号语法创建关联：

```markdown
本功能依赖 [[ARCH-001]] 中定义的认证架构。
相关实现参考 [[FEAT-0120]] 的用户模型。
```

渲染时解析为可点击链接。

---

## 5. 里程碑与验收标准

### 5.1 Stage 作为里程碑

每个 `stage` 代表一个里程碑，具有独立的验收标准：

```yaml
phases:
  - name: design
    title: '设计阶段'
    status: done
    acceptance_criteria:
      - criterion: 'API 设计文档'
        verification: 'file_exists:docs/api/login.yaml'

  - name: implementation
    title: '实现阶段'
    status: doing
    acceptance_criteria:
      - criterion: '登录 API 实现'
        verification: 'test_pass:tests/api/test_login.py'
```

### 5.2 验收标准语法

| 验证类型  | 语法                 | 说明           |
| --------- | -------------------- | -------------- |
| 测试通过  | `test_pass:<path>`   | 指定测试通过   |
| 文件存在  | `file_exists:<path>` | 文件存在于仓库 |
| 代码审查  | `code_review:<path>` | 审查标记完成   |
| Lint 通过 | `lint_clean:<path>`  | 无风格问题     |
| 自定义    | `custom:<script>`    | 执行验证脚本   |

### 5.3 Checklist 语义

Checklist 是细粒度的可验证任务：

```yaml
checklist:
  - id: 'chk-001'
    item: '设计数据库 Schema'
    checked: true
    verification:
      type: 'test'
      target: 'tests/db/test_schema.py::test_user_table'

  - id: 'chk-002'
    item: '实现登录 API'
    checked: false
    depends_on:
      - 'chk-001'
```

**关键特性**：

- **可回归**：已勾选项可因验证失败而回归
- **依赖传播**：被依赖项回归时，依赖项自动回归

---

## 6. 目录结构约定

### 6.1 文件组织

Issue Ticket 按类型和状态分层存储：

```
Issues/
├── Features/
│   ├── open/
│   │   └── FEAT-0123.md
│   ├── doing/
│   │   └── FEAT-0120.md
│   └── done/
│       └── FEAT-0100.md
├── Fixes/
│   ├── open/
│   └── done/
├── Chores/
│   └── ...
└── Archive/
    └── 2026-Q1/
        └── FEAT-0099.md
```

### 6.2 路径语义

- **文件存在 = 信号待处理**：Inbox 中有未处理的 Issue
- **文件移动 = 状态变更**：从 `open/` 移到 `doing/` 表示启动
- **Git 是档案**：历史记录在 Git 中，不在目录状态里

---

## 7. 设计原则

### 7.1 文件即状态

Issue 的状态由其文件系统位置决定，而非数据库记录：

```python
def get_status(issue_path: Path) -> str:
    """从路径推断状态"""
    return issue_path.parent.name  # 'open', 'doing', 'done'
```

### 7.2 可观测性优先

任何信息都应可直接通过文件系统访问：

```bash
# 查看所有进行中任务
ls Issues/Features/doing/

# 搜索包含特定标签的 Issue
grep -r "area:auth" Issues/

# 查看今日修改的 Issue
find Issues -name "*.md" -mtime 0
```

### 7.3 向前兼容

Schema 演进原则：

- 新增字段：向后兼容（旧文件无该字段）
- 废弃字段：保留解析，不报错
- 类型扩展：使用联合类型（`string | list`）

---

## 8. 结论

本文定义了 AHP 的记录系统：

1. **文本即记录**：Markdown + YAML 的本地文件格式，原生支持版本控制
2. **四阶段模型**：Draft → Doing → Review → Done 的协作生命周期
3. **丰富关联**：parent、dependencies、tags、wiki links 的多维关联
4. **可验证任务**：Stage 里程碑和 Checklist 的自动化验收

记录系统为智能体提供了结构化的工作上下文，是后续 Agent 集成和过程干预的基础载体。

---

## 参考

- [01. 问题定义与动机](./01_Motivation.md)
- [03. 智能体集成](./03_Agent_Integration.md)

<!-- END FILE: 02_Record_System.md -->

================================================================================

<!-- BEGIN FILE: 03_Agent_Integration/01_AGENTS_md.md -->

# File: 03_Agent_Integration/01_AGENTS_md.md

# 3.1 AGENTS.md：上下文配置

## 摘要

`AGENTS.md` 是 AHP 与智能体交互的第一接触点，作为项目级的"宪法"，向智能体注入规则、偏好和上下文信息，确保智能体在正确的约束下工作。

---

## 1. 核心概念

### 1.1 什么是 AGENTS.md

`AGENTS.md` 是一个 Markdown 格式的配置文件，定义了：

- **项目背景与结构**：架构概览、目录组织
- **编码规范与约束**：命名约定、导入规则、代码风格
- **工作流规则**：Git 规范、分支策略、提交流程
- **角色定义**：不同场景下的行为偏好

### 1.2 与 README.md 的区别

| 特性         | README.md          | AGENTS.md          |
| ------------ | ------------------ | ------------------ |
| **目标读者** | 人类开发者         | LLM 智能体         |
| **内容重点** | 项目介绍、快速开始 | 行为规则、约束条件 |
| **更新频率** | 低频（项目稳定后） | 中频（随规则演进） |
| **格式风格** | 自由文本           | 结构化、指令式     |

---

## 2. 文件位置与继承

### 2.1 多级配置体系

支持多级配置，按就近原则继承：

```
~/AGENTS.md                    # 用户级默认
  ↓ (继承并覆盖)
/workspace/AGENTS.md           # 项目级规则
  ↓ (继承并覆盖)
/workspace/subdir/AGENTS.md    # 子目录特定规则
```

### 2.2 继承规则

1. **字段合并**：子级文件补充父级未定义的字段
2. **显式覆盖**：子级明确定义的字段覆盖父级
3. **累加列表**：如 `skills`、`ignore_patterns` 等列表类型字段累加

### 2.3 典型目录结构

```
project/
├── AGENTS.md              # 项目级主配置
├── docs/
│   └── AGENTS.md          # 文档目录特定规则
├── src/
│   └── AGENTS.md          # 源代码目录规则
└── .ahp/
    └── AGENTS.local.md    # 本地覆盖（gitignored）
```

---

## 3. 内容结构规范

### 3.1 标准模板

````markdown
<!-- AGENTS.md 标准模板 -->

# [项目名称] - Agent 上下文

## 1. 项目概览

### 1.1 架构

- 架构风格：[分层/微服务/事件驱动]
- 主要技术栈：[语言/框架/数据库]
- 关键目录结构：
  - `src/domain/`：领域层
  - `src/application/`：应用层
  - `src/infrastructure/`：基础设施层

### 1.2 核心依赖

- 外部服务：API、数据库等
- 内部模块：核心库、工具函数

## 2. 编码规范

### 2.1 命名约定

| 类型 | 规范             | 示例               |
| ---- | ---------------- | ------------------ |
| 模块 | snake_case       | `user_service.py`  |
| 类   | PascalCase       | `UserService`      |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`  |
| 函数 | snake_case       | `get_user_by_id()` |

### 2.2 导入规则

1. 标准库
2. 第三方库
3. 本项目模块（绝对导入）

### 2.3 代码风格

- 缩进：4 空格
- 行长度：100 字符
- 类型注解：必填

## 3. 工作流规则

### 3.1 Git 规范

- 分支策略：Trunk Based Development
- 禁止直接在 main 分支修改
- Issue 必须关联分支
- 提交信息格式：`type(scope): message`

### 3.2 测试要求

- 新功能必须有单元测试
- 测试覆盖率不得低于 80%
- 集成测试放在 `tests/integration/`

### 3.3 代码审查

- 所有提交需通过 PR
- 至少 1 个审批
- CI 检查通过

## 4. 特殊规则

### 4.1 安全约束

- 禁止在代码中硬编码密钥
- 用户输入必须验证和转义
- 敏感操作需审计日志

### 4.2 性能约束

- 数据库查询需有索引
- 批量操作限制 1000 条/次
- 缓存策略：TTL 300s

## 5. 上下文变量

### 5.1 环境变量

```bash
NODE_ENV=production
DEBUG=false
API_BASE_URL=https://api.example.com
```
````

### 5.2 常用命令

```bash
# 运行测试
npm test

# 代码检查
npm run lint

# 构建
npm run build
```

````

### 3.2 必需字段

| 章节 | 说明 | 重要性 |
|------|------|--------|
| 项目概览 | 架构、技术栈、目录结构 | 高 |
| 编码规范 | 命名、导入、风格 | 高 |
| 工作流规则 | Git、测试、审查 | 高 |
| 特殊规则 | 安全、性能约束 | 中 |

---

## 4. 动态上下文生成

### 4.1 上下文组装流程

当智能体启动 Issue 时，AHP 动态组装上下文：

```python
def build_agent_context(issue: IssueTicket) -> str:
    """构建智能体上下文"""
    context_parts = [
        load_agents_md(),           # 项目级配置
        load_issue_context(issue),  # Issue 详情
        load_related_files(issue),  # 关联文件内容
    ]
    return "\n\n---\n\n".join(context_parts)
````

### 4.2 上下文片段示例

````markdown
<!-- AGENTS.md 加载的内容 -->

# 项目概览

本项目采用分层架构...

---

<!-- Issue 详情 -->

# Issue FEAT-0123: 实现用户登录

## 描述

添加基于 JWT 的用户认证系统

## Checklist

- [x] 设计数据库 Schema
- [ ] 实现登录 API
- [ ] 编写单元测试

---

<!-- 关联文件 -->

## 相关文件

### src/models/user.py

```python
class User(Base):
    id: int
    email: str
    password_hash: str
```
````

````

---

## 5. 最佳实践

### 5.1 编写建议

1. **具体而非抽象**
   - ❌ "编写干净的代码"
   - ✅ "函数长度不超过 50 行，复杂度不超过 10"

2. **提供示例**
   - 每个规范都配上代码示例
   - 展示正确和错误的对比

3. **分层组织**
   - 从宏观到微观
   - 先架构，再规范，最后具体规则

4. **保持更新**
   - 技术栈变更时同步更新
   - 新约束及时添加

### 5.2 常见模式

#### 技术栈声明

```markdown
## 技术栈

### 后端
- **语言**：Python 3.11+
- **框架**：FastAPI 0.100+
- **ORM**：SQLAlchemy 2.0+
- **数据库**：PostgreSQL 15+

### 前端
- **框架**：React 18+
- **状态管理**：Zustand
- **样式**：Tailwind CSS
````

#### 架构约束

```markdown
## 架构约束

### 依赖规则

- Domain 层不依赖任何外部层
- Application 层仅依赖 Domain
- Infrastructure 层可依赖所有上层

### 禁止事项

- 禁止在 Domain 层使用 `datetime.now()`，使用注入的 Clock
- 禁止 Repository 直接返回 ORM 对象，必须转换为 Domain 模型
```

---

## 6. 与其他机制的关系

### 6.1 与 Hooks 的关系

```
AGENTS.md          Hooks
    │                │
    ▼                ▼
定义规则          强制执行
"使用 TBD"        禁止 main 分支提交
"测试覆盖 80%"    pre-issue-submit 检查
```

AGENTS.md 定义规则，Hooks 在关键点强制执行。

### 6.2 与 Skills 的关系

```
AGENTS.md          Skills
    │                │
    ▼                ▼
说明可用工具      提供工具实现
"使用 monoco-issue"  `monoco issue` 命令
```

AGENTS.md 说明可用的 Skills，Skills 提供具体实现。

---

## 7. 示例：完整的 AGENTS.md

```markdown
# E-Commerce API - Agent 上下文

## 1. 项目概览

### 1.1 架构

- **风格**： Clean Architecture + CQRS
- **技术栈**：Python 3.11, FastAPI, PostgreSQL, Redis
- **部署**：Docker + Kubernetes

### 1.2 目录结构
```

src/
├── domain/ # 领域层：实体、值对象、领域事件
├── application/ # 应用层：用例、命令、查询
├── infrastructure/ # 基础设施：ORM、API、外部服务
└── interfaces/ # 接口层：控制器、DTO

````

## 2. 编码规范

### 2.1 Python 规范
- 遵循 PEP 8
- 使用 Black 格式化
- 类型注解覆盖率 100%

### 2.2 导入顺序
```python
# 1. 标准库
from datetime import datetime

# 2. 第三方库
from fastapi import APIRouter

# 3. 本项目（按层级）
from domain.models import User
from application.services import UserService
````

### 2.3 错误处理

- 使用自定义异常类
- 不在 Domain 层使用 try-except
- API 层统一捕获并转换

## 3. 工作流规则

### 3.1 Git

- 使用 Trunk Based Development
- 分支命名：`feat/FEAT-XXX-short-desc`
- 提交信息：`feat(auth): add JWT login [FEAT-0123]`

### 3.2 测试

- 单元测试覆盖率 ≥ 80%
- 集成测试覆盖关键路径
- 使用 pytest + pytest-asyncio

### 3.3 Issue 管理

- 使用 `monoco issue` 命令
- 启动前确保 checklist 完整
- 提交前运行 `monoco issue lint`

## 4. 安全约束

- API 密钥使用环境变量
- 密码使用 bcrypt 哈希
- JWT 过期时间 1 小时
- 敏感接口需要 rate limiting

## 5. 性能约束

- 数据库查询需 EXPLAIN 验证
- API 响应时间 < 200ms (p99)
- 批量操作限制 1000 条/次

```

---

## 参考

- [3.2 Agent Hooks](./02_Agent_Hooks.md)
- [3.3 Agent Skills](./03_Agent_Skills.md)
- [04. 控制协议](../04_Control_Protocol.md)

<!-- END FILE: 03_Agent_Integration/01_AGENTS_md.md -->

================================================================================


<!-- BEGIN FILE: 03_Agent_Integration/02_Agent_Hooks.md -->
# File: 03_Agent_Integration/02_Agent_Hooks.md

# 3.2 Agent Hooks：过程干预

## 摘要

Hooks 是在关键执行点插入的验证与干预机制。AHP 实现的 **ACL（Agent Control Language）**，基于社区通用的 Hooks 概念，扩展了 Issue 生命周期相关事件，实现智能体执行过程的干预控制。

---

## 1. 核心概念

### 1.1 什么是 Agent Hooks

Agent Hooks 是 AHP 实现的 ACL（Agent Control Language），是 AHP 控制协议的执行载体，提供：

- **时机选择**：在关键执行点插入干预
- **条件评估**：检查当前状态是否满足要求
- **信号生成**：根据评估结果产生干预信号
- **响应处理**：处理智能体的反馈

### 1.2 与 Git Hooks 的区别

| 特性 | Git Hooks | Agent Hooks |
|------|-----------|-------------|
| **触发时机** | Git 操作前后 | 智能体执行生命周期 |
| **干预对象** | Git 命令 | 智能体决策与工具调用 |
| **响应方式** | 退出码 | 信号强度（Block/Control/Prompt/Aid） |
| **上下文** | 有限的 Git 信息 | 完整的 Issue 与执行上下文 |

---

## 2. 触发器（Triggers）

### 2.1 触发点定义

触发器定义 Hook 的激活时机：

| 触发点 | 时机 | 典型用途 | 适用强度 |
|--------|------|----------|----------|
| `pre-issue-start` | Issue 启动前 | 依赖检查、环境准备 | block, control |
| `post-issue-start` | Issue 启动后 | 上下文加载、初始化 | aid |
| `pre-tool-use` | 工具调用前 | 权限验证、参数检查 | block, control |
| `post-tool-use` | 工具调用后 | 结果验证、日志记录 | aid |
| `pre-issue-submit` | Issue 提交前 | 验收检查、质量门禁 | block, control, prompt |
| `post-issue-submit` | Issue 提交后 | 审查触发、通知 | aid |
| `pre-issue-close` | Issue 关闭前 | 完成验证、归档检查 | block |
| `post-issue-close` | Issue 关闭后 | 复盘生成、度量记录 | aid |

### 2.2 触发器生命周期

```

Issue 生命周期：

pre-issue-start ──► post-issue-start ──► ...执行中... ──► pre-issue-submit ──► post-issue-submit ──► pre-issue-close ──► post-issue-close
│ │ │ │ │ │
▼ ▼ ▼ ▼ ▼ ▼
环境检查 上下文加载 质量门禁 审查触发 完成验证 复盘生成
依赖验证 初始化任务 checklist 通知发送 归档检查 度量记录

````

### 2.3 触发条件

除了时机，还可以配置更细粒度的触发条件：

```yaml
hooks:
  pre-tool-use:
    # 仅对特定工具触发
    when:
      tool: ["Bash", "Write"]

  pre-issue-submit:
    # 基于 Issue 属性
    when:
      issue.type: "feature"
      files.changed_count: "> 10"
````

---

## 3. 预言机（Oracles）

### 3.1 预言机概述

预言机是 Hook 的决策组件，负责评估条件并返回干预信号：

```python
class Oracle(ABC):
    """预言机基类"""

    @abstractmethod
    def evaluate(self, context: HookContext) -> Signal:
        """
        评估条件，返回干预信号。

        Returns:
            Signal: 包含干预强度（block/control/prompt/aid）
        """
        pass
```

### 3.2 内置预言机

| 预言机                   | 功能                  | 默认强度       | 配置参数                                 |
| ------------------------ | --------------------- | -------------- | ---------------------------------------- |
| `ChecklistValidator`     | 检查 checklist 完成度 | block/prompt   | `allow_partial`, `min_completion_rate`   |
| `FileChangeLimiter`      | 限制单次变更文件数    | control        | `max_files`, `action`                    |
| `TestGate`               | 要求测试通过          | block          | `coverage_threshold`, `require_all_pass` |
| `SecurityScanner`        | 扫描安全风险          | block/prompt   | `rules`, `severity_threshold`            |
| `DependencyChecker`      | 检查依赖满足情况      | block          | `manifest_files`                         |
| `LintChecker`            | 代码风格检查          | prompt/control | `linters`, `auto_fix`                    |
| `CommitMessageValidator` | 提交信息验证          | prompt         | `pattern`, `required_fields`             |

### 3.3 预言机配置示例

```yaml
hooks:
  pre-issue-submit:
    # Checklist 验证
    - oracle: ChecklistValidator
      config:
        allow_partial: false # 不允许部分完成
        min_completion_rate: 0.9 # 至少 90% 完成

    # 文件变更限制
    - oracle: FileChangeLimiter
      config:
        max_files: 20 # 最多 20 个文件
        action: control # 超出时自动控制
        control_action: split_batch # 自动分批

    # 测试门禁
    - oracle: TestGate
      config:
        coverage_threshold: 80 # 覆盖率阈值
        require_all_pass: true # 要求全部通过
```

### 3.4 自定义预言机

```python
class MyCustomOracle(Oracle):
    """自定义预言机示例：检查 API 文档完整性"""

    def __init__(self, config: dict):
        self.required_doc_files = config.get("required_files", [])
        self.intensity = config.get("intensity", "prompt")

    def evaluate(self, context: HookContext) -> Signal:
        # 获取变更的文件
        changed_files = context.issue.files.changed

        # 检查是否包含 API 变更
        api_files = [f for f in changed_files if "api" in f or "router" in f]

        if not api_files:
            return Signal.accept()  # 无 API 变更，通过

        # 检查文档是否更新
        doc_files = [f for f in changed_files if "docs" in f or "README" in f]
        missing_docs = []

        for api_file in api_files:
            expected_doc = self._get_expected_doc(api_file)
            if expected_doc not in doc_files:
                missing_docs.append(expected_doc)

        if missing_docs:
            if self.intensity == "block":
                return Signal.block(
                    reason=f"API 文档缺失: {missing_docs}",
                    resolution_path=[f"添加文档: {d}" for d in missing_docs]
                )
            else:
                return Signal.prompt(
                    message=f"检测到 API 变更，建议更新文档: {missing_docs}",
                    suggestions=["更新 API 文档", "确认无需更新"]
                )

        return Signal.accept()
```

---

## 4. 信号系统

### 4.1 信号强度

预言机评估后生成信号，强度分为四级：

| 强度        | 符号 | 强制性 | 智能体行为                          |
| ----------- | ---- | ------ | ----------------------------------- |
| **Block**   | B    | 强制   | 停止操作，根据 resolution_path 修复 |
| **Control** | C    | 自动   | 接受参数调整，继续执行              |
| **Prompt**  | P    | 可选   | 阅读警告，可选择接受建议或继续      |
| **Aid**     | A    | 无     | 异步接收建议，不影响当前流程        |

### 4.2 信号结构

```typescript
interface Signal {
  header: {
    id: string // UUID
    type: string // 信号类型
    timestamp: string // ISO8601
    source: string // 预言机名称
    intensity: 'block' | 'control' | 'prompt' | 'aid'
    correlation_id?: string // 关联信号链
  }
  context: {
    hook: string // 触发点
    issue_id: string // 关联 Issue
    files: string[] // 相关文件
  }
  payload: {
    // Block
    reason?: string
    resolvable?: boolean
    resolution_path?: string[]

    // Control
    modifications?: Modification[]
    reversible?: boolean

    // Prompt
    severity?: 'low' | 'medium' | 'high'
    message?: string
    suggestions?: string[]
    continue_allowed?: boolean

    // Aid
    context_info?: string
    best_practices?: string[]
    follow_ups?: string[]
  }
}
```

### 4.3 信号响应

智能体消费信号后返回响应：

```typescript
interface SignalResponse {
  signal_id: string
  consumed_at: string
  action: ConsumptionAction
  details?: Record<string, any>
}

type ConsumptionAction =
  // Block
  | 'retry_after_fix'
  | 'proceed_with_risk'
  | 'abort'
  // Control
  | 'accept_modification'
  | 'reject_modification'
  // Prompt
  | 'acknowledge'
  | 'apply_suggestion'
  | 'dismiss'
  // Aid
  | 'suggestion_applied'
  | 'suggestion_deferred'
```

---

## 5. Hook 配置

### 5.1 配置文件位置

```
~/.ahp/hooks.yaml              # 用户级默认
  ↓ (继承并覆盖)
./.ahp/hooks.yaml              # 项目级配置
  ↓ (继承并覆盖)
./.ahp/hooks.local.yaml        # 本地覆盖（gitignored）
```

### 5.2 配置格式

```yaml
# hooks.yaml 完整示例

hooks:
  # Issue 启动前
  pre-issue-start:
    - oracle: DependencyChecker
      config:
        manifest_files: ['package.json', 'requirements.txt']
      when:
        # 仅在特定条件下触发
        environment: ['development', 'staging']

  # Issue 启动后
  post-issue-start:
    - oracle: ContextLoader
      config:
        include_files: true
        include_git_history: true

  # 工具调用前
  pre-tool-use:
    - oracle: PermissionChecker
      config:
        dangerous_commands: ['rm -rf', 'DROP TABLE']
        require_confirmation: true
      when:
        tool: ['Bash', 'Database']

  # 工具调用后
  post-tool-use:
    - oracle: ChangeLogger
      config:
        log_level: 'info'
      when:
        tool: ['Write', 'Edit', 'Delete']

  # Issue 提交前 - 质量门禁
  pre-issue-submit:
    # 1. Checklist 验证
    - oracle: ChecklistValidator
      config:
        allow_partial: false
      priority: 1 # 优先执行

    # 2. 文件变更限制
    - oracle: FileChangeLimiter
      config:
        max_files: 20
        action: prompt
      priority: 2

    # 3. 测试门禁
    - oracle: TestGate
      config:
        coverage_threshold: 80
        require_all_pass: true
      priority: 3

    # 4. 安全扫描
    - oracle: SecurityScanner
      config:
        rules: ['no-secrets', 'no-sql-injection']
      priority: 4

  # Issue 提交后
  post-issue-submit:
    - oracle: ReviewTrigger
      config:
        notify_reviewers: true
        create_pr: true

  # Issue 关闭前
  pre-issue-close:
    - oracle: CompletionVerifier
      config:
        require_tests: true
        require_docs: true

  # Issue 关闭后
  post-issue-close:
    - oracle: RetrospectiveGenerator
      config:
        generate_metrics: true
        archive_issue: true
```

### 5.3 配置选项

| 选项       | 类型    | 说明       | 默认值           |
| ---------- | ------- | ---------- | ---------------- |
| `oracle`   | string  | 预言机名称 | 必填             |
| `config`   | object  | 预言机配置 | `{}`             |
| `when`     | object  | 触发条件   | `{}`（总是触发） |
| `priority` | number  | 执行优先级 | 0（并行执行）    |
| `enabled`  | boolean | 是否启用   | `true`           |
| `async`    | boolean | 异步执行   | `false`          |

---

## 6. 执行流程

### 6.1 Hook 执行时序

```
智能体发起操作
      │
      ▼
┌─────────────┐
│ Hook 触发   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 条件过滤    │  <-- when 条件检查
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 预言机评估   │  <-- 按 priority 顺序执行
│ - 条件检查   │
│ - 强度确定   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 信号生成    │
│ - 构造载荷   │
│ - 添加上下文 │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ 信号传递    │────►│ 智能体消费  │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ 响应处理    │
                    │ - 允许继续  │
                    │ - 要求修复  │
                    │ - 参数调整  │
                    └─────────────┘
```

### 6.2 信号处理示例

```python
# 智能体尝试提交
agent.submit_issue("FEAT-0123")

# pre-issue-submit hook 触发
signal = oracle.evaluate(context)

# Case 1: Block
if signal.intensity == "block":
    agent.receive_message("提交被拒绝：checklist 未完成")
    agent.fix_issues(signal.resolution_path)

# Case 2: Control
elif signal.intensity == "control":
    agent.receive_message("batch_size 已从 1000 调整为 100")
    agent.accept_modification(signal.modifications)

# Case 3: Prompt
elif signal.intensity == "prompt":
    agent.receive_message("警告：单次修改超过 20 个文件，建议分步提交")
    choice = agent.decide("继续" | "分步")
```

---

## 7. 设计原则

### 7.1 渐进干预

优先使用低级别控制，必要时升级：

```
首次提交（Prompt）──► 未修复（Control）──► 仍违规（Block）
     ▲                                            │
     └──────────── 修复后继续 ─────────────────────┘
```

### 7.2 上下文敏感

同一规则在不同上下文产生不同强度的信号：

```python
def evaluate_change_size(context: Context) -> Signal:
    changed = len(context.files.changed)

    # 上下文敏感：根据环境调整阈值
    if context.environment == "production":
        threshold = 10
        intensity = "block" if changed > threshold else "allow"
    else:
        threshold = 30
        intensity = "prompt" if changed > threshold else "allow"

    return Signal(intensity=intensity, ...)
```

### 7.3 反馈闭环

干预历史用于优化策略：

```
[干预执行] ──► [效果记录] ──► [策略分析] ──► [规则调整]
     │              │              │
     └──────────────┴──────────────┘
        （信号日志支持持续改进）
```

---

## 8. 完整示例

### 场景：Issue 提交

**背景**：智能体完成 FEAT-0123，执行 `monoco issue submit`

**执行过程**：

```
1. pre-issue-submit hook 触发
   │
   ├─► checklist-validator
   │   发现 2/3 项未完成
   │   → 生成 block 信号
   │
   └─► 智能体接收信号
       "提交被拒绝：checklist 未完成 [chk-003]"
       修复建议："完成 API 文档"

2. 智能体修复后再次提交
   │
   ├─► checklist-validator
   │   全部完成 → 通过
   │
   ├─► change-size-limiter
   │   发现 25 个文件变更
   │   → 生成 prompt 信号
   │
   └─► 智能体接收信号
       "警告：大变更（25 文件），建议分步？"
       选择："继续"（确认可接受）

3. pre-issue-submit 通过
   → Issue 进入 review 状态
   → post-issue-submit hook 触发
      → 生成 aid 信号
      → "已通知审查者，预计 2 小时响应"
```

**信号日志**：

```jsonl
{"timestamp": "2026-02-09T10:00:00Z", "hook": "pre-issue-submit", "intensity": "block", "source": "checklist-validator", "consumed": true, "action": "retry_after_fix"}
{"timestamp": "2026-02-09T10:15:00Z", "hook": "pre-issue-submit", "intensity": "prompt", "source": "change-size-limiter", "consumed": true, "action": "acknowledge"}
{"timestamp": "2026-02-09T10:15:01Z", "hook": "post-issue-submit", "intensity": "aid", "source": "notification", "consumed": true, "action": "suggestion_applied"}
```

---

## 参考

- [3.1 AGENTS.md](./01_AGENTS_md.md)
- [3.3 Agent Skills](./03_Agent_Skills.md)
- [04. 控制协议](../04_Control_Protocol.md)

<!-- END FILE: 03_Agent_Integration/02_Agent_Hooks.md -->

================================================================================

<!-- BEGIN FILE: 03_Agent_Integration/03_Agent_Skills.md -->

# File: 03_Agent_Integration/03_Agent_Skills.md

# 3.3 Agent Skills：能力扩展

## 摘要

Skills 是智能体可调用的工具包，封装领域特定的操作能力。通过标准化的接口定义，Skills 将 AHP 的功能以工具形式暴露给智能体，实现能力的模块化扩展。

---

## 1. 核心概念

### 1.1 什么是 Agent Skills

Agent Skills 是 AHP 提供的扩展机制：

- **能力封装**：将领域操作封装为可调用工具
- **标准化接口**：统一的调用约定和返回格式
- **动态发现**：运行时加载和注册
- **权限控制**：细粒度的访问控制

### 1.2 与 Function Calling 的关系

| 层面       | Function Calling   | Agent Skills                            |
| ---------- | ------------------ | --------------------------------------- |
| **定位**   | LLM 底层能力       | AHP 应用层封装                          |
| **范围**   | 通用工具调用       | 领域特定操作                            |
| **上下文** | 无状态             | 完整的 AHP 上下文感知                   |
| **示例**   | `ReadFile`, `Bash` | `monoco issue start`, `monoco memo add` |

---

## 2. Skill 结构

### 2.1 文件组织

每个 Skill 是一个目录，包含：

```
skills/
└── skill-name/
    ├── SKILL.md          # 使用文档与示例
    ├── schema.yaml       # 参数与返回值定义
    ├── hooks.yaml        # Skill 级 Hooks（可选）
    └── src/              # 实现代码
        ├── __init__.py
        └── tools/
            ├── tool_a.py
            └── tool_b.py
```

### 2.2 SKILL.md 规范

````markdown
# Skill: skill-name

## 描述

一句话描述 Skill 的功能。

## 使用场景

- 场景 1：...
- 场景 2：...

## 可用工具

### tool-name

**描述**：工具功能描述

**参数**：
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| param1 | string | 是 | 参数说明 |
| param2 | number | 否 | 参数说明，默认 10 |

**返回值**：
| 字段 | 类型 | 描述 |
|------|------|------|
| result | string | 操作结果 |
| data | object | 详细数据 |

**示例**：

```python
# 调用示例
result = skill.tool_name(param1="value", param2=20)
```
````

## 最佳实践

1. 建议 1
2. 建议 2

## 注意事项

- 注意点 1
- 注意点 2

````

### 2.3 Schema.yaml 规范

```yaml
# schema.yaml

name: skill-name
description: Skill 描述
version: 1.0.0
author: AHP Team
category: [issue-management, documentation, testing]

tools:
  - name: create
    description: 创建新 Issue
    parameters:
      type:
        type: string
        enum: [feature, fix, chore, docs, refactor]
        description: Issue 类型
      title:
        type: string
        minLength: 5
        maxLength: 100
        description: Issue 标题
      description:
        type: string
        description: 详细描述
      labels:
        type: array
        items:
          type: string
        description: 标签列表
        default: []
    returns:
      issue_id:
        type: string
        description: 生成的 Issue ID
      file_path:
        type: string
        description: Issue 文件路径
      branch_name:
        type: string
        description: 建议的分支名称

  - name: start
    description: 启动 Issue
    parameters:
      id:
        type: string
        description: Issue ID
      branch:
        type: boolean
        description: 是否创建分支
        default: true
      worktree:
        type: boolean
        description: 是否使用 worktree
        default: false
    returns:
      branch_name:
        type: string
        description: 分支名称
      files:
        type: array
        items:
          type: string
        description: 关联文件列表
      worktree_path:
        type: string
        description: worktree 路径（如适用）
````

---

## 3. 内置 Skills

### 3.1 monoco-issue：Issue 生命周期管理

| 工具         | 功能              | 示例调用                                    |
| ------------ | ----------------- | ------------------------------------------- |
| `create`     | 创建新 Issue      | `monoco issue create feature -t "登录功能"` |
| `start`      | 启动 Issue        | `monoco issue start FEAT-0123 --branch`     |
| `sync-files` | 同步文件变更      | `monoco issue sync-files`                   |
| `submit`     | 提交 Issue        | `monoco issue submit FEAT-0123`             |
| `close`      | 关闭 Issue        | `monoco issue close FEAT-0123`              |
| `lint`       | 检查 Issue 完整性 | `monoco issue lint FEAT-0123`               |

**使用场景**：

```python
# 场景 1：开始新任务
agent.use_skill("monoco-issue", "create", {
    "type": "feature",
    "title": "实现用户登录",
    "description": "添加 JWT 认证..."
})

# 场景 2：启动已创建的 Issue
agent.use_skill("monoco-issue", "start", {
    "id": "FEAT-0123",
    "branch": True
})

# 场景 3：提交完成的工作
agent.use_skill("monoco-issue", "submit", {
    "id": "FEAT-0123"
})
```

### 3.2 monoco-memo：快速笔记捕获

| 工具     | 功能            | 示例调用                                         |
| -------- | --------------- | ------------------------------------------------ |
| `add`    | 添加 Memo       | `monoco memo add "需要优化查询性能" -c database` |
| `list`   | 列出待处理 Memo | `monoco memo list`                               |
| `delete` | 删除 Memo       | `monoco memo delete MEMO-001`                    |
| `open`   | 打开 inbox      | `monoco memo open`                               |

**使用场景**：

```python
# 场景：记录临时想法
agent.use_skill("monoco-memo", "add", {
    "content": "数据库查询需要添加索引",
    "context": "performance"
})

# 稍后查看待处理事项
memos = agent.use_skill("monoco-memo", "list")
# 输出：["MEMO-001: 数据库查询需要添加索引"]
```

### 3.3 monoco-spike：外部仓库引用

| 工具     | 功能         | 示例调用                                           |
| -------- | ------------ | -------------------------------------------------- |
| `add`    | 添加外部仓库 | `monoco spike add https://github.com/example/repo` |
| `sync`   | 同步引用内容 | `monoco spike sync`                                |
| `list`   | 列出引用     | `monoco spike list`                                |
| `remove` | 移除引用     | `monoco spike remove repo-name`                    |

**使用场景**：

```python
# 场景：参考开源实现
agent.use_skill("monoco-spike", "add", {
    "url": "https://github.com/awesome-auth/jwt-auth",
    "name": "jwt-reference"
})

# 查看引用
agent.use_skill("monoco-spike", "list")
# 输出：["jwt-reference: https://github.com/..."]
```

### 3.4 monoco-i18n：国际化管理

| 工具    | 功能           | 示例调用            |
| ------- | -------------- | ------------------- |
| `scan`  | 扫描缺失翻译   | `monoco i18n scan`  |
| `sync`  | 同步翻译文件   | `monoco i18n sync`  |
| `check` | 检查翻译完整性 | `monoco i18n check` |

### 3.5 monoco-lint：代码检查

| 工具    | 功能            | 示例调用                         |
| ------- | --------------- | -------------------------------- |
| `run`   | 运行所有 linter | `monoco lint run`                |
| `fix`   | 自动修复问题    | `monoco lint fix`                |
| `check` | 检查特定规则    | `monoco lint check import-order` |

---

## 4. Skill 发现与加载

### 4.1 加载路径

AHP 从以下位置加载 Skills：

```
1. 内置 Skills：~/.ahp/skills/          # AHP 官方提供
2. 项目 Skills：./.ahp/skills/          # 项目自定义
3. 用户 Skills：~/.config/ahp/skills/   # 用户个人
```

加载顺序：内置 → 项目 → 用户（后加载的覆盖先加载的）

### 4.2 发现机制

```python
class SkillRegistry:
    """Skill 注册表"""

    def discover_skills(self) -> list[Skill]:
        """发现所有可用 Skills"""
        skills = []

        for search_path in self.search_paths:
            for skill_dir in search_path.glob("*/"):
                if (skill_dir / "schema.yaml").exists():
                    skill = self._load_skill(skill_dir)
                    skills.append(skill)

        return skills

    def get_skill(self, name: str) -> Skill | None:
        """按名称获取 Skill"""
        return self._skills.get(name)
```

### 4.3 动态加载

```python
# 运行时加载新 Skill
ahp.load_skill("/path/to/custom-skill")

# 重新加载已修改的 Skill
ahp.reload_skill("monoco-issue")
```

---

## 5. Skill 开发

### 5.1 创建新 Skill

```bash
# 使用 CLI 创建模板
monoco skill create my-skill --template python

# 生成目录结构
my-skill/
├── SKILL.md
├── schema.yaml
├── hooks.yaml
└── src/
    ├── __init__.py
    └── tools/
        └── __init__.py
```

### 5.2 实现示例

```python
# src/tools/__init__.py
from ahp import Skill, tool

class MySkill(Skill):
    """自定义 Skill 示例"""

    @tool
    def analyze_code(self, file_path: str, rules: list[str] = None) -> dict:
        """
        分析代码质量。

        Args:
            file_path: 要分析的文件路径
            rules: 要检查的规则列表

        Returns:
            分析结果
        """
        # 实现逻辑
        issues = self._run_analysis(file_path, rules)

        return {
            "file": file_path,
            "issues": issues,
            "score": self._calculate_score(issues)
        }

    @tool
    def fix_issues(self, file_path: str, issue_ids: list[str] = None) -> dict:
        """自动修复代码问题"""
        # 实现逻辑
        fixes = self._apply_fixes(file_path, issue_ids)

        return {
            "file": file_path,
            "fixes_applied": len(fixes),
            "details": fixes
        }
```

### 5.3 注册与使用

```python
# __init__.py
from .tools import MySkill

# 导出 Skill 类
__all__ = ["MySkill"]
```

使用：

```python
# 智能体调用
result = agent.use_skill("my-skill", "analyze_code", {
    "file_path": "src/main.py",
    "rules": ["unused-imports", "complexity"]
})
```

---

## 6. Skill 与 Hooks 的关系

### 6.1 对比

| 维度         | Skills         | Hooks        |
| ------------ | -------------- | ------------ |
| **触发方式** | 智能体主动调用 | 事件被动触发 |
| **控制权**   | 智能体掌握     | AHP 掌握     |
| **用途**     | 扩展能力       | 约束与引导   |
| **返回值**   | 操作结果       | 干预信号     |
| **执行时机** | 按需           | 预设触发点   |

### 6.2 协作关系

```
智能体
  │
  ├─► 调用 Skill ──► 执行操作 ──► 返回结果
  │                     │
  │                     ▼
  │               触发 Hook
  │               （如 post-tool）
  │                     │
  │                     ▼
  └──────────────── 接收信号
                    （如需干预）
```

### 6.3 互补示例

```python
# 智能体调用 Skill
result = agent.use_skill("monoco-issue", "submit", {"id": "FEAT-0123"})

# 内部流程：
# 1. Skill 执行提交逻辑
# 2. 触发 pre-issue-submit Hook
# 3. Hook 检查 checklist（ChecklistValidator）
# 4. 发现未完成项，返回 block 信号
# 5. Skill 返回错误结果，智能体收到反馈

# 智能体响应反馈
agent.fix_issues(["完成 API 文档"])
agent.use_skill("monoco-issue", "submit", {"id": "FEAT-0123"})
# 这次通过，提交成功
```

---

## 7. Skill 级 Hooks

### 7.1 概念

每个 Skill 可以定义自己的 Hooks，在 Skill 调用前后执行：

```yaml
# my-skill/hooks.yaml

hooks:
  pre-invoke:
    # 在 Skill 工具调用前执行
    - oracle: ParameterValidator
      config:
        schema: '${skill.schema}'

  post-invoke:
    # 在 Skill 工具调用后执行
    - oracle: ResultFormatter
      config:
        format: 'json'
```

### 7.2 用途

- **参数验证**：确保输入符合 schema
- **权限检查**：验证智能体有权限调用
- **结果处理**：格式化、缓存、日志
- **副作用**：发送通知、更新状态

---

## 8. 最佳实践

### 8.1 Skill 设计原则

1. **单一职责**：每个 Skill 专注于一个领域
2. **原子操作**：工具粒度适中，可组合使用
3. **幂等性**：相同输入产生相同结果，可重复调用
4. **清晰文档**：SKILL.md 包含完整使用说明

### 8.2 命名规范

| 类型       | 规范             | 示例                               |
| ---------- | ---------------- | ---------------------------------- |
| Skill 名称 | kebab-case，前缀 | `monoco-issue`, `myproject-deploy` |
| 工具名称   | snake_case       | `create`, `start`, `sync_files`    |
| 参数名称   | snake_case       | `issue_id`, `create_branch`        |

### 8.3 错误处理

```python
@tool
def my_tool(self, param: str) -> dict:
    try:
        result = self._do_work(param)
        return {
            "success": True,
            "data": result
        }
    except ValidationError as e:
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "message": str(e),
                "suggestions": e.suggestions
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": "internal_error",
                "message": "操作失败，请重试"
            }
        }
```

---

## 参考

- [3.1 AGENTS.md](./01_AGENTS_md.md)
- [3.2 Agent Hooks](./02_Agent_Hooks.md)
- [04. 控制协议](../04_Control_Protocol.md)

<!-- END FILE: 03_Agent_Integration/03_Agent_Skills.md -->

================================================================================

<!-- BEGIN FILE: 03_Agent_Integration/README.md -->

# File: 03_Agent_Integration/README.md

# 03. 智能体集成

## 摘要

智能体集成层定义 AHP 如何与 LLM 智能体交互。通过 **AGENTS.md** 上下文配置、**Agent Hooks** 触发机制，以及 **Agent Skills** 能力扩展，AHP 将记录系统转化为智能体的可执行环境。

---

## 快速对比：三机制的工作模式

| 维度         | AGENTS.md                 | Agent Hooks                      | Agent Skills                       |
| ------------ | ------------------------- | -------------------------------- | ---------------------------------- |
| **作用时机** | 会话初始化                | 状态转换前/后                    | 按需调用                           |
| **控制方向** | AHP → Agent（单向注入）   | AHP ↔ Agent（双向干预）          | Agent → AHP（主动请求）            |
| **核心功能** | 定义规则与上下文          | 验证与引导                       | 扩展能力工具包                     |
| **Metaphor** | 宪法/用户手册             | 交通信号灯                       | 工具箱                             |
| **文件位置** | `AGENTS.md`（项目根目录） | `.ahp/hooks.yaml`                | `.ahp/skills/` 或 `~/.ahp/skills/` |
| **触发方式** | 自动加载                  | 事件被动触发                     | 智能体主动调用                     |
| **典型示例** | "本项目使用 TBD 工作流"   | "提交前 checklist 未完成 → 阻止" | `monoco issue start FEAT-001`      |
| **性质**     | 社区实践\*                | **AHP 实现的 ACL**               | 社区实践\*                         |

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

| 层级       | 组件      | 功能                   | 触发时机      |
| ---------- | --------- | ---------------------- | ------------- |
| **上下文** | AGENTS.md | 向智能体注入规则与偏好 | 会话初始化    |
| **干预**   | Hooks     | 在关键点验证与引导     | 状态转换前/后 |
| **能力**   | Skills    | 扩展智能体工具集       | 按需调用      |

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

| 章节                                     | 内容                 |
| ---------------------------------------- | -------------------- |
| [3.1 AGENTS.md](./01_AGENTS_md.md)       | 上下文配置机制详解   |
| [3.2 Agent Hooks](./02_Agent_Hooks.md)   | 过程干预与触发器系统 |
| [3.3 Agent Skills](./03_Agent_Skills.md) | 能力扩展与工具包     |

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

| 上下文   | `rm -rf /` 的响应 |
| -------- | ----------------- |
| 生产环境 | Block             |
| 开发环境 | Prompt            |
| 沙箱环境 | Aid（记录即可）   |

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

<!-- END FILE: 03_Agent_Integration/README.md -->

================================================================================

<!-- BEGIN FILE: 04_Control_Protocol.md -->

# File: 04_Control_Protocol.md

# 04. 控制协议

## 摘要

控制协议定义 AHP 的干预机制。通过连续控制光谱确定干预强度，通过信号系统实现干预通信，Hooks 作为集成点将控制逻辑嵌入智能体执行流程。

---

## 1. 协议概述

### 1.1 为什么需要控制协议

智能体执行是开放的生成过程，需要机制在关键节点进行引导而非仅依赖事后验证。控制协议提供：

- **强度分级**：从建议到阻止的连续干预空间
- **时机选择**：在关键执行点插入干预
- **双向通信**：智能体与 AHP 的信息交换格式

### 1.2 协议栈

```
┌─────────────────────────────────────────────────────┐
│  Agent Layer (LLM + Tools)                          │
├─────────────────────────────────────────────────────┤
│  Integration Layer (Hooks)                          │
│  - 触发器（时机选择）                                  │
│  - 预言机（条件评估）                                  │
├─────────────────────────────────────────────────────┤
│  Signal Layer (通信格式)                             │
│  - 信号头（元数据）                                   │
│  - 载荷（干预细节）                                   │
├─────────────────────────────────────────────────────┤
│  Control Layer (强度分级)                            │
│  - Block / Control / Prompt / Aid                   │
├─────────────────────────────────────────────────────┤
│  Record Layer (Issue Tickets)                       │
└─────────────────────────────────────────────────────┘
```

---

## 2. 连续控制光谱

### 2.1 四级干预模型

控制光谱定义从"阻止"到"赋能"的四个干预级别：

| 级别            | 符号 | 强制性 | 时机       | 核心操作  |
| --------------- | ---- | ------ | ---------- | --------- |
| **Blocking**    | B    | 高     | pre-event  | 拒绝执行  |
| **Controlling** | C    | 中     | pre-event  | 参数调整  |
| **Prompting**   | P    | 低     | pre-event  | 风险提醒  |
| **Aiding**      | A    | 无     | post-event | 建议/复盘 |

偏序关系：$B \prec C \prec P \prec A$（强制性递减）

### 2.2 级别语义

#### Blocking（阻止级）

```
IF condition THEN deny_execution
```

**适用场景**：

- 数据丢失风险（不可逆操作）
- 安全合规违规
- 前置条件不满足

**决策结构**：

```json
{
  "level": "blocking",
  "decision": "deny",
  "reason": "Checklist 未完成: [chk-001, chk-002]",
  "resolvable": true,
  "resolution_path": ["完成 chk-001: 设计数据库 Schema", "完成 chk-002: 实现登录 API"]
}
```

#### Controlling（控制级）

```
allow_execution WITH modification
```

**适用场景**：

- 性能影响可控（自动分批）
- 自动修复可行（参数优化）
- 安全降级可接受（沙箱限制）

**决策结构**：

```json
{
  "level": "controlling",
  "decision": "allow_with_modification",
  "modifications": [
    {
      "target": "batch_size",
      "original": 10000,
      "updated": 1000,
      "reason": "避免内存溢出"
    }
  ],
  "reversible": true
}
```

#### Prompting（提示级）

```
allow_execution WITH warning
```

**适用场景**：

- 风险存在但可接受
- 复杂度警告（大变更）
- 依赖提示（影响分析）

**决策结构**：

```json
{
  "level": "prompting",
  "decision": "warn",
  "severity": "medium",
  "message": "单次修改涉及 25 个文件，建议分步提交",
  "suggestions": ["拆分为 3 个独立提交", "先提交核心变更，再提交测试"],
  "continue_allowed": true
}
```

#### Aiding（赋能级）

```
execution_done THEN suggest
```

**适用场景**：

- 最佳实践分享
- 知识沉淀
- 自动化后续

**决策结构**：

```json
{
  "level": "aiding",
  "decision": "suggest",
  "context": "提交完成: 5 文件修改，新增 200 行",
  "suggestions": [
    {
      "type": "best_practice",
      "description": "建议检查测试覆盖率"
    },
    {
      "type": "follow_up",
      "description": "自动创建文档更新任务"
    }
  ]
}
```

### 2.3 级别选择决策树

```
识别风险点
    │
    ▼
风险是否可接受？
    │
    ├──────[否]──────► 能否自动修复？
    │                    ├──[否]──► Blocking
    │                    └──[是]──► Controlling
    │
    ├──────[是]──────► 需提醒？
    │                    ├──[是]──► Prompting
    │                    └──[否]──► 正常执行
    │
    └──────[事后]─────► 建议有用？
                         ├──[是]──► Aiding
                         └──[否]──► 无干预
```

---

## 3. 信号系统

### 3.1 信号定义

信号是 AHP 的基本通信单元，在干预点传递控制信息：

```typescript
interface Signal {
  header: SignalHeader
  context: SignalContext
  payload: SignalPayload
}

interface SignalHeader {
  id: string // UUID
  type: string // 信号类型
  timestamp: string // ISO8601
  source: string // 来源组件
  intensity: 'block' | 'control' | 'prompt' | 'aid'
  correlation_id?: string // 关联信号链
}
```

### 3.2 信号类型

| 类型         | 说明           | 示例                                      |
| ------------ | -------------- | ----------------------------------------- |
| **生命周期** | 智能体执行事件 | `session-start`, `task-complete`          |
| **领域**     | Issue 管理事件 | `pre-issue-start`, `post-issue-submit`    |
| **策略**     | 规则触发       | `security-violation`, `quality-threshold` |

### 3.3 信号强度与消费方式

| 强度      | 消费要求 | 响应时间  | 可忽略     |
| --------- | -------- | --------- | ---------- |
| `block`   | 强制响应 | 同步      | 否         |
| `control` | 自动应用 | 同步      | 否（透明） |
| `prompt`  | 可选响应 | 同步/异步 | 是         |
| `aid`     | 异步消费 | 异步      | 是         |

### 3.4 信号响应

智能体消费信号后返回响应：

```typescript
interface SignalResponse {
  signal_id: string
  consumed_at: string
  action: ConsumptionAction
  details?: Record<string, any>
}

type ConsumptionAction =
  // Block
  | 'retry_after_fix'
  | 'proceed_with_risk'
  | 'abort'
  // Control
  | 'accept_modification'
  | 'reject_modification'
  // Prompt
  | 'acknowledge'
  | 'apply_suggestion'
  | 'dismiss'
  // Aid
  | 'suggestion_applied'
  | 'suggestion_deferred'
```

---

## 4. 与 Hooks 的集成

### 4.1 Hook 作为集成点

Hooks 是控制协议的执行载体，在特定触发点：

1. 评估条件（预言机）
2. 生成信号
3. 传递信号给智能体
4. 处理响应

### 4.2 触发点映射

| Hook 触发点         | 适用强度               | 典型信号类型        |
| ------------------- | ---------------------- | ------------------- |
| `pre-issue-start`   | block, control         | `dependency-check`  |
| `post-issue-start`  | aid                    | `context-loaded`    |
| `pre-tool-use`      | block, control         | `permission-check`  |
| `post-tool-use`     | aid                    | `result-analysis`   |
| `pre-issue-submit`  | block, control, prompt | `quality-gate`      |
| `post-issue-submit` | aid                    | `review-triggered`  |
| `pre-issue-close`   | block                  | `completion-verify` |
| `post-issue-close`  | aid                    | `retrospective`     |

### 4.3 配置示例

```yaml
# .ahp/hooks.yaml

hooks:
  pre-issue-submit:
    # 触发器：提交前
    trigger: pre-issue-submit

    # 预言机列表（按顺序执行）
    oracles:
      - name: checklist-validator
        # 生成信号的条件和强度
        rules:
          - condition: 'checklist.incomplete_count > 0'
            intensity: block
            message: 'Checklist 未完成'

          - condition: 'checklist.incomplete_count > 0 and checklist.completion_rate > 0.8'
            intensity: prompt
            message: '大部分已完成，确认提交？'

      - name: change-size-limiter
        rules:
          - condition: 'files.changed_count > 20'
            intensity: control
            action:
              type: split_suggestion
              max_batch: 10

      - name: test-gate
        rules:
          - condition: 'tests.failed_count > 0'
            intensity: block
            message: '测试未通过'

          - condition: 'coverage.current < coverage.threshold'
            intensity: prompt
            message: '覆盖率低于阈值'
```

### 4.4 执行流程

```
智能体发起操作
      │
      ▼
┌─────────────┐
│ Hook 触发   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 预言机评估   │
│ - 条件检查   │
│ - 强度确定   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 信号生成    │
│ - 构造载荷   │
│ - 添加上下文 │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ 信号传递    │────►│ 智能体消费  │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ 响应处理    │
                    │ - 允许继续  │
                    │ - 要求修复  │
                    │ - 参数调整  │
                    └─────────────┘
```

---

## 5. 设计原则

### 5.1 渐进干预

优先使用低级别控制，必要时升级：

```
首次提交（Prompt）──► 未修复（Control）──► 仍违规（Block）
     ▲                                            │
     └──────────── 修复后继续 ─────────────────────┘
```

### 5.2 上下文敏感

同一规则在不同上下文产生不同强度的信号：

```python
def evaluate_change_size(context: Context) -> Signal:
    changed = len(context.files.changed)

    # 上下文敏感：根据环境调整阈值
    if context.environment == "production":
        threshold = 10
        intensity = "block" if changed > threshold else "allow"
    else:
        threshold = 30
        intensity = "prompt" if changed > threshold else "allow"

    return Signal(intensity=intensity, ...)
```

### 5.3 反馈闭环

干预历史用于优化策略：

```
[干预执行] ──► [效果记录] ──► [策略分析] ──► [规则调整]
     │              │              │
     └──────────────┴──────────────┘
        （信号日志支持持续改进）
```

---

## 6. 完整示例

### 6.1 场景：Issue 提交

**背景**：智能体完成 FEAT-0123，执行 `monoco issue submit`

**执行过程**：

```
1. pre-issue-submit hook 触发
   │
   ├─► checklist-validator
   │   发现 2/3 项未完成
   │   → 生成 block 信号
   │
   └─► 智能体接收信号
       "提交被拒绝：checklist 未完成 [chk-003]"
       修复建议："完成 API 文档"

2. 智能体修复后再次提交
   │
   ├─► checklist-validator
   │   全部完成 → 通过
   │
   ├─► change-size-limiter
   │   发现 25 个文件变更
   │   → 生成 prompt 信号
   │
   └─► 智能体接收信号
       "警告：大变更（25 文件），建议分步？"
       选择："继续"（确认可接受）

3. pre-issue-submit 通过
   → Issue 进入 review 状态
   → post-issue-submit hook 触发
      → 生成 aid 信号
      → "已通知审查者，预计 2 小时响应"
```

### 6.2 信号日志

```jsonl
{"timestamp": "2026-02-09T10:00:00Z", "hook": "pre-issue-submit", "intensity": "block", "source": "checklist-validator", "consumed": true, "action": "retry_after_fix"}
{"timestamp": "2026-02-09T10:15:00Z", "hook": "pre-issue-submit", "intensity": "prompt", "source": "change-size-limiter", "consumed": true, "action": "acknowledge"}
{"timestamp": "2026-02-09T10:15:01Z", "hook": "post-issue-submit", "intensity": "aid", "source": "notification", "consumed": true, "action": "suggestion_applied"}
```

---

## 7. 结论

本文定义了 AHP 的控制协议：

1. **连续控制光谱**：Block / Control / Prompt / Aid 四级干预模型
2. **信号系统**：标准化的通信格式和消费协议
3. **Hook 集成**：将控制逻辑嵌入智能体执行流程

控制协议使 AHP 能够在智能体执行过程中进行渐进式干预，而非仅依赖事后验证，从而实现质量前移和经济优化。

---

## 参考

- [02. 记录系统](./02_Record_System.md)
- [03. 智能体集成](./03_Agent_Integration.md)

<!-- END FILE: 04_Control_Protocol.md -->

================================================================================

<!-- BEGIN FILE: 05_Evolutionary_Dynamics.md -->

# File: 05_Evolutionary_Dynamics.md

# 05. 进化动力学：从启发式提示到确定性验证

## 摘要

AHP 不仅是一个静态的控制框架，更是一个具备自我进化能力的动态系统。本文阐述了 AHP 如何通过"知识演进管道"解决智能体上下文容量有限与工程约束无限增长之间的矛盾。通过将规则从 `AGENTS.md`（启发式提示）逐步卸载至 Agent Hooks（形式化验证），AHP 实现了 Just-in-Time Prompting 机制，在保持上下文简洁的同时，通过环境感知的即时干预降低系统熵值。

---

## 1. 核心矛盾：上下文腐烂 vs. 规则膨胀

### 1.1 认知的边际收益递减

随着项目的演进，工程团队积累了大量的最佳实践、安全约束和风格指南。传统的智能体治理倾向于将这些所有规则写入 System Prompt 或 `AGENTS.md`。

然而，大语言模型的注意力机制存在局限性：

- **竞争效应**：模型需要在"理解任务逻辑"与"遵守边缘规则"之间分配有限的注意力资源。
- **上下文腐烂**：随着 Prompt 长度增加，模型对特定指令的遵循率呈现非线性下降。
- **成本激增**：每个 Token 都会增加推理延迟和经济成本。

### 1.2 激活的不确定性

另一种扩展能力的方式是使用 Agent Skills（工具）。然而，工具的调用依赖于智能体的主动意图（Intent）。研究表明 [^1]，在缺乏明确引导的情况下，智能体往往会忽略可用工具，导致能力处于"休眠"状态。

这就构成了智能体工程的核心困境：**我们希望智能体遵守的规则越来越多，但智能体能够有效承载的上下文空间却是有限的。**

---

## 2. 理论模型：知识演进管道

为了打破上述困境，AHP 提出了一套知识从"软约束"向"硬门禁"流动的演进机制。

### 2.1 演进三阶段

```mermaid
graph LR
    A[失效模式发现] -->|自然语言描述| B(AGENTS.md: 启发式提示)
    B -->|规则固化| C(Agent Hooks: 形式化验证)
    C -->|上下文卸载| D[保持上下文纯净]
```

#### 阶段一：发现 (Discovery)

通过分析 AHP 记录系统（Issue Tickets）中的交互历史，识别反复出现的失效模式（Failure Patterns）。

- _例子_：智能体经常在修改 API 后忘记更新文档。

#### 阶段二：孵化 (Incubation / Heuristic)

将新发现的规则以自然语言形式写入 `AGENTS.md`。

- _形式_：`"规则：修改 API 代码时，必须同步更新相应的文档。"`
- _优势_：部署快，灵活性高，利用 LLM 的通用理解力。
- _劣势_：占用上下文，依赖模型自觉遵守。

#### 阶段三：固化与卸载 (Formalization & Offloading)

当规则足够稳定且可以通过代码逻辑描述时，将其转化为 **Oracle** 并挂载到 **Hook** 上，同时从 `AGENTS.md` 中删除该规则。

- _形式_：编写 `DocumentationOracle`，在 `pre-issue-submit` 阶段自动检查 API 变更与文档变更的对应关系。
- _优势_：零上下文占用，100% 执行率，确定性反馈。

### 2.2 演进的判据

并非所有知识都适合形式化。只有满足以下特征的规则才应进入 Hooks：

1.  **可检测性 (Detectability)**：触发条件有明确的代码特征（如文件路径、AST 变更）。
2.  **高频性 (Frequency)**：该错误频繁发生，值得编写专门代码。
3.  **确定性 (Determinism)**：判断标准清晰，误报率低。

对于模糊的、创造性的建议（如"代码应具有良好的可读性"），仍应保留在 `AGENTS.md` 中。

---

## 3. 机制创新：Hooks 作为 JIT Prompting

### 3.1 动态上下文注入

Agent Hooks 不仅仅是拦截器，本质上是一种 **Just-in-Time (JIT) Prompting** 机制。它通过识别环境模式，判别智能体当前所处的特定情境，从而注入最恰当的提示。

| 机制            | 触发方式 | 时机          | 效果                     |
| :-------------- | :------- | :------------ | :----------------------- |
| **AGENTS.md**   | 静态加载 | 会话开始时    | 全局提示，容易被遗忘     |
| **Agent Hooks** | 动态触发 | 错误发生前/后 | 局部提示，精准且印象深刻 |

### 3.2 熵减效应

在热力学中，熵代表系统的混乱度。智能体在执行任务时，随着步骤增加，偏离目标的概率（熵）往往会增加。

Hooks 通过在关键节点（状态转换）引入负熵（Negative Entropy）：

- **剪枝**：通过 `Blocking` 信号，剪除错误的决策分支。
- **纠偏**：通过 `Prompting` 信号，将智能体的注意力拉回正确轨道。

```
执行轨迹：
Start ──► Step 1 ──► Step 2 (偏差) ──► [Hook 触发: JIT 提示] ──► Step 2 (修正) ──► Goal
                                              ▲
                                              └─ 熵减干预
```

---

## 4. 治理的精细化：基于遥测的动态适应

### 4.1 Hooks 作为传感器

在 AHP 框架中，Hooks 不仅是执行点，更是系统的**遥测传感器（Telemetry Sensors）**。每一个信号的生成、消费和结果都应被结构化记录：

- **触发频率 (Trigger Frequency)**：识别哪些规则是高频触发的热点。
- **修正耗时 (Mean Time to Repair, MTTR)**：智能体在收到 `Blocking` 或 `Prompting` 信号后，平均需要多少次尝试才能通过验证。
- **忽略率 (Dismissal Rate)**：对于 `Prompting` 级别的信号，智能体选择“忽略”的比例。

### 4.2 规则的 ROI 评估

通过聚合统计分析，运营人员可以评估规则的适用性：

- **高频触发 + 高忽略率**：说明该提示可能过于繁琐或不合时宜，属于“无效噪音”，应优化触发条件或降级。
- **高触发 + 长修正耗时**：说明该领域是智能体的“认知盲区”，仅靠 Hook 拦截不够，应加强 `AGENTS.md` 中的背景知识注入或开发专项 Skill。
- **零触发**：说明规则可能已过时，或者防御的失效模式在当前架构下已不存在，应考虑清理以维持系统简洁。

---

## 5. 闭环反馈：智能体的主动申诉机制

### 5.1 智能体作为系统观测者

演进不应只是“人对智能体”的单向治理。AHP 引入了基于 `MEMO.md` 的**主动反馈机制**，赋予智能体对 Harness 系统本身的评价能力。

当智能体在执行任务时感受到以下压力，它可以主动写入 `MEMO.md`：

- **约束冲突**：例如，`AGENTS.md` 要求保持函数短小，但 Hook 逻辑在特定复杂场景下导致了不必要的代码拆分。
- **流程堵点 (Bottlenecks)**：某些 Hook 验证耗时过长，或反馈信息模糊，阻碍了任务进度。
- **最佳实践演进**：智能体在处理最新版本的第三方库时，发现 `AGENTS.md` 中的建议已不再适用。

### 5.2 反馈处理流

1.  **记录**：智能体记录堵点，附带上下文证据，然后继续工作。
2.  **消费**：项目维护者或 Architect 智能体定期审查 `MEMO.md`。
3.  **响应**：根据反馈调整 Hook 强度、更新 `AGENTS.md` 或优化 Skills，实现 Harness 系统与业务需求的动态对齐。

---

## 6. 案例研究：从建议到铁律，再到反馈循环

**场景：禁止在该项目中使用 `print` 进行调试，强制使用 `logger`。**

### 演进与反馈闭环

1.  **初始状态**：智能体大量使用 `print`，导致生产日志混乱。
2.  **AGENTS.md 阶段**：添加 `"禁止使用 print()，必须使用 logging 模块"`。
3.  **Hooks 阶段**：编写 `NoPrintOracle`，在 `pre-issue-submit` 触发 `Blocking`。
4.  **遥测阶段**：发现该 Hook 触发频率极高，但 MTTR 很短（智能体能瞬间修复）。这说明规则明确但容易被遗忘。
5.  **反馈阶段**：智能体在 `MEMO.md` 记录：_"在快速原型开发（Spike 类型 Issue）时，强制使用 logger 增加了样板代码开销，建议对 Spike 类型任务放宽限制。"_
6.  **优化阶段**：调整 Hook 触发逻辑，仅在 `feature` 和 `fix` 类型任务中强制拦截，在 `spike` 类型中改为 `Prompting`。

---

## 7. 结论

AHP 的进化动力学机制解决了智能体工程的可持续性问题。通过建立知识演进管道、遥测分析机制和智能体反馈闭环，我们能够：

1.  **最大化智能体效能**：让智能体专注于任务本身，而非记忆繁琐的规则。
2.  **最小化环境熵**：通过 JIT Prompting 实现高精度的过程控制。
3.  **精细化工程治理**：利用遥测指标指导规则的去冗余与强度调节。
4.  **建立双向契约**：通过 `MEMO.md` 使 Harness 系统具备感知业务需求变更的能力，实现人、智能体与协议的共同演进。

---

## 参考

[^1]: Vercel. "Agents.md outperforms Skills in our agent evals".

<!-- END FILE: 05_Evolutionary_Dynamics.md -->

================================================================================

<!-- BEGIN FILE: 06_Conclusion.md -->

# File: 06_Conclusion.md

# 06. 结论：走向智能体环境工程 (Agent Environment Engineering)

## 摘要

本文作为 AHP (Agent-Human Protocol) 倡议的总结篇章，回顾了自主智能体在软件工程领域面临的结构性挑战，并综合阐述了 AHP 如何通过记录系统、集成机制、控制协议和进化动力学构建一套完整的治理框架。我们主张，随着智能体能力的提升，工程重心应从微观的"提示词工程"（Prompt Engineering）转向宏观的"环境工程"（Environment Engineering），即构建一个具备可观测、可干预、可进化的确定性作业环境，以容纳不确定性的智能体行为。

---

## 1. 引言：不确定性与工程确定性的博弈

软件工程的核心追求是**确定性**（Determinism）——代码的执行结果应当是可预测、可重复的。然而，基于大语言模型（LLM）的自主智能体本质上引入了**随机性**（Stochasticity）和**不确定性**。

AHP 倡议的初衷并非消除智能体的创造性（即不确定性的正面），而是通过一种架构机制，将这种不确定性限制在可控的边界内。在前几章中，我们探讨了：

- **01. 动机**：明确了验证不可行、经济不可持续、观测不可用三大约束，确立了"过程干预"的核心策略。
- **02. 记录系统**：通过 "Text-as-Record" 的 Issue Ticket 建立了人机协作的共享事实来源（Single Source of Truth）。
- **03. 集成机制**：通过 `AGENTS.md`（静态宪法）、Hooks（动态免疫）和 Skills（扩展能力）构成了智能体的生存空间。
- **04. 控制协议**：定义了从 "Blocking" 到 "Aiding" 的连续干预光谱，实现了柔性治理。
- **05. 进化动力学**：揭示了规则如何在系统中流动，通过 JIT Prompting 解决上下文腐烂问题。

本章将综合这些组件，提出"智能体环境工程"的理论框架，并展望其未来发展。

---

## 2. 理论综合：AHP 的三位一体架构

AHP 的核心贡献在于建立了一个**三位一体（Trinity）**的智能体治理架构，分别对应智能体行为的三个维度：

### 2.1 认知锚点 (Cognitive Anchoring) —— AGENTS.md

> _解决"我是谁？我在哪里？即定规则是什么？"的问题。_

相比于不仅依赖模型训练数据，AHP 强调**检索导向推理**（Retrieval-Oriented Reasoning）。`AGENTS.md` 不仅是文档，更是环境的"物理法则"。研究表明（如 Vercel 的案例），这种被动上下文（Passive Context）在传达框架知识方面优于主动工具调用，因为它消除了智能体的决策负载。

### 2.2 行为边界 (Behavioral Bounding) —— Agent Hooks

> _解决"我能做什么？我做错了吗？"的问题。_

这是 AHP 最具创新性的部分。传统的 Agent 框架侧重于"赋能"（通过 Tools/Skills），而 AHP 同样重视"约束"。Hooks 作为**ACL (Agent Control Language)** 的载体，充当了环境的免疫系统。它不仅防止破坏，更通过即时反馈（JIT Prompting）塑造智能体的行为模式，实现"边做边学"。

### 2.3 能力扩展 (Capability Extension) —— Agent Skills

> _解决"我如何改变世界？"的问题。_

Skills 提供了标准化的动作空间。不同于通用的 Function Calling，AHP 的 Skills 是与 Issue 生命周期和记录系统深度绑定的。这使得工具调用不再是孤立的 API 请求，而是具有上下文感知（Context-Aware）的语义动作。

---

## 3. 范式转移：从 Prompt Engineering 到 Environment Engineering

AHP 标志着智能体开发范式的根本转变。

| 维度           | 提示工程 (Prompt Engineering) | 环境工程 (Environment Engineering) |
| :------------- | :---------------------------- | :--------------------------------- |
| **关注点**     | 优化单一输入的文本            | 构建交互的反馈回路                 |
| **控制方式**   | 劝说 (Persuasion)             | 约束 (Constraint)                  |
| **上下文管理** | 静态注入，易超限              | 动态加载，知识卸载                 |
| **错误处理**   | 依赖模型自我修正              | 外部系统拦截与纠偏                 |
| **演进方式**   | 手工调整 Prompt               | 数据驱动的规则进化                 |

**环境工程的核心论点是：** 不要试图通过更好的 Prompt 训练一个完美的智能体，而应该构建一个能够容忍不完美智能体并引导其产出完美结果的**鲁棒环境**。

### 3.1 环境即提示 (Environment as Prompt)

在 AHP 中，环境本身就是提示的一部分。文件系统的结构、Issue 的状态、Git 的历史、Hook 的反馈，共同构成了一个巨大的、隐式的、动态的 Prompt。智能体通过与环境的交互（试错、探索），获得比静态文本更丰富的上下文信息。

### 3.2 治理即服务 (Governance as a Service)

AHP 将治理逻辑从智能体内部剥离，下沉到基础设施层。这意味着：

- **可复用性**：一套 Hooks 规则可以应用于不同的模型（GPT-4, Claude 3.5, DeepSeek）。
- **可维护性**：规则的变更无需重新微调模型或修改复杂的 System Prompt。

---

## 4. 未来展望

### 4.1 Agent-Computer Interface (ACI) 的标准化

AHP 提出的 `AGENTS.md`、Issue Schema 和 Hook 协议，实际上是在定义 **Agent-Computer Interface (ACI)** 的雏形。未来，如同 POSIX 定义了程序与 OS 的接口，ACI 将标准化智能体与软件项目的交互方式。

**研究方向：**

- **LSP for Agents**：类似于 Language Server Protocol，定义智能体获取上下文和执行操作的通用协议。
- **标准化信号集**：建立跨框架的干预信号标准（如 HTTP 状态码之于 Web）。

### 4.2 多智能体协作的制度化

目前的 AHP 主要关注"单智能体-环境"的交互。随着多智能体系统（Multi-Agent Systems）的普及，AHP 需要演进出"社会化"规则：

- **协作协议**：定义智能体之间的交接（Handoff）标准。
- **权限分级**：区分"架构师智能体"（可修改规则）与"工兵智能体"（仅执行任务）。

### 4.3 自我进化的闭环

在 `05. 进化动力学` 中我们探讨了规则的演进。未来的 AHP 系统应当具备自动化的**元治理（Meta-Governance）**能力：

- 系统自动分析 Hook 触发日志，生成新的 `AGENTS.md` 规则建议。
- 智能体通过 A/B 测试验证新规则的有效性。

---

## 5. 结语

智能体工程正在经历从"玩具"（Toy）到"工具"（Tool）的跨越。要实现这一跨越，我们不能仅期待模型能力的摩尔定律，必须在工程侧提供与之匹配的脚手架。

AHP 倡议不仅仅是一套协议，更是一种**对齐（Alignment）**的实践方案——不是通过训练层面的对齐，而是通过**运行时环境（Runtime Environment）**的对齐，确保硅基智能体的无限潜力能够安全、高效、经济地服务于人类的工程目标。

通过 **记录（Record）** 锚定事实，通过 **集成（Integrate）** 扩展能力，通过 **控制（Control）** 守住底线，通过 **进化（Evolve）** 适应变化，AHP 致力于成为智能体时代的 TCP/IP 协议——不可见，但无处不在，支撑起人机协作的未来。

---

## 参考文献

1.  Monoco AHP Initiative Documents (01-05).
2.  Gao, J. (2026). "Agents.md outperforms Skills in our agent evals". Vercel Blog.
3.  Weng, L. (2023). "LLM-powered Autonomous Agents". Lil'Log.
4.  Chase, H. (2023). LangChain Documentation & Concepts.

<!-- END FILE: 06_Conclusion.md -->

================================================================================

<!-- BEGIN FILE: README.md -->

# File: README.md

# Agent Harness Protocol (AHP)

## 摘要

自主智能体（Autonomous Agents）在软件工程任务中的应用面临三个结构性约束：产物形式化验证的不可行性、质量保障的经济性要求，以及过程可观测性的缺失。本文提出**Agent Harness Protocol (AHP)**，一种面向自主智能体执行过程的干预框架。AHP 通过建立连续控制光谱（Control Spectrum）、过程信号系统（Signal System）和结构化工作单元描述（Issue Ticket Schema），试图在保持智能体自主性的同时，实现从"阻止"到"赋能"的渐进式质量保障。

**关键词**：自主智能体、过程干预、质量保障、可观测性、人机协作

---

## 1. 引言

### 1.1 背景

近年来，大型语言模型（LLM）驱动的自主智能体在软件工程任务中展现出显著潜力。这些智能体能够执行代码生成、重构、调试等复杂任务，其执行轨迹通常涉及多步骤决策和工具调用（Claude Code, Gemini CLI, AutoGPT 等）。

然而，将这些智能体部署于生产环境时，质量保障成为核心挑战。传统软件工程依赖形式化验证和自动化测试确保正确性，但对于智能体生成的代码和决策，这些手段面临根本性限制。

### 1.2 文档结构

本文档按以下结构组织：

| 章节                                                                                  | 内容                                       |
| ------------------------------------------------------------------------------------- | ------------------------------------------ |
| [01. 问题定义与动机](./01_Motivation.md)                                              | 三约束分析：验证可行性、经济约束、可观测性 |
| [02. 记录系统](./02_Record_System.md)                                                 | Issue Ticket 的结构化定义与生命周期        |
| [03. 智能体集成](./03_Agent_Integration/)                                             | AGENTS.md、Hooks、Skills 三机制详解        |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.1 AGENTS.md](./03_Agent_Integration/01_AGENTS_md.md)       | 上下文配置机制详解                         |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.2 Agent Hooks](./03_Agent_Integration/02_Agent_Hooks.md)   | 过程干预与触发器系统                       |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.3 Agent Skills](./03_Agent_Integration/03_Agent_Skills.md) | 能力扩展与工具包                           |
| [04. 控制协议](./04_Control_Protocol.md)                                              | 连续控制光谱与信号系统                     |

---

## 2. 核心概念

### 2.1 连续控制光谱（Control Spectrum）

AHP 的核心观察是：智能体控制不应是二元的（允许/拒绝），而应是一个从"阻止"（Blocking）到"赋能"（Aiding）的连续光谱。

```
Blocking ◄──────────────────────────────────────► Aiding
  阻拦              控制              提示              帮助
   │                │                │                │
   ▼                ▼                ▼                ▼
 拒绝操作       限制选项        提醒风险        建议最佳
                                   │            实践/复盘
                              pre-event        post-event
                               (info)           (guide)
```

详见：[04. 控制协议](./04_Control_Protocol.md)

### 2.2 过程信号（Signal）

Signal 是 AHP 中的基本通信单元，携带控制强度信息，在智能体执行过程中的关键时点被生成和消费。

```
┌─────────────────────────────────────────────────────────┐
│                      Signal                             │
├──────────────┬────────────────┬─────────────────────────┤
│   Source     │   Intensity    │      Payload            │
│   (来源)     │   (强度)       │      (载荷)             │
├──────────────┼────────────────┼─────────────────────────┤
│ • pre-event  │ • block        │ • decision              │
│ • post-event │ • control      │ • message               │
│ • periodic   │ • prompt       │ • suggestions           │
│              │ • aid          │ • context               │
└──────────────┴────────────────┴─────────────────────────┘
```

详见：[04. 控制协议](./04_Control_Protocol.md)

### 2.3 结构化工作单元（Issue Ticket）

Issue Ticket 定义了智能体工作的边界、验收标准和完成定义，是 Signal 的上下文载体。

详见：[02. 记录系统](./02_Record_System.md)

### 2.4 智能体集成三机制

AHP 通过三种机制实现与智能体的集成：

| 机制             | 作用             | 类比          |
| ---------------- | ---------------- | ------------- |
| **AGENTS.md**    | 定义规则与上下文 | 宪法/用户手册 |
| **Agent Hooks**  | 关键点验证与引导 | 交通信号灯    |
| **Agent Skills** | 扩展能力工具包   | 工具箱        |

详见：[03. 智能体集成](./03_Agent_Integration/)

---

## 3. 与 Monoco 的关系

AHP 是一个**概念框架**（Conceptual Framework），Monoco 是其**参考实现**（Reference Implementation）。

```
┌─────────────────────────────────────────────────────────────┐
│                         AHP 概念层                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Control   │  │   Signal    │  │   Issue Ticket      │  │
│  │   Spectrum  │  │   System    │  │   Schema            │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │             │
│         └────────────────┴────────────────────┘             │
│                          │                                  │
│                    AHP Protocol                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ 实例化
┌─────────────────────────────────────────────────────────────┐
│                      Monoco 实现层                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Hooks     │  │   Issue     │  │   Skills/           │  │
│  │   System    │  │   Lifecycle │  │   AGENTS.md         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 状态与范围

**当前状态**：概念框架（Conceptual Framework）

**范围边界**：

- AHP 定义**协议规范**，不绑定特定实现
- AHP 关注**单智能体**执行过程，不涉及多智能体协调
- AHP 假设智能体具备**工具调用能力**和**环境感知能力**

---

## 参考

- 存档文档：[.archive/](./.archive/)

<!-- END FILE: README.md -->

================================================================================

<!-- BEGIN FILE: 99_References/agents-md-outperforms-skills-in-our-agent-evals.md -->

# File: 99_References/agents-md-outperforms-skills-in-our-agent-evals.md

---

# ===== 身份标识 =====

id: "vercel-agents-md-outperforms-skills"
title: "AGENTS.md 在我们的智能体评估中表现优于 Skills"

# ===== 来源信息 =====

source: "https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals"
date: "2026-01-27"
author: "Jude Gao"

# ===== 类型分类 =====

type: "blog"

# ===== 国际化 =====

language: "zh"

# ===== 知识治理 =====

company: "Vercel"
domain:

- "AI 智能体"
- "Next.js"
- "开发者工具"
- "机器学习评估"
  tags:
- "AGENTS.md"
- "skills"
- "Next.js"
- "AI 编程智能体"
- "文档"
- "检索导向推理"
- "提示工程"

# ===== 关联知识 =====

related_repos:

- "vercel/next.js"

# ===== 内容摘要（用于 RAG）=====

summary: |
一项对比两种教授编程智能体框架特定知识方法的研究发现，将压缩后的文档索
引嵌入 AGENTS.md 中实现了 100% 的通过率，而 skills 仅为 79%。关键洞察在于：
被动上下文消除了决策点并始终可用，而 skills 需要智能体主动调用，它们在 56%
的情况下未能做到这一点。文章还提供了 npx @next/codemod@canary agents-md
命令来快速设置此方案。

---

> **作者**：Jude Gao（Next.js 软件工程师）
> **发布日期**：2026年1月27日
> **阅读时间**：7 分钟

---

我们原以为 skills 会是教授编程智能体框架特定知识的解决方案。但在构建了专注于 Next.js 16 API 的评估测试后，我们发现了一个意想不到的结果。

一个直接嵌入 `AGENTS.md` 的压缩后 8KB 文档索引实现了 **100% 的通过率**，而即使有明确指示告诉智能体使用它们，skills 的最高通过率也只有 **79%**。如果没有这些指示，skills 的表现甚至还不如没有文档的情况。

下面是我们尝试过的方法、学到的经验，以及如何为你自己的 Next.js 项目设置这一方案。

---

## 我们试图解决的问题

AI 编程智能体依赖的训练数据会逐渐过时。Next.js 16 引入了像 `'use cache'`、`connection()` 和 `forbidden()` 这样的 API，这些在当前模型的训练数据中并不存在。当智能体不了解这些 API 时，它们会生成错误的代码或退回到旧的编程模式。

反过来也可能发生：当你运行的是较旧的 Next.js 版本时，模型可能会建议使用尚不存在于你项目中的新 API。我们希望通过为智能体提供与版本匹配的文档来解决这个问题。

---

## 教授智能体框架知识的两种方法

在深入结果之前，先简要说明我们测试的两种方法：

**Skills** 是一种打包领域知识的开放标准，编程智能体可以使用这些知识。一个 skill 将提示词、工具和文档捆绑在一起，智能体可以按需调用。其理念是：智能体识别到需要框架特定的帮助时，调用 skill 并获取相关文档。

**AGENTS.md** 是项目根目录下的一个 Markdown 文件，为编程智能体提供持久化的上下文。无论你在 `AGENTS.md` 中放入什么内容，智能体在每一轮对话中都能访问到，无需智能体决定加载它。Claude Code 使用 `CLAUDE.md` 实现相同的目的。

我们构建了一个 Next.js 文档 skill 和一个 `AGENTS.md` 文档索引，然后通过评估套件测试哪个表现更好。

---

## 我们最初押注于 skills

Skills 看起来是正确的抽象。你将框架文档打包成一个 skill，智能体在处理 Next.js 任务时调用它，然后生成正确的代码。关注点分离清晰，上下文开销最小，智能体只加载它需要的内容。甚至还有一个不断增长的可用 skill 目录 [skills.sh](https://skills.sh)。

我们预期的流程是：智能体遇到 Next.js 任务 → 调用 skill → 读取与版本匹配的文档 → 生成正确的代码。

然后我们运行了评估测试。

---

## Skills 未能被可靠触发

在 **56% 的评估案例中**，skill 从未被调用。智能体明明可以访问文档，但却没有使用它。添加 skill 相比基线没有任何改进：

| 配置              | 通过率 | 相比基线 |
| ----------------- | ------ | -------- |
| 基线（无文档）    | 53%    | —        |
| Skill（默认行为） | 53%    | +0pp     |

零改进。Skill 存在，智能体可以使用它，但智能体选择不使用。在详细的构建/检查/测试细分指标中，skill 在某些指标上甚至比基线表现更差（测试通过率 58% vs 63%），这表明环境中存在但未使用的 skill 可能会引入噪音或干扰。

这不是我们设置特有的问题。智能体不能可靠地使用可用工具是当前模型的已知局限性。

---

## 明确指示有帮助，但措辞很脆弱

我们尝试在 `AGENTS.md` 中添加明确指示，告诉智能体使用 skill。

> 在编写代码之前，先探索项目结构，
> 然后调用 nextjs-doc skill 获取文档。

这将触发率提高到 95% 以上，通过率提升到 79%。

| 配置               | 通过率 | 相比基线 |
| ------------------ | ------ | -------- |
| 基线（无文档）     | 53%    | —        |
| Skill（默认行为）  | 53%    | +0pp     |
| 带明确指示的 Skill | 79%    | +26pp    |

这是一个不错的改进。但我们发现了一个意想不到的现象：指示的措辞会显著影响智能体的行为。

不同的措辞产生了截然不同的结果：

| 指示                       | 行为                           | 结果           |
| -------------------------- | ------------------------------ | -------------- |
| "你必须调用 skill"         | 先读取文档，锚定在文档模式上   | 错过项目上下文 |
| "先探索项目，再调用 skill" | 先建立心智模型，将文档作为参考 | 更好的结果     |

同一个 skill。同样的文档。基于细微的措辞差异，产生了不同的结果。

在一个评估案例中（`'use cache'` 指令测试），"先调用"方法写出了正确的 `page.tsx`，但完全遗漏了必需的 `next.config.ts` 更改。而"先探索"方法两者都正确处理了。

这种脆弱性让我们担忧。如果细微的措辞调整会产生巨大的行为波动，这种方法对于生产使用来说显得过于脆弱。

---

## 构建可信的评估

在得出结论之前，我们需要可信的评估。我们最初的测试套件存在提示词模糊、测试验证实现细节而非可观察行为、以及聚焦于模型训练数据中已有的 API 等问题。我们没有真正测量我们在乎的东西。

我们通过消除测试泄露、解决矛盾、转向基于行为的断言来强化评估套件。最重要的是，我们添加了针对模型训练数据中不存在的 Next.js 16 API 的测试。

**我们聚焦评估套件中的 API：**

- `connection()` 用于动态渲染
- `'use cache'` 指令
- `cacheLife()` 和 `cacheTag()`
- `forbidden()` 和 `unauthorized()`
- `proxy.ts` 用于 API 代理
- 异步 `cookies()` 和 `headers()`
- `after()`、`updateTag()`、`refresh()`

下文的所有结果都来自这个强化后的评估套件。每种配置都经过相同的测试评判，并重复运行以排除模型方差的影响。

---

## 得到验证的直觉

如果完全消除决策会怎样？与其希望智能体调用 skill，我们可以将文档索引直接嵌入 `AGENTS.md`。不是完整的文档，只是一个告诉智能体在哪里可以找到与项目 Next.js 版本匹配的特定文档文件的索引。然后智能体可以按需读取这些文件，无论你是使用最新版本还是维护旧项目，都能获得版本准确的信息。

我们在注入的内容中添加了一条关键指示：

> **重要**：对于任何 Next.js 任务，优先使用检索导向推理而非预训练导向推理。

这告诉智能体查阅文档，而不是依赖可能过时的训练数据。

---

## 令人惊讶的结果

我们在四种配置上运行了强化评估套件：

**最终通过率：**

| 配置               | 通过率   | 相比基线  |
| ------------------ | -------- | --------- |
| 基线（无文档）     | 53%      | —         |
| Skill（默认行为）  | 53%      | +0pp      |
| 带明确指示的 Skill | 79%      | +26pp     |
| AGENTS.md 文档索引 | **100%** | **+47pp** |

在详细细分指标中，`AGENTS.md` 在构建、检查、测试三个维度都取得了完美分数。

| 配置               | 构建     | 检查     | 测试     |
| ------------------ | -------- | -------- | -------- |
| 基线               | 84%      | 95%      | 63%      |
| Skill（默认行为）  | 84%      | 89%      | 58%      |
| 带明确指示的 Skill | 95%      | 100%     | 84%      |
| AGENTS.md          | **100%** | **100%** | **100%** |

这不是我们预期的结果。这种"笨拙"的方法（一个静态 Markdown 文件）胜过了更复杂的基于 skill 的检索，即使我们微调了 skill 触发器。

### 为什么被动上下文胜过主动检索？

我们的理论归结为三个因素：

1. **没有决策点**。使用 `AGENTS.md` 时，不存在智能体必须决定"我应该查一下吗？"的时刻。信息已经存在。

2. **始终可用**。Skills 是异步加载的，只有在被调用时才加载。`AGENTS.md` 的内容在每一轮对话的系统提示词中都有。

3. **没有顺序问题**。Skills 会产生顺序决策（先读文档 vs 先探索项目）。被动上下文完全避免了这个问题。

---

## 解决上下文膨胀问题

将文档嵌入 `AGENTS.md` 存在上下文窗口膨胀的风险。我们通过压缩解决了这个问题。

最初的文档注入约 40KB。我们将其压缩到 **8KB**（减少了 80%），同时保持 100% 的通过率。压缩后的格式使用管道符分隔的结构，将文档索引打包到最小空间：

```
[Next.js 文档索引]|root: ./.next-docs
|重要：对于任何 Next.js 任务，优先使用检索导向推理而非预训练导向推理
|01-app/01-getting-started:{01-installation.mdx,02-project-structure.mdx,...}
|01-app/02-building-your-application/01-routing:{01-defining-routes.mdx,...}
```

完整的索引涵盖了 Next.js 文档的每个部分。智能体知道在哪里可以找到文档，而无需在上下文中拥有完整内容。当它需要特定信息时，会从 `.next-docs/` 目录读取相关文件。

---

## 亲自尝试

一个命令即可为你的 Next.js 项目设置此方案：

```bash
npx @next/codemod@canary agents-md
```

这个功能是官方 `@next/codemod` 包的一部分。

该命令做三件事：

1. 检测你的 Next.js 版本
2. 下载匹配的文档到 `.next-docs/`
3. 将压缩后的索引注入你的 `AGENTS.md`

如果你使用的智能体支持 `AGENTS.md`（如 Cursor 或其他工具），同样的方法也适用。

---

## 对框架维护者的意义

Skills 并非无用。`AGENTS.md` 方法为智能体处理所有 Next.js 任务提供了广泛的、横向的改进。Skills 更适合垂直的、动作特定的工作流，由用户显式触发，比如"升级我的 Next.js 版本"、"迁移到 App Router"，或应用框架最佳实践。两种方法是互补的。

也就是说，对于一般框架知识，被动上下文目前在按需检索方面表现更好。如果你维护一个框架，希望编程智能体能生成正确的代码，考虑提供一个用户可以添加到他们项目中的 `AGENTS.md` 片段。

### 实用建议

- **不要等待 skills 改进**。随着模型工具使用能力的提升，这个差距可能会缩小，但现在结果才重要。

- **积极压缩**。你不需要在上下文中放置完整文档。一个指向可检索文件的索引同样有效。

- **用评估测试**。构建针对训练数据中不存在的 API 的评估测试。那是文档访问最重要的场景。

- **为检索设计**。结构化你的文档，让智能体可以找到并读取特定文件，而不是需要预先加载所有内容。

目标是让智能体从预训练导向推理转向检索导向推理。`AGENTS.md` 被证明是实现这一目标的最可靠方式。

---

*研究和评估由 Jude Gao 完成。CLI 工具：`npx @next/codemod@canary agents-md`*R

<!-- END FILE: 99_References/agents-md-outperforms-skills-in-our-agent-evals.md -->

================================================================================
