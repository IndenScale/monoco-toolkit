---
id: FEAT-0007
type: feature
status: closed
title: Support External or Sub-project Issue Roots
created_at: "2026-01-09"
parent: EPIC-0001
dependencies:
  - FEAT-0002
related: []
solution: implemented
tags: []
---

## FEAT-0007: Support External or Sub-project Issue Roots

## Objective

支持在 Monorepo 或复杂项目结构中，Issue 目录不位于项目根目录的情况（如 `Domains/Business/Issues`），甚至支持多个 Issue 根目录聚合（Co-existence）。

## Acceptance Criteria

1. **Configurable Root**: `.monoco/config.yaml` 中的 `paths.issues` 应该支持深层路径配置（不仅是单纯的目录名）。
2. **Auto Discovery**: `monoco issue` 命令应该能够智能探测当前上下文的 Issue Root，或者支持 `--root` 参数显式指定。
3. **Multi-Root Support (Future)**: 能够聚合显示多个子项目的进度（Scope）。

## Technical Tasks

- [x] 验证并测试配置 `paths.issues` 为深层路径（如 `packages/frontend/Issues`）时的 CLI 表现。
- [x] 增强 `CommandLine` 参数解析，允许运行时覆盖 Issue Root。
- [x] 研究跨目录 / 跨项目的 Issue 引用机制。
