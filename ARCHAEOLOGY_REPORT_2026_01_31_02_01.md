# Monoco Toolkit 考古报告："发行版 (Distro)" 转型 (2026-01-31 至 2026-02-01)

**日期**: 2026-02-01
**作者**: Monoco Kernel (考古模式)
**主题**: 对 48 小时冲刺期间项目演进的深度分析

## 1. 执行摘要 (Executive Summary)

在 2026 年 1 月 31 日至 2 月 1 日期间，Monoco Toolkit 经历了一个变革性的“变态发育”阶段，从单纯的 CLI 工具集进化为自称为 **"无头项目管理操作系统" (Headless Project Management Operating System)** 的复杂系统。这一时期的特点是激进的重构、严格治理结构的建立，以及复杂的“三层技能架构”的实施。

**关键统计数据：**
- **分析提交数**: 约 118 次提交。
- **触及文件**: 271 个唯一文件。
- **主要发布**: 1 月 31 日发布 v0.3.10。
- **关键转型**: 采用 "Linux 发行版" 架构隐喻 (Kernel, Systemd, Package Manager)。

**"失落"的一代**: 此期间的一大批特性工单（`FEAT-0131`, `0132`, `0135`, `0136`, `0127`）在当前的 `Issues/` 目录中已物理消失。这归因于在 `FEAT-0135` 和 `CHORE-0027` 中实施的激进归档策略。然而，通过代码取证，本报告成功挖掘出了它们幸存的“基因片段”。

## 2. 演进时间线 (Timeline of Evolution)

### 2026 年 1 月 31 日：奠基与大清洗 (The Foundation & The Purge)

*   **上午/下午**: 聚焦于 `FEAT-0124` (Issue 生命周期触发器) 和 `CHORE-0024` (Git Hook 优化)。团队确立了 **Session Hooks** (运行时环境)、**Git Hooks** (代码质量) 和 **Workflow Triggers** (业务流程) 之间的职责边界。
*   **17:00 - 18:00**: **资源统一 (`FEAT-0127`)**。`monoco.core.resource` 包诞生，标准化了 Skill、Prompt 和 Config 的发现与加载机制。
*   **18:00 - 19:30**: **大归档 (`CHORE-0027`)**。一次大规模的清理行动归档了 23 个遗留 Epic 和 161 个已关闭的 Atom Issue。这为新架构扫清了障碍。
*   **20:00 - 22:00**: **技能架构革命 (`FEAT-0132`, `FEAT-0128/129`)**。实施了“三层技能架构”。引入 `Planner` 角色，填补了 Manager 和 Engineer 之间的空白。
*   **23:00**: **v0.3.10 发布**。作为这些变更的检查点版本发布。

### 2026 年 2 月 1 日：治理与编排 (Governance & Orchestration)

*   **01:00**: **Memo 反馈环 (`FEAT-0131`)**。Memos 被提升为“通用反馈总线” (Universal Feedback Bus)，允许系统通过捕捉稍纵即逝的想法 (fleeting notes) 进行演进。
*   **09:00 - 10:00**: **归档策略 (`FEAT-0135`)**。正式化了 `.archives/` 目录和 `archived` 状态。
*   **10:00 - 11:00**: **领域治理 (`FEAT-0136`)**。在 Linter 中实施了严格的、感知项目规模的领域覆盖率规则。
*   **深夜 (22:00+)**: **领域重构**。对领域本体论进行了彻底检修 (新增 `AgentEmpowerment`, `Foundation`, `IssueSystem`)。实施了严格的状态一致性强制检查 (`FEAT-0144`)。

## 3. 架构演进："发行版" 隐喻 (The "Distro" Metaphor)

`GEMINI.md` 和 `AGENTS.md` 中记录了最显著的概念转变。Monoco 明确将自身建模为一个 Linux 发行版：

| Monoco 概念 | Linux 隐喻 | 功能职责 |
| :--- | :--- | :--- |
| **Monoco** | **Distro** (Ubuntu/Arch) | 管理策略、工作流和包系统。 |
| **Kimi/Kosong** | **Kernel** (内核) | 智能运行时和执行引擎。 |
| **Session** | **Systemd / Init** | 管理 Agent 进程生命周期和状态。 |
| **Issue** | **Systemd Unit** | 原子的工作单元 (Service/Task)。 |
| **Skill** | **Package** (apt/pacman) | 可安装的能力和工作流包。 |

