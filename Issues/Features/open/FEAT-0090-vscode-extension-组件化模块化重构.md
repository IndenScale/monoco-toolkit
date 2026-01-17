---
id: FEAT-0090
uid: cca9d1
type: feature
status: open
stage: in_progress
title: VSCode Extension 组件化模块化重构
created_at: "2026-01-17T12:42:08"
opened_at: "2026-01-17T12:42:08"
updated_at: "2026-01-17T12:53:06"
dependencies: []
related: []
tags: [refactoring, vscode, architecture]
# parent: <EPIC-ID>   # Optional: Parent Issue ID
# solution: null      # Required for Closed state (implemented, cancelled, etc.)
---

## FEAT-0090: VSCode Extension 组件化模块化重构

## Objective

将 VSCode Extension 从单体架构重构为模块化、可测试、可维护的架构。

**Why**:

- 当前代码存在严重的坏味道（God Class、代码重复、职责混乱）
- 难以测试和维护
- 缺乏清晰的模块边界

**What**:

- 建立共享类型系统
- 拆分大文件为小模块
- 消除代码重复
- 提升测试覆盖率

**Value**:

- 降低 60% 的代码复杂度
- 提升可维护性和可扩展性
- 支持单元测试和集成测试

## Acceptance Criteria

- [x] Phase 1: 基础设施完成（共享模块、类型定义）
- [x] Phase 2: Extension.ts 拆分完成（204 LOC，目标 < 100 LOC 部分达成）
- [ ] Phase 3: Webview 重构完成（TypeScript 迁移、组件化）
- [ ] Phase 4: LSP Server 重构完成（纯协议层）
- [ ] Phase 5: 测试覆盖率 > 80%
- [ ] 无功能回归
- [x] 编译无错误
- [ ] 文档更新完成

## Technical Tasks

### Phase 1: 基础设施 ✅ (2026-01-17 完成)

- [x] 创建共享模块目录结构
  - [x] `shared/types/` - 类型定义
  - [x] `shared/constants/` - 常量定义
  - [x] `shared/utils/` - 工具函数
- [x] 定义核心类型
  - [x] Issue.ts - Issue 相关类型
  - [x] Project.ts - Project 相关类型
  - [x] Config.ts - 配置类型
  - [x] Message.ts - 消息类型
- [x] 定义常量
  - [x] ViewTypes.ts - 视图类型
  - [x] MessageTypes.ts - 消息类型
  - [x] CommandIds.ts - 命令 ID
- [x] 提取可执行文件解析逻辑
  - [x] MonocoExecutableResolver.ts
  - [x] 消除 bootstrap.ts 和 server.ts 的重复代码
- [x] 配置 TypeScript
  - [x] shared/tsconfig.json
  - [x] 更新 client/tsconfig.json
  - [x] 更新 server/tsconfig.json
  - [x] 更新编译脚本
- [x] 验证编译成功

**成果**:

- 新增 12 个文件，~280 LOC
- 消除 114 LOC 重复代码
- 详见 `PHASE1_REPORT.md`

### Phase 2: 拆分 Extension.ts ✅ (2026-01-17 完成)

- [x] 提取命令注册
  - [x] BaseCommandRegistry.ts
  - [x] CommandRegistry.ts
  - [x] IssueCommands.ts
  - [x] ActionCommands.ts
  - [x] SettingsCommands.ts
- [x] 提取 Provider 注册
  - [x] ProviderRegistry.ts
  - [x] 更新现有 Provider 使用共享类型
- [x] 提取 LSP 客户端管理
  - [x] LanguageClientManager.ts
- [x] 提取 Webview Provider
  - [x] KanbanProvider.ts
- [x] 重构 extension.ts
  - [x] 从 747 LOC 减少到 204 LOC (-73%)
  - [ ] 进一步优化到 < 100 LOC (可选)
- [x] 更新 bootstrap.ts
  - [x] 使用共享的 MonocoExecutableResolver
  - [x] 从 181 LOC 减少到 ~130 LOC (-28%)

**成果**:

- 新增 8 个文件，~752 LOC
- extension.ts: 747 → 204 LOC (-73%)
- bootstrap.ts: 181 → 130 LOC (-28%)
- 详见 `PHASE2_REPORT.md`

### Phase 3: 重构 Webview (预计 1 周)

- [ ] 迁移到 TypeScript
  - [ ] main.js -> main.ts
- [ ] 提取状态管理
  - [ ] StateManager.ts
- [ ] 提取组件
  - [ ] IssueTree.ts
  - [ ] ProjectSelector.ts
  - [ ] CreateForm.ts
- [ ] 提取消息处理
  - [ ] VSCodeBridge.ts

### Phase 4: 重构 LSP Server (预计 1 周)

- [ ] 提取 Provider
  - [ ] DefinitionProvider.ts
  - [ ] CompletionProvider.ts
  - [ ] DiagnosticProvider.ts
- [ ] 提取工作区索引
  - [ ] WorkspaceIndexer.ts
- [ ] 重构 server.ts
  - [ ] 目标: < 300 LOC
  - [ ] 纯协议层

### Phase 5: 测试覆盖 (预计 1 周)

- [ ] 单元测试
  - [ ] MonocoExecutableResolver.test.ts
  - [ ] CommandRegistry.test.ts
  - [ ] ProviderRegistry.test.ts
  - [ ] ActionService.test.ts
  - [ ] WorkspaceIndexer.test.ts
- [ ] 集成测试
  - [ ] lsp.test.ts
- [ ] E2E 测试
  - [ ] kanban.test.ts
- [ ] 测试覆盖率 > 80%

## Review Comments

### Phase 1 Review (2026-01-17)

✅ **完成情况**:

- 所有计划任务完成
- 编译测试通过
- 类型系统建立完成

📝 **经验总结**:

- TypeScript 路径别名配置需要注意 rootDir 冲突
- 共享模块的输出目录选择影响打包流程
- 类型定义的完整性对后续重构至关重要

🎯 **下一步**:

- 开始 Phase 2: 拆分 Extension.ts
- 优先提取命令注册逻辑

### Phase 2 Review (2026-01-17)

✅ **完成情况**:

- 所有计划任务完成
- extension.ts 从 747 LOC 减少到 204 LOC (-73%)
- bootstrap.ts 从 181 LOC 减少到 ~130 LOC (-28%)
- 新增 8 个模块化文件
- 编译测试通过

📝 **经验总结**:

- 依赖注入设计显著提升了代码可测试性
- 每个消息类型一个方法的模式大幅提升可维护性
- 命令注册的分类管理使代码更清晰
- 共享模块的使用消除了大量重复代码

🎯 **下一步**:

- 开始 Phase 3: 重构 Webview
- 优先迁移 main.js 到 TypeScript

💡 **改进建议**:

- extension.ts 可进一步优化到 < 100 LOC
- 可以提取 `runMonoco` 到 `utils/CLIExecutor.ts`
- 可以提取 `checkDependencies` 到 `services/DependencyChecker.ts`
