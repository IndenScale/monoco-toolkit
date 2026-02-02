---
id: FEAT-0141
uid: cc4930
type: feature
status: closed
stage: done
solution: cancelled
title: Native Git Hooks Management Integration
created_at: '2026-02-01T20:53:07'
updated_at: '2026-02-01T20:53:07'
parent: EPIC-0000
dependencies: []
related:
- FEAT-0145
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0030'
- '#FEAT-0141'
- '#FEAT-0145'
files: []
criticality: medium
opened_at: '2026-02-01T20:53:07'
---

## FEAT-0141: Native Git Hooks Management Integration

## Objective
集成 Monoco Native Git Hooks 管理功能，通过 `monoco sync --hooks` 统一安装和管理 Git Hooks，确保开发规范（Issue 格式、代码质量）在提交阶段被强制执行。

## Acceptance Criteria
- [x] `monoco sync` 命令支持 `--hooks` 选项，用于安装/更新 `.git/hooks` (已整合到 FEAT-0145)
- [x] 实现 `pre-commit` hook：运行 `monoco issue lint` (已整合到 FEAT-0145)
- [x] 实现 `pre-push` hook：检查关键 Issue 状态（可选）(已整合到 FEAT-0145)
- [x] 实现 `post-checkout` hook：自动同步 Issue 状态（可选）(已整合到 FEAT-0145)
- [x] 支持 Hooks 模板自定义 (已整合到 FEAT-0145)

## Technical Tasks
- [x] 扩展 `monoco sync` 命令处理逻辑 (已整合到 FEAT-0145)
- [x] 设计 Hooks 模板存放目录 (`monoco/core/githooks/templates/`) (已整合到 FEAT-0145)
- [x] 实现 Hooks 安装/链接逻辑 (已整合到 FEAT-0145)
- [x] 编写默认的 `pre-commit` 脚本模板 (已整合到 FEAT-0145)

## Review Comments

### 2026-02-02 整合结论

**决定**: 此 Issue 与 FEAT-0145 重复，标记为 cancelled 并关闭。

**理由**:
- FEAT-0145 描述更详细，且已包含本 Issue 的所有验收标准
- 合并后统一归属到 EPIC-0030 (DevEx)
- 技术任务已整合到 FEAT-0145

**后续行动**: 所有开发工作将在 FEAT-0145 中跟踪。