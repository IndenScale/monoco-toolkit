---
id: FEAT-0176
uid: 3ba03d
type: feature
status: open
stage: review
title: 测试 close 无需 force
created_at: '2026-02-04T11:57:17'
updated_at: '2026-02-04T11:57:53'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0176'
files:
- '"Issues/Features/open/FEAT-0176-\346\265\213\350\257\225-close-\346\227\240\351\234\200-force.md"'
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T11:57:17'
isolation:
  type: branch
  ref: feat/feat-0176-测试-close-无需-force
  created_at: '2026-02-04T11:57:21'
---

## FEAT-0176: 测试 close 无需 force

## Objective

测试关闭 Issue 时不需要 --force 参数。

## Acceptance Criteria
- [x] 测试通过

## Technical Tasks
- [x] 完成测试

## Review Comments

验证 prune 失败不回滚事务的修复。
