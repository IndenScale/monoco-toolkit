# Agent Onboarding：系统性上下文与知识管理

## 摘要

Agent 的有效运作依赖于高质量的上下文（Context）和结构化的知识输入。本文阐述 Monoco 的 **Agent Onboarding** 体系——一套系统性的方法论，用于管理 Agent 的外部知识摄入、上下文配置和技能组织。该体系包含四个核心组件：**Spike（外部知识库）**、**Context File（环境配置）**、**Skills（能力包）**和 **Glossary（术语体系）**，共同构成 Agent 的"入职培训"基础设施。

---

## 1. 引言：为什么需要 Agent Onboarding？

人类新员工入职时需要：
- **了解公司背景**：阅读员工手册、组织架构文档
- **掌握工作规范**：学习代码规范、提交流程
- **获取领域知识**：理解业务术语、系统架构
- **配置工作环境**：设置开发工具、访问权限

Agent 同样需要类似的"入职流程"。然而，当前大多数 Agent 系统采用**临时性、非结构化的上下文注入**，导致：

- **知识碎片化**：外部参考、最佳实践、项目规范散落在各处
- **上下文漂移**：不同会话间缺乏一致的上下文基准
- **术语不一致**：同一概念在不同文档中有不同表达
- **知识过时**：外部参考库缺乏同步机制

**Agent Onboarding** 旨在解决这些问题，建立一套**可重复、可验证、可演化**的 Agent 上下文管理体系。

---

## 2. 核心组件：Agent 的知识基础设施

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent Onboarding 体系                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │    Spike    │  │Context File │  │   Skills    │  │  Glossary   ││
│  │  外部知识库  │  │  环境配置   │  │   技能包    │  │   术语体系   ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘│
│         │                │                │                │       │
│         ▼                ▼                ▼                ▼       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      Agent 上下文层                              ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        ││
│  │  │ 项目背景  │  │ 工作规范  │  │ 能力工具  │  │ 领域语言  │        ││
│  │  │ 架构知识  │  │ 流程约束  │  │ 工作流    │  │ 概念定义  │        ││
│  │  │ 参考实现  │  │ 质量标准  │  │ 最佳实践  │  │ 命名约定  │        ││
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Spike：外部知识库管理

Spike 系统解决**"Agent 如何安全地学习和引用外部代码"**的问题。

#### 2.1.1 核心概念：Git as Knowledgebase

传统上，开发者通过以下方式学习外部代码：
- 浏览器打开 GitHub 仓库，阅读源码
- 本地 `git clone` 后忘记清理
- 复制代码片段到项目，失去溯源

Spike 将 Git 仓库提升为**一等知识公民**：

```
Spike 工作流

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   发现      │────→│   添加      │────→│   同步      │────→│   引用      │
│  外部仓库   │     │ monoco      │     │ monoco      │     │  在 Issue   │
│             │     │ spike add   │     │ spike sync  │     │  或代码中   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  技术调研              配置记录              本地克隆            智能提示
  竞品分析              URL + 版本            到 .references/     跨仓库跳转
  最佳实践              写入 config           只读访问            架构参考
```

#### 2.1.2 设计原则

| 原则 | 说明 | 实现机制 |
|------|------|----------|
| **只读隔离** | 外部代码不可修改 | `.references/` 目录 + Git 只读权限 |
| **意图追踪** | 记录"为什么引入"而非"引入了什么" | `config.yaml` 保存 URL，不保存内容 |
| **版本锁定** | 可重现的知识状态 | Git commit hash 或 tag |
| **自动清理** | 避免仓库膨胀 | `.gitignore` 忽略，可随时重建 |

#### 2.1.3 典型应用场景

```yaml
# .monoco/config.yaml
project:
  spike_repos:
    # 架构参考：学习优秀的项目结构
    cookiecutter-data-science: https://github.com/drivendata/cookiecutter-data-science
    # API 参考：理解框架设计模式
    fastapi: https://github.com/tiangolo/fastapi
    # 竞品分析：对比类似实现
    langchain: https://github.com/langchain-ai/langchain
```

