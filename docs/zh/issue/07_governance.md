# 治理成熟度 (Governance Maturity)

Monoco 采用**渐进式治理 (Progressive Governance)** 策略。我们不主张在一开始就引入厚重的规范，而是根据项目规模（Issues 总数、Epics 数量）自动从轻量模式切换到严格治理模式。

## 1. 成熟度等级

| 等级                    | 适用阶段        | 核心要求                         | 治理手段            |
| :---------------------- | :-------------- | :------------------------------- | :------------------ |
| **L1: 草稿 (Draft)**    | 个人项目 / 原型 | 仅需 `id`, `title`               | 语义解析            |
| **L2: 标准 (Standard)** | 团队协作        | 包含 AC、Tasks、阶段约束         | `monoco issue lint` |
| **L3: 治理 (Mature)**   | 企业级 / 大规模 | 分域治理 (`domains`)、国际化同步 | 强制性 Linter 检查  |

## 2. 自动升级机制

Monoco 的 Linter 会根据项目活跃度自动识别成熟期：

- **触发条件**: 当项目 `Issues > 50` 或 `Epics > 8` 时。
- **强制要求**:
  - **Domains**: Frontmatter 必须包含 `domains` 字段，以实现领域隔离和跨项目引用。
  - **Language**: 文档语言必须与项目定义的源语言一致。
  - **Checksum**: (计划中) 关键决策的修改需经过散列验证。

## 3. 约束规则

### 3.1 状态一致性

处于 `status: closed` 的 Issue 必须处于 `stage: done`，且：

- 所有 `Acceptance Criteria` 必须为已完成 (`[x]`)。
- 所有 `Technical Tasks` 必须已解决。
- 必须存在 `solution` 描述。

### 3.2 标签链路

每个 Issue 的 `tags` 字段必须包含其父级 ID、依赖项 ID 以及自身 ID。这为 Agent 提供了无死角的知识检索能力。

---

[上一章: 06. 查询语法](./06_query_syntax.md) | **下一章**: [没有了]
