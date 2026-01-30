# Changelog

Generated on 2026-01-30

## [v0.3.9] - 2026-01-30

### Flow Skills 架构升级

- **FEAT-0121**: Define Standard Agent Workflows via Flow Skills
  - 为 Engineer、Manager、Reviewer 角色定义标准化 Flow Skills
  - 使用 Mermaid 状态机定义工作流程
  - 支持 Kimi CLI `/flow:*` 命令

- **FEAT-0122**: Enhance SkillManager to Support Multi-Skill Architecture
  - 重构 SkillManager 支持 1 Feature : N Skills 架构
  - 统一标准 Skill 和 Flow Skill 注入机制
  - 支持 `type: flow` 和 `role` 元数据字段

- **FEAT-0123**: Migrate Core Features to Flow Skills Pattern
  - i18n: `i18n_scan_workflow` - 扫描 → 识别 → 生成任务
  - Spike: `research_workflow` - 添加 → 同步 → 分析 → 提取 → 归档
  - Issue: `issue_lifecycle_workflow` - Open → Start → Develop → Submit → Review → Close
  - Memo: `note_processing_workflow` - Capture → Process → Organize → Archive/Convert

### Agent 架构优化

- **CHORE-0023**: Rename scheduler module to agent
  - `monoco/features/scheduler/` → `monoco/features/agent/`
  - `SchedulerConfig` → `AgentConfig`（保留向后兼容别名）
  - 与 CLI 命令 `monoco agent` 保持一致

- **FEAT-0120**: Implement Agent Session Lifecycle Hooks
  - 实现 Session 生命周期钩子机制
  - 内置 `GitCleanupHook` 自动清理分支
  - 内置 `LoggingHook` 记录 Session 事件

### 双模式 Skill 架构

- 传统 Skills: Command Reference（命令参考、配置说明）
- Flow Skills: SOP 工作流（状态机、检查点、合规要求）
- 两者互补，服务不同场景

## [v0.3.2] - Recent Releases

### FEAT-0095: 文档内容与 CLI 参考

- _Result_: Implemented - Core documentation pages (Manifesto, CLI Reference, Landing Page) populated and verified.

### FEAT-0094: 内容管道与国际化策略

- _Result_: implemented

### FEAT-0093: 站点基础设施与设计系统

- _Result_: implemented

### FEAT-0092: Governance Maturity Checks

- _Result_: Implemented

### FEAT-0091: 实现 Git Hooks 机制

- _Result_: implemented

### FEAT-0090: VSCode Extension 组件化模块化重构

- _Result_: Core refactoring (Phase 1-4) completed. Webview and LSP are now modular

### FEAT-0088: 可配置 Issue Schema 加载器 (YAML 配置)

- _Result_: implemented

### FEAT-0087: 动态状态机引擎 (数据驱动逻辑)

- _Result_: implemented

### FEAT-0086: DDD Issue 建模 (影子对象层)

- _Result_: implemented

### FEAT-0085: 更新 VS Code 扩展以支持优化的动作系统

- _Result_: Cancelled - Agent functionality removed from VS Code extension.

### FEAT-0084: 优化 Issue 生命周期动作与 Agent 集成

- _Result_: Cancelled - Agent functionality removed from Monoco core.

### FEAT-0083: Integration of Monoco CLI as LSP Backend

- _Result_: implemented

### FEAT-0082: Issue Ticket Validator

- _Result_: implemented

### FEAT-0081: Prompty Action System: Context-Aware Agent Skills

- _Result_: implemented

### FEAT-0080: VS Code Execution UI: Sidebar & CodeLens

- _Result_: implemented

### FEAT-0079: VS Code 扩展与 Agent 状态的集成

- _Result_: implemented

### FEAT-0078: Agent 执行层与 CLI 集成

- _Result_: implemented

### FEAT-0077: Migrate Cockpit View to Pure LSP Architecture

- _Result_: Implemented Pure LSP architecture, removing Python dependency for the Kanban

### FEAT-0076: Implement Monoco Language Server

- _Result_: Implemented a dual-project structure (client/server) within `extensions/vscode`.

### FEAT-0075: VS Code Extension Realignment: Implementation of Proxy Pattern

- _Result_: implemented

### FEAT-0074: Core Integration Registry

- _Result_: implemented

### FEAT-0073: Implement Skill Manager and Distribution

- _Result_: implemented

### FEAT-0072: Core Agent Environment Manager (Sync & Uninstall)

- _Result_: implemented

### FEAT-0071: Implement Monoco Sync and Prompt Injection System

- _Result_: implemented

### FEAT-0070: 实现标准化的 monoco config 命令