**Agent 使用模式**：
- **调研阶段**：`monoco spike add <url>` 收集参考仓库
- **设计阶段**：在 Issue 中引用 `.references/cookiecutter-data-science/{{cookiecutter.project_name}}/src` 的结构
- **实现阶段**：对比 `.references/fastapi/fastapi/routing.py` 学习路由设计
- **维护阶段**：`monoco spike sync` 更新参考代码

### 2.2 Context File：环境配置与"宪法"

Context File 解决**"Agent 如何理解当前环境的规则和偏好"**的问题。

#### 2.2.1 层级化配置体系与 Resources 机制

Monoco 采用**三层 Context File 架构**结合 **Resources 目录机制**，实现配置的模块化管理和动态同步：

```
Context File 层级与 Resources 机制

┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3: Project Context (项目级)                                  │
│  ├── AGENTS.md / GEMINI.md / CLAUDE.md  ◄── monoco sync 注入       │
│  └── .monoco/config.yaml                                            │
│  作用域：当前项目                                                    │
│  内容：项目架构、编码规范、提交流程、工具偏好                         │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: Directory Context (目录级)                                │
│  └── {FOLDER}/AGENTS.md                                             │
│  作用域：特定目录及其子目录                                           │
│  内容：模块架构、子系统规范、局部约束                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: Root Context (根级)                                       │
│  └── ~/.monoco/config.yaml                                          │
│  作用域：用户全局                                                     │
│  内容：个人偏好、默认工具、全局别名                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Resources 目录（模块化配置源）                                      │
│                                                                     │
│  monoco/features/issue/resources/                                   │
│  ├── en/AGENTS.md      # Issue 管理指南（英文）                      │
│  ├── zh/AGENTS.md      # Issue 管理指南（中文）                      │
│  └── skills/           # Issue 相关 Flow Skills                     │
│                                                                     │
│  monoco/features/spike/resources/                                   │
│  ├── en/AGENTS.md      # Spike 使用指南                            │
│  ├── zh/AGENTS.md      # Spike 使用指南（中文）                      │
│  └── skills/           # Spike 研究工作流                           │
│                                                                     │
│  设计原则：                                                          │
│  1. 每个 Feature 维护自己的 Resources                               │
│  2. 支持 i18n（多语言）                                              │
│  3. AGENTS.md 通过 monoco sync 聚合到项目根目录                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 Resources 目录的设计哲学

**为什么使用 Resources 目录而不是直接编辑根目录的 AGENTS.md？**

| 问题 | 直接编辑 | Resources 机制 |
|------|----------|----------------|
| **版本控制** | AGENTS.md 可能被用户修改，难以追踪 | Resources 随 Monoco 版本发布，可追溯 |
| **模块化** | 所有内容混杂在一个文件 | 每个 Feature 独立维护，职责清晰 |
| **国际化** | 手动维护多语言版本 | 按语言代码组织，自动选择 |
| **更新机制** | 用户需手动合并更新 | `monoco sync` 自动注入最新内容 |
| **一致性** | 不同项目 AGENTS.md 差异大 | 所有项目共享同一套标准指南 |

**Resources 目录结构**：

```
monoco/features/{feature_name}/resources/
├── en/                          # 英文资源（默认回退语言）
│   ├── AGENTS.md               # Agent 操作指南
│   └── SKILL.md                # Skill 定义（如有）
├── zh/                          # 中文资源
│   ├── AGENTS.md
│   └── SKILL.md
└── skills/                      # Flow Skills（可选）
    └── {skill_name}/
        └── SKILL.md
```

**AGENTS.md 内容规范**：

```markdown
# {Feature Name} (Agent Guidance)

## {Feature Name}

简要描述该功能的作用。

- **命令1**: `monoco {feature} {command}` - 描述
- **命令2**: `monoco {feature} {command}` - 描述

## 关键规则

1. **规则1**: 详细说明
2. **规则2**: 详细说明
   - 子规则 A
   - 子规则 B

## ⚠️ 禁止事项

- 🛑 **禁止 X**: 原因和后果
- 🛑 **禁止 Y**: 原因和后果

> 📖 参考 `{feature}-skill` 获取完整文档。
```

#### 2.2.2 Context File 的内容规范

以 `AGENTS.md` 为例，标准结构包括：

```markdown
# 项目 Context

