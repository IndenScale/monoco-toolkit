---
id: FEAT-0006
type: feature
status: closed
stage: Done
title: 支持层级 Issue 组织 (Support Hierarchical Issue Organization)
created_at: '2026-01-09'
parent: EPIC-0002
dependencies:
- FEAT-0002
related: []
solution: implemented
tags:
- '#EPIC-0002'
- '#FEAT-0002'
- '#FEAT-0006'
uid: d68c40
---

## FEAT-0006: 支持层级 Issue 组织 (Support Hierarchical Issue Organization)

## 目标 (Objective)

支持 `Issues/Stories/open/Backend/Auth/FEAT-123.md` 这样的深层目录结构，允许用户根据业务域、模块或组件对 Issue 进行物理分组，而不仅仅依赖于扁平的文件列表。

## 验收标准 (Acceptance Criteria)

1. **发现 (Discovery)**: `monoco issue scope/lint` 默认仅扫描一级目录（浅层）。必须支持 `-r/--recursive` 参数以开启递归扫描（深层）。
2. **校验 (Linting)**: `lint` 规则需放宽，允许 Issue 存在于子目录。如果不开启 `-r`，则忽略子目录违规（因为看不到）。
3. **创建 (Creation)**: `monoco issue create` 支持 `--subdir` 参数。
4. **结构完整性 (Structure Integrity)**: 当 Issue 状态流转（如 `open` -> `closed`）时，**必须保留**其原有的子目录结构，禁止将其扁平化移动到根目录。

## 技术任务 (Technical Tasks)

- [x] 更新 `monoco.features.commands.lint` 和 `scope`，添加 `--recursive` 参数，默认关闭递归。
- [x] 更新 `core.py` 逻辑，在 `update_issue_status` 中计算相对路径，确保 `rename` 操作保留子目录层级。
- [x] 验证 `core.parse_issue` 和 `core.find_next_id` 的路径查找逻辑。
- [x] (可选) 在 `create` 命令中添加 `--subdir` 参数以支持直接创建在子目录中。

## Review Comments

- [x] Self-Review
