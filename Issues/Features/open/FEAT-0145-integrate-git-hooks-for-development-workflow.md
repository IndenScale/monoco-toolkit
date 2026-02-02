---
id: FEAT-0145
uid: 6d6bf7
type: feature
status: open
stage: draft
title: 集成 Git Hooks 到开发工作流
created_at: '2026-02-01T20:57:03'
updated_at: '2026-02-02T13:25:35'
parent: EPIC-0030
dependencies: []
related:
- FEAT-0141
domains: []
tags:
- '#EPIC-0030'
- '#FEAT-0145'
- '#FEAT-0141'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Epics/open/EPIC-0030-developer-experience-tooling.md
- Issues/Features/open/FEAT-0145-integrate-git-hooks-for-development-workflow.md
criticality: medium
opened_at: '2026-02-02T13:25:35'
isolation:
  type: direct
  ref: current
---

## FEAT-0145: 集成 Git Hooks 到开发工作流

## 背景与目标

将 Git Hooks（pre-commit, pre-push）集成到 Monoco 工作流中，确保数据完整性和流程合规。

**上下文**:
- **问题**: Issue 缺失必要字段（如已关闭 Issue 的 `solution` 字段）可能会破坏索引器或依赖关系。手动修复容易出错。
- **解决方案**: 使用 `pre-commit` 钩子运行 `monoco issue lint` 并拦截不合规的提交。

## 架构设计决策

### 方案选择：分布式 Hooks + 聚合器模式

经过讨论，采用**分布式 Hooks + 聚合器**架构：

1. **分布式**：每个 Feature 在 `resources/hooks/` 存放自己的 hook 脚本
   - 高内聚：i18n 的 hook 逻辑在 i18n feature 中
   - 可插拔：禁用 Feature 自动禁用其 hooks
   - 可扩展：新增 Feature 自动携带 hooks

2. **聚合器**：`features/hooks/` 负责收集、排序、生成最终 hook
   - 遍历所有 Feature 发现 hooks
   - 按 priority 排序，串联执行
   - 写入 `.git/hooks/`

### 目录结构

```
monoco/features/
├── hooks/                          # Hooks 聚合器 Feature
│   ├── commands.py                 # monoco hooks install/uninstall/status
│   ├── core.py                     # GitHooksManager - 聚合所有 hooks
│   ├── adapter.py
│   └── resources/
│       └── templates/
│           └── base.sh             # 基础 hook 模板（可选）
│
├── issue/
│   └── resources/
│       └── hooks/                  # Issue 相关的 hooks
│           └── pre-commit.sh       # Issue lint 检查
│
└── i18n/                           # 其他 Feature 示例
    └── resources/
        └── hooks/
            └── pre-commit.sh       # 翻译完整性检查
```

### Hook 发现机制

- **约定目录**：`features/{feature}/resources/hooks/{hook-type}.sh`
- **执行顺序**：按 Feature priority 排序，默认字母序
- **生成策略**：串联执行，任一失败则终止

### 为什么不使用 pre-commit 框架

1. **API 限制**：pre-commit 官方明确拒绝提供 Python API，只能通过 subprocess 调用
2. **配置分离**：pre-commit 使用独立的 YAML 配置，与 Monoco 统一配置理念冲突
3. **过度设计**：Monoco 只需要简单的 `pre-commit` hook，pre-commit 的多语言支持是过度设计

## 验收标准

- [ ] `monoco hooks install` 命令安装 git hooks 到 `.git/hooks/`
- [ ] `monoco hooks uninstall` 命令移除已安装的 hooks
- [ ] `monoco hooks status` 命令显示 hooks 安装状态和配置
- [ ] `pre-commit` hook 收集所有 Feature 的 pre-commit 脚本并串联执行
- [ ] Issue Feature 提供 `resources/hooks/pre-commit.sh` 运行 `monoco issue lint`
- [ ] 支持按 Feature 启用/禁用 hooks（通过 `workspace.yaml` 配置）
- [ ] `pre-push` 钩子检查未完成的关键 Issue（可选/可配置）。

## 技术任务

### Phase 1: Hooks 聚合器基础设施
- [ ] 创建 `monoco/features/hooks/` Feature 模块
- [ ] 设计 `HookDeclaration` 元数据类（type, script_path, priority）
- [ ] 实现 `GitHooksManager.collect_hooks(hook_type)` 发现机制
- [ ] 实现 Hook 串联生成逻辑（生成可执行的 shell 脚本）
- [ ] 实现虚拟环境自动检测（确保 hook 中调用正确的 Python 环境）
- [ ] 创建 `monoco hooks` 子命令（install/uninstall/status）

### Phase 2: Issue Feature Hooks
- [ ] Issue Feature: 创建 `resources/hooks/pre-commit.sh`
- [ ] 实现 staged Issue 文件检测（只检查变更产生影响的 Issue）
- [ ] 集成 `monoco issue lint` 命令

### Phase 3: 配置与扩展
- [ ] 添加 Feature-level hooks 启用/禁用配置到 `workspace.yaml`
- [ ] 支持 hooks 优先级自定义
- [ ] 文档：如何为 Feature 添加自定义 hook
- [ ] 实现 `pre-push` hook：检查关键 Issue 状态（可选配置）
- [ ] 实现 `post-checkout` hook：自动同步 Issue 状态（可选）

## 超出范围 (Out of Scope)

- **pre-commit 框架集成**：自建方案已满足需求，避免外部依赖

## Review Comments

### 2026-02-02 架构讨论更新

**设计变更**:
- 从集中式 `monoco/assets/hooks` 改为**分布式** `features/{feature}/resources/hooks/`
- 新增 `features/hooks/` 作为聚合器，负责收集和生成最终 hook
- 移除 `pre-push` 和 `post-checkout` 任务，聚焦核心需求（注：后续根据 Phase 3 决定是否部分实现）
- 明确不使用 pre-commit 框架，采用直接写入 `.git/hooks/` 方案

**架构优势**:
- 高内聚：每个 Feature 拥有自己的 hooks，职责清晰
- 可插拔：禁用 Feature 自动禁用其 hooks
- 可扩展：新增 Feature 自动携带 hooks，无需修改 hooks feature
- 与 Monoco Feature 架构完美契合

### 2026-02-02 整合更新

**变更**:
- Parent 从 EPIC-0025 调整为 EPIC-0030 (DevEx & Infrastructure)
- 整合了 FEAT-0141 的技术任务（模板目录、pre-push/post-checkout hooks）
- FEAT-0141 已标记为 duplicate 并关闭

**归属理由**: Git Hooks 属于开发者体验基础设施，与 EPIC-0030 的 "Code Quality Infrastructure" 和 "Local Development Environment" 目标一致。