## 项目概述
- 项目目标与核心价值
- 技术栈与架构决策
- 关键依赖与版本

## 编码规范
- 命名约定（函数、类、变量）
- 代码组织原则
- 注释与文档要求

## 工作流程
- Issue 生命周期管理
- 分支策略与提交规范
- 代码审查标准

## 工具配置
- Linter 与 Formatter 设置
- 测试框架与覆盖率要求
- CI/CD 流水线说明

## 禁止事项
- 🛑 严禁直接修改 main 分支
- 🛑 禁止提交未通过 lint 的代码
- 🛑 禁止在 Issue 中使用后缀 ID（如 FEAT-0001-1）
```

#### 2.2.3 monoco init + monoco sync：初始化与同步机制

Monoco 通过 **`init`** 和 **`sync`** 两个核心命令，实现 Agent 环境的自动化配置：

##### monoco init：项目初始化

`monoco init` 是 Agent Onboarding 的**入口命令**，负责创建项目的基础结构和配置：

```
monoco init 执行流程

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   启动      │────→│  全局配置   │────→│  项目配置   │────→│  目录结构   │
│  monoco     │     │  ~/.monoco/ │     │  .monoco/   │     │   初始化    │
│   init      │     │  config.yaml│     │  *.yaml     │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  交互式/命令行         作者信息            项目身份            Issues/
  参数收集              遥测设置            工作区配置          .references/
                      （可选）            Hooks 配置          .monoco/roles/

┌─────────────┐     ┌─────────────┐
│  Feature    │────→│   Git       │
│  初始化     │     │  Hooks      │
│             │     │  安装       │
└─────────────┘     └─────────────┘
       │
       ▼
  遍历所有已注册
  的 Features，
  调用 feature.initialize()
```

**生成的配置文件**：

```yaml
# .monoco/project.yaml - 项目身份
project:
  name: MyProject
  key: MP

# .monoco/workspace.yaml - 工作区配置
paths:
  issues: Issues
  spikes: .references
hooks:
  pre-commit: monoco issue lint --recursive
```

**初始化目录结构**：

```
project-root/
├── .monoco/                     # Monoco 配置目录
│   ├── project.yaml             # 项目身份
│   ├── workspace.yaml           # 环境配置
│   └── roles/                   # Agent 角色定义（从 resources 复制）
├── Issues/                      # Issue 追踪目录
├── .references/                 # Spike 外部知识库
└── AGENTS.md / GEMINI.md        # 由 monoco sync 生成
```

##### monoco sync：环境同步

`monoco sync` 是 Agent Onboarding 的**持续维护命令**，负责将 Features 的 Resources 同步到项目环境：

```
monoco sync 执行流程

┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   启动      │────→│  Feature    │────→│  收集       │────→│  角色分发   │
│  monoco     │     │  注册       │     │  Prompts    │     │  Roles      │
│   sync      │     │  Registry   │     │  & Skills   │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  加载配置              遍历所有            每个 Feature         从 resources/
  检测 Agent            已注册 Feature      调用 integrate()     roles/ 复制到
  框架类型            收集 AGENTS.md                          .monoco/roles/
                      和 Skills

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Skills     │────→│  Prompt     │────→│  目标文件   │
│  分发       │     │  注入       │     │  更新       │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  根据配置语言        使用 PromptInjector    更新 GEMINI.md
  (i18n.source_lang)  将收集的 Prompts     CLAUDE.md 等
  分发到 .agent/      注入到目标文件
  .claude/ 等
```

**Feature Registry 与 Integration 机制**：

```python
# 每个 Feature 实现 MonocoFeature 接口
class IssueFeature(MonocoFeature):
    @property
    def name(self) -> str:
        return "issue"
    
    def initialize(self, root: Path, config: Dict) -> None:
        # init 阶段：创建 Issues/ 目录结构
        pass
    
    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        # sync 阶段：返回 AGENTS.md 内容
        lang = config.get("i18n", {}).get("source_lang", "en")
        prompt_file = Path(__file__).parent / "resources" / lang / "AGENTS.md"
        content = prompt_file.read_text()
        return IntegrationData(
            system_prompts={"Issue Management": content}
        )
