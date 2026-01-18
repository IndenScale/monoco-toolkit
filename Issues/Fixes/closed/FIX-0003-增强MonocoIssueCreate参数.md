---
id: FIX-0003
type: fix
status: closed
stage: done
title: 增强 monoco issue create 以支持缺失参数和输出 (Enhance monoco issue create)
created_at: "2026-01-10T20:40:55.417933"
opened_at: "2026-01-10T20:40:55.417933"
updated_at: "2026-01-13T08:37:54.758332"
closed_at: "2026-01-10T20:46:20.951561"
parent: EPIC-0002
solution: implemented
dependencies: []
related: []
tags: []
uid: cdf64e
---

## FIX-0003: 增强 monoco issue create 以支持缺失参数和输出 (Enhance monoco issue create)

## 目标 (Objective)

改进 `monoco issue create` 命令以支持完整的元数据填充，并提供对 Agent 友好的输出。这解决了调查中发现的不足，即 Agent 无法轻易确定已创建文件的路径或设置 Sprint 和 Tag 等初始字段。

## 验收标准 (Acceptance Criteria)

1. **缺失参数支持 (Missing Parameters Support)**:
   - 创建时支持设置 Sprint ID (`--sprint <ID>`)。
   - 创建时支持设置多个 Tag (`--tags <tag>`)。
2. **输出路径 (Output Path)**:
   - 该命令必须在成功消息中或作为单独的一行输出已创建文件的绝对或相对路径，使 Agent 能够立即定位并编辑该文件。
3. **校验 (Validation)**:
   - 在创建之前，验证提供的 `--dependency` 和 `--related` ID 确实存在于 Issue 数据库中。

## 技术任务 (Technical Tasks)

- [x] 更新 `Toolkit/monoco/features/issue/commands.py`: 为 `create` 命令添加 `sprint` 和 `tags` 选项。
- [x] 更新 `Toolkit/monoco/features/issue/core.py`: 更新 `create_issue_file` 签名 and 逻辑以处理新字段。
- [x] 在 `create_issue_file` 中实现对 `dependencies` 和 `related` 的存在性检查（重用 `find_issue_path`）。
- [x] 修改 `Toolkit/monoco/features/issue/commands.py`: 更新成功打印信息以包含 `issue_path`。

## Review Comments

- [x] Self-Review
