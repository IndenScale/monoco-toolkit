# IssueSystem

## 定义

Monoco 的核心工作项管理系统，负责 Issue（Epic/Feature/Chore/Fix/Story/Arch）的全生命周期管理。它是项目的"单一真理源"，维护所有工作的状态、关系和治理规则。

## 职责

- **Identity Management**: Issue ID 分配、唯一性校验、命名规范
- **Lifecycle Management**: 状态流转（Open/Closed/Backlog）、阶段管理（Draft/Doing/Review/Done）
- **Relationship Management**: 父子关系、依赖关系、阻塞关系维护
- **Storage & Consensus**: Issue 文件持久化、Front Matter 管理、变更历史
- **Governance**: Lint 规则、规范校验、归档策略、质量门禁
- **Metrics & Reporting**: 解决率统计、Domain 覆盖率、工作量分析

## 边界

- **负责**: 所有与"工作项管理"相关的内容
- **不负责**: 工作如何被执行（AgentEmpowerment）、开发工具（DevEx）、基础层（Foundation）

## 原则

- **File-as-DB**: 文件系统即数据库，Markdown 即接口
- **Immutable History**: Issue 历史可追溯，变更留痕
- **Explicit Relationships**: 所有关系显式声明，拒绝隐式依赖
- **Governance by Default**: 默认启用规范检查，质量内建