```

**同步后的 AGENTS.md 结构**：

```markdown
<!-- MONOCO_GENERATED_START -->
## Monoco Core

Core toolkit commands for project management...

## Issue Management (Agent Guidance)

System for managing tasks using `monoco issue`...

## Spike (Research)

Manage external reference repositories...
<!-- MONOCO_GENERATED_END -->

## 项目特定规则（用户自定义内容）

- 本项目的特殊约定
- 团队特定的流程
```

**关键设计点**：

1. **自动生成的内容包裹在标记中**：`MONOCO_GENERATED_START/END`，用户自定义内容写在外面
2. **增量更新**：`monoco sync` 只更新标记内的内容，保留用户的自定义规则
3. **多语言支持**：根据 `i18n.source_lang` 选择对应语言的 Resources
4. **Framework 感知**：自动检测 `.claude/`、`.gemini/` 等目录，将 Skills 分发到正确位置

### 2.3 Skills：能力包与可复用知识

Skills 解决**"Agent 如何获得特定领域能力"**的问题。

#### 2.3.1 Skill 的本质

Skill 是**可分发、可版本化、可组合**的能力单元：

```
Skill 结构

monoco_flow_issue_lifecycle_workflow/
├── SKILL.md          # 技能定义：触发条件、执行步骤、输出格式
├── prompts/
│   └── analyze.j2    # Prompt 模板
├── rules/
│   └── validation.md # 规则定义
└── examples/
    └── sample.md     # 示例输入输出
```

#### 2.3.2 Skill 的分类

| 类型 | 定义 | 示例 |
|------|------|------|
| **Flow Skill** | 标准化工作流 | Issue 生命周期、代码审查流程 |
| **Tool Skill** | 工具使用指南 | Git 高级操作、数据库迁移 |
| **Domain Skill** | 领域专业知识 | DDD 建模、安全编码规范 |
| **Integration Skill** | 第三方集成 | AWS 部署、Stripe 支付接入 |

#### 2.3.3 Skill 的分发与加载

```yaml
# .monoco/config.yaml
skills:
  # 内置 Skills（随 Monoco 分发）
  built_in:
    - monoco/issue-lifecycle
    - monoco/i18n-scan
  
  # 远程 Skills（从 Git 仓库加载）
  remote:
    - url: https://github.com/acme/ddd-skill
      version: v1.2.0
  
  # 本地 Skills（项目特定）
  local:
    - path: ./.monoco/skills/internal-workflow
```

### 2.4 Glossary：术语体系与概念一致性

Glossary 解决**"Agent 如何理解领域特定语言"**的问题。

#### 2.4.1 术语治理的必要性

在多 Agent 协作中，术语不一致是语义损耗的重要来源：

| 问题 | 示例 | 后果 |
|------|------|------|
| 同词异义 | "Module" 指代码模块还是业务模块？ | 架构设计偏差 |
| 异词同义 | "User" vs "Customer" vs "Client" | 数据模型混乱 |
| 概念缺失 | 没有统一术语描述"跨服务事务" | 每个 Agent 各自发明术语 |

#### 2.4.2 Glossary 的结构

```yaml
# Issues/Domains/Glossary.md 或 .monoco/glossary.yaml
terms:
  - name: Issue
    definition: 通用原子工作单元，具有独立生命周期
    aliases: [Ticket, Task, Work Item]
    domain: IssueTracing
    
  - name: Spike
    definition: 外部参考仓库的本地只读镜像
    aliases: [Reference, External Knowledge]
    domain: KnowledgeManagement
    
  - name: Guardrail
    definition: 保障 Agent 输出质量的自动化检查机制
    aliases: [Check, Validation, Gate]
    domain: QualityAssurance
```

#### 2.4.3 术语一致性检查

Linter 自动检测术语使用：

```python
# 伪代码：术语一致性检查
def validate_term_consistency(content: str) -> List[Diagnostic]:
    issues = []
    for term in glossary.terms:
        # 检查是否使用了非推荐的别名
        for alias in term.aliases:
            if alias in content:
                issues.append(Diagnostic(
                    message=f"术语建议：使用 '{term.name}' 替代 '{alias}'",
                    severity=Warning
                ))
    return issues
