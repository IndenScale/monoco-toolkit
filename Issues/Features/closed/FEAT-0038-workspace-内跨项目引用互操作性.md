---
id: FEAT-0038
uid: a1b2c3
type: feature
status: closed
stage: done
title: Workspace 内跨项目引用互操作性
created_at: '2026-01-13T10:36:19'
opened_at: '2026-01-13T12:25:00'
updated_at: '2026-01-13T12:43:34'
closed_at: '2026-01-13T12:43:34'
parent: EPIC-0001
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0001'
- '#FEAT-0038'
---

## FEAT-0038: Workspace 内跨项目引用互操作性

## Objective

实现 Workspace 内跨项目引用的完整互操作性，确保 Issue 在不同项目间移动、引用时的 Identity (UID) 稳定，并支持基于命名空间的 Display ID (Handle) 自动对齐。

## Acceptance Criteria

- [x] **Project Namespace Support**:
  - `monoco.yaml` 支持定义 Workspace 成员项目。
  - 支持 `project::ID` (例如 `FEAT-0004`) 的引用语法。
- [x] **Identity Stabilization (UID)**:
  - 在 Issue 元数据中引入全局唯一的 `uid` (Short Hash)。
  - 当 Issue 跨项目移动导致物理 ID 冲突时，系统能根据 `uid` 进行唯一性识别。
- [x] **Handle Interoperability**:
  - `monoco issue lint` 支持检测全工作区 ID 冲突。
  - 支持辅助工具自动处理跨项目移动时的"重编号 (Renumbering)"逻辑。

## Technical Tasks

- [x] 升级 `IssueID` 类以支持 Namespace 识别。
- [x] 改进 `IssueRepository` 使其能够递归搜索 Workspace 成员路径。
- [x] 在 `IssueMetadata` 中增加 `uid` 字段并兼容现有无 UID 的 Issue。
- [x] 增强 `monoco issue lint`，使其在 Workspace 级别扫描 ID 冲突。
- [x] 实现 `monoco issue move` 命令，支持跨项目移动并自动处理 ID 冲突。

## Review Comments

- [x] Self-Review
