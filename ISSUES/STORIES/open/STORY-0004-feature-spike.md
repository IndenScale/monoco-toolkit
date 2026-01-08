---
parent: EPIC-0001
id: STORY-0004
type: story
status: open
title: "Feature: Spike Management (Local)"
created_at: 2026-01-08
tags: [toolkit, feature, spike, architecture]
---

parent: EPIC-0001

## STORY-0004: Spike Management (Local)

## Objective

实现 `monoco spike` 子命令，用于管理技术调研 (Spike) 和参考资料。

## Acceptance Criteria

1. **List Command**: `monoco spike list` 列出所有 Spike (通常位于 `SPIKES/` 或 `docs/`?). _注：需确认 Spike 存储位置，目前假设与 Issue 类似机制_。
2. **Tracking**: 能够关联 Issue 与 Spike 文档。

## Technical Tasks

- [ ] Define Spike directory structure / file convention.
- [ ] Implement `monoco spike list`.
- [ ] Integrate with `monoco.core.output`.