```

---

## 3. 组件间的协作关系

```
Agent Onboarding 数据流

┌─────────────────────────────────────────────────────────────────────┐
│                        知识摄入层                                   │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐ │
│  │   Spike     │─────────→│   Memo      │─────────→│   Issue     │ │
│  │  外部知识   │  引用    │  想法缓冲   │  转化    │  工作单元   │ │
│  └─────────────┘          └─────────────┘          └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        上下文构建层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │Context File │  │   Skills    │  │  Glossary   │  │   Domain    ││
│  │  环境规则   │  │   能力包    │  │   术语定义  │  │   领域模型  ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘│
│         │                │                │                │       │
│         └────────────────┴────────────────┴────────────────┘       │
│                              │                                      │
│                              ▼                                      │
│                    ┌───────────────────┐                           │
│                    │   Agent Session   │                           │
│                    │   初始化上下文    │                           │
│                    └───────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

**协作模式**：

1. **Spike → Issue**：在 Issue 中引用外部仓库的架构决策或代码模式
2. **Memo → Issue**：将临时想法转化为正式的工作单元
3. **Context File + Skills**：为 Agent 提供"工作环境 + 工具箱"
4. **Glossary + Domain**：确保所有 Agent 使用统一的语言描述业务概念

---

## 4. 实践指南：构建 Agent Onboarding 体系

### 4.1 初始化项目（Project Bootstrap）

```bash
# 1. 初始化 Monoco 项目（创建 .monoco/ 配置、Issues/ 目录、Git Hooks）
monoco init --name "MyProject" --key "MP" --author "Developer Name"

# 2. 同步 Agent 环境（生成 AGENTS.md、分发 Skills、复制 Roles）
monoco sync

# 3. 添加必要的 Spike 参考（外部知识库）
monoco spike add https://github.com/awesome-architecture/project-template
monoco spike add https://github.com/coding-standards/python-best-practices

# 4. 同步 Spike 到本地
monoco spike sync

# 5. 定义核心术语（可选）
monoco glossary add "Domain Event" "领域事件，表示业务中发生的有意义的事"

# 6. 验证配置
monoco config show
```

**初始化后的项目结构**：

```
my-project/
├── .monoco/                     # Monoco 配置
│   ├── project.yaml             # 项目身份（名称、Key）
│   ├── workspace.yaml           # 工作区配置（路径、Hooks）
│   └── roles/                   # Agent 角色模板
│       ├── engineer.yaml
│       ├── manager.yaml
│       └── reviewer.yaml
├── Issues/                      # Issue 追踪
│   ├── Epics/
│   ├── Features/
│   ├── Chores/
│   └── Fixes/
├── .references/                 # Spike 外部知识库
│   └── project-template/        # git clone 的只读仓库
├── AGENTS.md / GEMINI.md        # 由 monoco sync 生成
└── .git/hooks/                  # Git Hooks（由 init 安装）
    └── pre-commit
```

### 4.2 日常维护

```bash
# 同步 Agent 环境（更新 AGENTS.md、Skills、Roles）
# 在以下场景运行：
# - 升级 Monoco 版本后
# - 添加/移除 Features 后
# - 修改 i18n 配置后
monoco sync

# 检查同步状态（不实际修改文件）
monoco sync --check

# 同步特定目标文件
monoco sync --target CLAUDE.md

# 同步外部知识库
monoco spike sync

# 扫描术语一致性
monoco glossary lint

# 归档已处理的 Memo
monoco memo archive
```

**何时运行 `monoco sync`**：

| 场景 | 原因 |
|------|------|
| 升级 Monoco 后 | 获取最新版 Features 的 AGENTS.md 和 Skills |
| 新团队成员加入 | 确保其 Agent 环境配置正确 |
| 修改 `.monoco/config.yaml` 后 | 应用新的配置（如语言切换） |
| 添加新 Feature 后 | 注册并初始化新功能的 Resources |
| CI/CD 流水线中 | 确保构建环境的一致性 |