这个隐喻不仅仅是文档说明；它直接影响了代码结构，特别是 `monoco/daemon/` (操作系统服务) 和 `monoco/core/resource/` (包管理器)。

## 4. 三层技能架构 (The Three-Level Skill Architecture)

对 `monoco/core/skills.py` 和 `monoco/core/skill_framework.py` 的代码分析揭示了 Agent 能力的精细解耦：

1.  **Atom Skills (原子技能 `monoco_atom_*`)**:
    *   不可变的原子能力 (如 "Read File", "Git Commit")。
    *   使用 YAML 定义。
2.  **Workflow Skills (工作流技能 `monoco_workflow_*`)**:
    *   定义操作序列的编排逻辑。
    *   "原子的图谱" (Graph of Atoms)。
    *   示例: `workflow-dev` 将 `atom-code-dev` 的操作编排在一个特定的循环中。
3.  **Role Skills (角色技能 `monoco_role_*`)**:
    *   配置层，注入 Prompt 人设和默认模式。
    *   示例: `role-engineer` 配置 `workflow-dev` 以使用 "Cautious" (谨慎) 心智模式。

这种架构允许在不改变底层 Agent 人设的情况下“热插拔”工作流，或在不破坏高层工作流的情况下升级原子工具。

## 5. Issue 系统革命 (Issue System Revolution)

### 5.1 严格治理 (`FEAT-0136`, `FEAT-0144`)
`monoco/features/issue/linter.py` 被大幅修改以实施“感知规模的治理” (Scale-Aware Governance)。
*   **规模检测**: 系统检查项目是否为“大规模” (>128 issues 或 >32 epics)。
*   **覆盖率规则**: 如果是大规模项目，>75% 的 Epic *必须* 分配领域 (Domains)。
*   **继承性**: 子 Issue 自动继承父级的领域。
*   **严格目录映射**: 状态为 `closed` 的 Issue *必须* 位于 `Issues/Features/closed/`。任何偏差都会触发 Linter 错误。

### 5.2 归档策略 (`FEAT-0135`)
`monoco/features/issue/core.py` 中的实现增加了对 `archived` 状态和目录的支持。这允许系统保持“工作集” (Working Set - 近期 Open/Closed) 的小巧和高性能，同时将历史记录保留在压缩或分离的路径中。

## 6. "失落"的一代：代码取证报告 (Code Forensics Report)

Git 日志中提到的几个 Feature 在 `Issues/` 目录中已消失。基于代码取证，以下是实际发生的情况：

*   **FEAT-0127 (Resource Package)**: 在 `monoco/core/resource/` 中实现。它引入了 `ResourceFinder` 和 `ResourceManager`，统一了从 Python 包加载 Skill、Prompt 和 Config 的方式。
*   **FEAT-0131 (Memo Bus)**: 在 `monoco/features/memo/` 中实现。它向 Scheduler 添加了 `MemoAccumulationPolicy`，允许 Daemon "阅读" 收件箱并在反馈积累到一定程度时触发 Architect Agent。
*   **FEAT-0136 (Domain Governance)**: 如上所述，其逻辑存活于 `linter.py` 和 `validator.py` 中。
*   **FEAT-0132 (Antigravity Sync)**: `monoco/core/workflow_converter.py` 中的代码显示了一个将 Monoco Flow Skills 转换为 "Antigravity Workflows" (可能是针对特定 IDE 集成) 的系统，验证了 "Headless" 的哲学。

## 7. 结论 (Conclusion)

这 48 小时代表了 Monoco Toolkit 的成熟。它从“脚本集合”转变为“受治理的系统”。
*   **优势**: 新的技能架构高度模块化且可扩展。治理 Linter 确保了项目的长期健康。
*   **风险**: 复杂性显著增加。“失落的 Issue”表明归档流程可能过于激进或不透明，若不小心管理，可能会掩盖项目历史 (尽管 Git Log 仍是最终的事实来源)。

**建议**:
1.  验证 `.archives/` 的完整性。
2.  确保在 CI 中运行 `monoco issue lint` 命令，以防止违反新的严格规则。
3.  向最终用户记录并说明“三层技能架构”，因为这是一次重大的范式转变。