---
id: FEAT-0135
uid: 47e994
type: feature
status: open
stage: review
title: Implement Issue Archival Strategy and Lint Support
created_at: '2026-02-01T09:37:27'
updated_at: '2026-02-01T09:42:32'
priority: medium
parent: EPIC-0026
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0026'
- '#FEAT-0135'
- cli
- issue-governance
- performance
files: []
criticality: medium
opened_at: '2026-02-01T09:37:27'
owner: IndenScale
---

## FEAT-0135: Implement Issue Archival Strategy and Lint Support

## FEAT-0135: 实现 Issue 归档策略与 Lint 支持

### 背景

随着项目迭代，`Issues/Features/closed` 目录下的文件数量不断增加。这导致：
1. **性能问题**: `monoco issue list` 和 VS Code Extension 在加载时需要扫描大量不相关的历史文件。
2. **认知负载**: 开发者在浏览文件系统时面对大量噪音。
3. **Lint 限制**: 目前的 Linter 可能对目录结构有严格限制（仅允许 `open`, `closed`, `backlog`），无法简单移动文件。

### 目标

引入 `archived` 状态和对应的目录结构，并更新工具链（CLI & Linter）以支持这一变更。

### 功能需求

#### 1. 目录结构变更
允许在 Issue 类型目录下存在 `archived` 目录。
结构示例：
```text
Issues/
  ├── Features/
  │   ├── open/
  │   ├── closed/     <-- 最近关闭 (e.g., 本月/本季度)
  │   ├── backlog/
  │   └── archived/   <-- 历史遗迹 (不会被默认加载)
          ├── 2025/
          └── ...
```

#### 2. Linter (Validator) 增强
- 修改 `IssueLinter` 或 `LayoutValidator`。
- 将 `archived` 及其子目录标记为 **合法** 路径。
- 确保 `closed` 与 `archived` 之间的流转被视为合法（或至少不报错）。

#### 3. Scanner / Resolver 变更
- **默认行为**: `IssueManager` 或 `FileScanner` 在扫描 Issue 时，**默认跳过** `archived` 目录。
- **Flag 支持**: 为 CLI 命令（如 `list`, `stats`）添加 `--all` 或 `--include-archived` 参数，当指定时才扫描归档目录。

#### 4. VS Code Extension 适配
- 确保 Extension 不会因为扫描数千个归档文件而卡顿。
- (可选) 提供一个 "Load Archive" 的开关或命令。

### 检查清单

- [x] **Specs**: 定义归档目录的命名规范（是否按年份/月份分层？本次暂定允许 `archived/**`）。
- [x] **CLI/Core**: 修改 `monoco/features/issue/core.py`，默认过滤 `archived`。
- [x] **CLI/Lint**: 修改 `monoco/features/issue/linter.py`，允许 `archived` 目录存在。
- [x] **CLI/Args**: 为 `monoco issue list` 添加 `--all` 参数支持。
- [x] **Migration**: 手动创建一个 `archived` 目录并移动部分旧 Issue 进行测试。

## Review Comments

### 实现总结

1. **目录结构**: 在 `Issues/{Type}/` 下新增 `archived/` 目录，支持按年份/月份分层（如 `archived/2025/`）。

2. **Core 模块修改** (`monoco/features/issue/core.py`):
   - `list_issues()`: 新增 `include_archived` 参数，默认 `False`
   - `find_next_id()`: 新增 `include_archived` 参数
   - `find_issue_path()`: 新增 `include_archived` 参数，默认 `True`（查找操作需要搜索归档）
   - `search_issues()`: 新增 `include_archived` 参数

3. **Linter 模块修改** (`monoco/features/issue/linter.py`):
   - `collect_project_issues()`: 新增 `include_archived` 参数，支持扫描归档目录

4. **Commands 模块修改** (`monoco/features/issue/commands.py`):
   - `list` 命令新增 `--all` / `-a` 参数，用于包含归档 Issue

5. **测试验证**:
   - 所有 92 个 Issue 相关测试通过
   - 手动验证 `monoco issue list --all` 可以显示归档目录中的 Issue
   - 默认情况下 `archived` 目录被正确跳过
