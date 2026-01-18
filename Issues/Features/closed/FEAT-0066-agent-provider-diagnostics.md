---
id: FEAT-0066
uid: fe5b70
type: feature
status: closed
stage: done
title: 智能体运行时诊断 (Agent Runtime Diagnostics)
created_at: "2026-01-15T08:55:53"
opened_at: "2026-01-15T08:55:53"
updated_at: "2026-01-16T08:34:01"
closed_at: "2026-01-16T08:34:01"
parent: EPIC-0012
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0066: 智能体运行时诊断 (Agent Runtime Diagnostics)

## 目标

提供诊断能力以验证已配置智能体运行时的运行状况。
这确保了当 Monoco 尝试将任务委托给智能体（例如通过 CLI）时，该工具实际上是可用且可执行的。

## 验收标准

1. **二进制文件检查**: 验证配置的可执行文件路径存在且具有执行权限。
2. **版本检查**: 尝试使用 `--version`（或等效命令）运行该运行时以验证响应能力。
3. **命令行界面**: 通过 `monoco doctor` 或 `monoco agent check` 公开这些检查。

## 技术任务

- [x] 为 `AgentIntegration` 实现 `Diagnostics` 接口。
- [x] 实现通用的二进制文件检查（路径存在性、权限）。
- [x] 为已知集成（Gemini CLI 等）添加特定的版本检查。
- [x] 集成到 Monoco Doctor 系统。

## Review Comments

- [x] Self-Review