### 4.3 Agent 会话启动流程

当 Agent 开始工作时，系统通过 `monoco sync` 准备好的环境自动加载：

```
Agent 会话启动时的上下文加载流程

┌─────────────────────────────────────────────────────────────────────┐
│  阶段 1: 系统级配置（由 monoco init 创建）                           │
│  └── ~/.monoco/config.yaml                                          │
│      └── 作者信息、全局偏好、遥测设置                                │
├─────────────────────────────────────────────────────────────────────┤
│  阶段 2: 项目级配置（由 monoco init + sync 创建）                    │
│  ├── .monoco/project.yaml        # 项目身份                          │
│  ├── .monoco/workspace.yaml      # 工作区配置                        │
│  └── AGENTS.md / GEMINI.md       # 由 sync 聚合的 Feature Guides    │
│      └── <!-- MONOCO_GENERATED_START -->                            │
│          ├── Monoco Core                                          │
│          ├── Issue Management                                     │
│          ├── Spike                                                │
│          └── ...                                                  │
│      └── <!-- MONOCO_GENERATED_END -->                            │
├─────────────────────────────────────────────────────────────────────┤
│  阶段 3: 动态 Skills（由 monoco sync 分发）                          │
│  ├── .claude/skills/monoco_flow_*/         # Flow Skills            │
│  ├── .claude/skills/monoco_issue/          # Issue Skill            │
│  └── .claude/skills/monoco_spike/          # Spike Skill            │
├─────────────────────────────────────────────────────────────────────┤
│  阶段 4: 运行时上下文                                              │
│  ├── 当前工作目录的 AGENTS.md（如子目录有）                          │
│  ├── Glossary 术语定义（内存中加载）                                 │
│  └── Spike 仓库状态验证                                             │
└─────────────────────────────────────────────────────────────────────┘
```

**关键机制**：

1. **`monoco init`** 是一次性设置，创建项目骨架
2. **`monoco sync`** 是持续维护，更新动态内容（AGENTS.md、Skills）
3. **AGENTS.md 由机器生成**，用户不应手动编辑标记内的内容
4. **Skills 是只读的**，由 Monoco 统一管理版本

---

## 5. 与编排层的关系

Agent Onboarding 体系与三大编排子系统的关系：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent 编排层                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Agent Onboarding（知识基础设施）                │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │   │
│  │  │  Spike  │ │ Context │ │ Skills  │ │ Glossary│           │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Issue 追踪系统（状态管理）                      │   │
│  │  将知识转化为可执行的工作单元，追踪状态流转                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              护栏系统（质量保障）                            │   │
│  │  使用 Context File 作为规则，Skills 作为检查工具             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              演化系统（持续改进）                            │   │
│  │  通过 Memo 收集反馈，更新 Context File 和 Skills             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**关系说明**：

- **Onboarding 是前置条件**：没有良好的知识基础设施，Issue、Guardrail、Evolution 都无法有效运作
- **Onboarding 是输入源**：Spike 和 Memo 为演化系统提供输入；Context File 和 Skills 为护栏系统提供规则
- **Onboarding 本身也演化**：Glossary 和 Skills 会随着项目发展而更新，形成元层面的演化

---

## 6. 结语

Agent Onboarding 不是一次性配置，而是**持续运行的知识管理体系**。它回答了三个核心问题：

1. **Agent 从哪里获取知识？** → Spike（外部）+ Memo（内部沉淀）
2. **Agent 如何理解环境规则？** → Context File（层级配置）
3. **Agent 如何掌握特定能力？** → Skills（可分发能力包）
4. **Agent 如何与团队保持一致语言？** → Glossary（术语体系）

正如人类组织的知识管理是核心竞争力，Agent 系统的 Onboarding 体系决定了其**可扩展性、可维护性和最终产出质量**。

---

## 参考文献

1. Monoco Toolkit 项目实践
2. "The Checklist Manifesto" - Atul Gawande（关于标准化流程的价值）
3. "Domain-Driven Design" - Eric Evans（关于统一语言的重要性）
4. "Building Microservices" - Sam Newman（关于服务边界和上下文）
