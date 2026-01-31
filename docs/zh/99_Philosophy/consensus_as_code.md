# 共识即代码：Monoco 的核心精神

## 摘要

Monoco Toolkit 与 Typedown 的表面形态是各种工具与协议的集合，但其灵魂只有一个核心认知：**共识即代码 (Consensus as Code)**。我们认为，在 Agent 驱动的复杂系统中，唯一的生存之道是实现**文档与系统的同一性 (The Identity of Document and System)**。所有的隐性知识必须显性化为可验证的代码，所有的中间层（App, DB, UI）都将消融，最终只剩下语义的载体（文本）与共识的铁律（代码）。

---

## 1. 核心定义：文档与系统的同一性

传统的软件工程是一种**分裂**的实践：

- **文档**描述了"系统应该是什么样"（Word, PDF）。
- **代码**实现了"系统实际上是什么样"（Java, Python）。
- **数据库**存储了"系统的当前状态"（Binary Data）。

这种分裂导致了熵增。文档腐烂，代码偏离，数据变成黑盒。

Monoco 提出的 **Literate System（文学化系统）** 试图消除这种分裂：

> **你不需要离开文档去定义系统；文档本身就是系统。**

在这个世界观下：

- 需求文档不仅仅是给人看的，它包含了 **Schema (Pydantic)** 和 **Test (Pytest)**。
- Agent 修改的不仅仅是文本文件，它直接修改了**系统状态**。
- 文档的验证（Linting/Testing）就是系统的**运行时逻辑**。

这就是 **共识即代码**。

---

## 2. 四大投影：核心思想的具象化

我们所做的每一个技术决策（Typedown, FS, Oracle, IDE），都只是这个核心灵魂向不同维度的**投影 (Projection)**。

### 2.1 载体的显性化 (Typedown 取代 Binary)

_解决"知识黑盒"问题_

- **旧世界**：AutoCAD 的 `.dwg` 文件、Excel 的 `.xlsx` 文件。数据被封锁在二进制格式中，只有特定的 App 才能解读。共识（"这根柱子必须承重"）藏在设计师的大脑里。
- **Monoco 世界**：
  - **Typedown (Markdown + Schema)**：数据回归为纯文本。
  - **Pydantic**：结构被显式定义。`class Column(BaseModel): load_bearing: bool`。
  - **逻辑**：Agent 和人一样，通过阅读文本理解世界，而非调用 API。
- **本质**：**如果共识不能被文本化阅读，它就不存在。**

### 2.2 物理的显性化 (FS 吞噬 Database)

_解决"状态不可见"问题_

- **旧世界**：状态存储在远端的 RDBMS 中。它是不可见的、易变的、无上下文的。你必须通过 App 的特定窗口才能窥视其一角。
- **Monoco 世界**：
  - **FS First**：状态物理地驻留在用户本地的文件系统中。
  - **Git Backed**：每一次状态变更都是一次 Commit，都有 Author 和 Message。
  - **透明性**：不需要 SQL，`ls` 和 `grep` 就是查询语言。
- **本质**：**如果状态不能被直接观测（File），我们就无法信任它。**

### 2.3 执行的显性化 (Oracle 取代 Backend Logic)

_解决"规则隐性化"问题_

- **旧世界**：业务规则硬编码在 Backend Service 的深处。逻辑是隐性的，只有触发报错时才知道违反了规则。
- **Monoco 世界**：
  - **Guardrails**：业务规则外置为独立的**司法体系**。
  - **Oracle**：Linter、Reviewer、Test Runner 像法律一样公开并独立运行。
  - **Typedown Spec**：规则直接写在文档里。`def check_policy(doc): assert doc.status != 'draft'`。
- **本质**：**如果不变量（Invariants）不能被独立验证，它就不是法律。**

### 2.4 交互的显性化 (IDE 吞噬 UI)

_解决"协议割裂"问题_

- **旧世界**：为了限制用户输入，我们开发了复杂的 GUI 表单。App 变成了功能的孤岛。
- **Monoco 世界**：
  - **IDE as Interface**：所有的交互收敛至编辑器。
  - **LSP at Runtime**：输入限制变成了实时的红色波浪线。反馈在输入的那一毫秒发生，而不是点击"提交"之后。
- **本质**：**交互不是为了通过"界面"填空，而是为了达成"协议"的一致。**

---

## 3. 终极图景：无限心智的宪法

Ivan Zhao 的文章《Steam, Steel, and Infinite Minds》描绘了一个宏大的经济愿景：未来的组织是拥有千万 Agent 的"东京"（Megacity）。

但 Ivan 没有回答的问题是：**谁来维持"东京"的秩序？**

如果依靠传统的 Database 和 App，这座城市会在瞬间陷入混乱。Agent 会互相覆盖数据，逻辑会在黑盒中冲突，熵增会摧毁一切。

Monoco 就是这座无限城市的**宪法 (Constitution)**。

我们不负责建造摩天大楼（那是 Agent 的工作），我们负责制定**物理法则**：

1.  **文本即物质**：万物皆文本。
2.  **Git 即时间**：历史不可篡改。
3.  **CI 即因果**：无验证不生效。

Monoco 的使命，是 **Make Consensus Executable (让共识可执行)**。我们为即将到来的"无限心智"时代，构建那个最底层的、不可动摇的**法治基石**。
