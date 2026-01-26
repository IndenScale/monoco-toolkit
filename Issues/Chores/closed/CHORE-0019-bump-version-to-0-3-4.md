---
id: CHORE-0019
uid: 8c2798
type: chore
status: closed
stage: done
title: 升级版本至 0.3.4
created_at: '2026-01-26T01:17:29'
opened_at: '2026-01-26T01:17:29'
updated_at: '2026-01-26T01:18:07'
closed_at: '2026-01-26T01:18:07'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0019'
files: []
---

## CHORE-0019: 升级版本至 0.3.4

## 目标 (Objective)
将所有 Toolkit 组件的版本升级到 0.3.4，紧随 v0.3.3 发布之后。这确保所有包在下一个开发周期中保持同步。

## 验收标准 (Acceptance Criteria)
- [x] 所有包 (`pyproject.toml`, `package.json`s) 均已更新至 0.3.4。
- [x] 验证脚本通过。

## 技术任务 (Technical Tasks)
- [x] 运行 `scripts/set_version.py 0.3.4`。
- [x] 运行 `scripts/verify_versions.py` 以确认一致性。

## 评审备注 (Review Comments)
- 使用辅助脚本成功更新了 5 个文件。
- 验证了所有组件的一致性。