- _Result_: implemented

### FEAT-0069: Spike 内容清洗与元数据增强

- _Result_: cancelled

### FEAT-0067: 执行配置与提示词管理

- _Result_: implemented

### FEAT-0066: 智能体运行时诊断 (Agent Runtime Diagnostics)

- _Result_: implemented

### FEAT-0065: 智能体运行时配置 (Agent Runtime Configuration)

- _Result_: implemented

### FEAT-0064: 智能父级选择

- _Result_: implemented

### FEAT-0063: 优化 VS Code 扩展 UI

- _Result_: implemented

### FEAT-0062: Drag-and-Drop Workflow via Text/URL

- _Result_: Implemented

### FEAT-0061: Cockpit Navigation Bridge (Webview to Editor)

- _Result_: Implemented

### FEAT-0059: VS Code Extension Scaffold & Webview Bridge

- _Result_: implemented

### FEAT-0058: Kanban 分发 - npm

- _Result_: implemented

### FEAT-0057: 看板终端集成 (xterm.js)

- _Result_: implemented

### FEAT-0056: Implement monoco-pty Service via WebSockets

- _Result_: implemented

### FEAT-0052: Kanban 分发 - NPM/NPX

- _Result_: implemented

### FEAT-0051: CLI 工具分发 - PyPI

- _Result_: implemented

### FEAT-0050: 一键安装脚本

- _Result_: implemented

### FEAT-0049: 安全清理

- _Result_: implemented

### FEAT-0048: 工具包自述文件完善

- _Result_: implemented

### FEAT-0047: 社区健康文件

- _Result_: implemented

### FEAT-0046: GitHub Page 维护

- _Result_: implemented

### FEAT-0043: Toolkit 分发渠道建设

- _Result_: Implemented

### FEAT-0038: Workspace 内跨项目引用互操作性

- _Result_: implemented

### FEAT-0037: CLI Advanced Issue Query

- _Result_: implemented

### FEAT-0036: Advanced Kanban Filter

- _Result_: implemented

### FEAT-0034: UI术语可配置化

- _Result_: implemented

### FEAT-0033: 交互式状态流转与合法性校验

- _Result_: implemented

### FEAT-0032: 可选分支隔离 (Optional Branch Isolation)

- _Result_: implemented

### FEAT-0031: 状态递归聚合 (Recursive State Aggregation)

- _Result_: implemented

### FEAT-0030: 提交溯源与扫描器 (Commit Traceability & Scanner)

- _Result_: implemented

### FEAT-0029: Web 看板实现 (Web Kanban Implementation)

- _Result_: implemented

### FEAT-0020: 工程视图 (Engineering View)

- _Result_: implemented

### FEAT-0019: 全局仪表盘 (Global Dashboard)

- _Result_: implemented

### FEAT-0016: 安全 Issue 编辑 (Safe Issue Editing)

- _Result_: implemented

### FEAT-0015: 看板 UI 增强 (Kanban UI Enhancements)

- _Result_: implemented

### FEAT-0014: 实现 Issue 管理 API (Implement Issue API)

- _Result_: implemented

### FEAT-0013: 实现 monoco issue list 命令 (Implement List Command)

- _Result_: implemented

### FEAT-0012: 增强 CLI 与 Server 的多工作区支持 (Enhance Workspace Support)

- _Result_: implemented

### FEAT-0011: 增强 i18n 报告功能: 支持缺失文档清单输出 (Enhance i18n Reporting)

- _Result_: implemented

### FEAT-0010: 增强 Init 命令 (Enhanced Init Command)

- _Result_: implemented

### FEAT-0009: 建立 Spike 系统使用文档体系 (Establish Spike Docs)

- _Result_: implemented

### FEAT-0008: 建立 Issue 系统使用文档体系 (Establish Issue Docs)

- _Result_: implemented

### FEAT-0007: 支持外部或子项目 Issue 根目录 (Support External Issue Roots)

- _Result_: implemented

### FEAT-0006: 支持层级 Issue 组织 (Support Hierarchical Issue Organization)

- _Result_: implemented

### FEAT-0005: 实现 i18n 扫描能力 (Implement i18n scan)

- _Result_: implemented

### FEAT-0004: 特性: 仓库管理 (Spike) (Repo Management - Spike)

- _Result_: implemented

### FEAT-0003: 特性: Issue 管理 (本地) (Issue Management - Local)

- _Result_: implemented

### FEAT-0002: Toolkit 核心基础设施 (Toolkit Core Infrastructure)

- _Result_: implemented

### FEAT-0001: 重构 Issue 术语为原生代理语义 (Refactor Issue Terminology)

- _Result_: implemented
