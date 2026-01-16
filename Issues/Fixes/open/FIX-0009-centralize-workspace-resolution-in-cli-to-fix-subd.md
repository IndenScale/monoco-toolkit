---
id: FIX-0009
uid: 39de87
type: fix
status: open
stage: draft
title: Centralize workspace resolution in CLI to fix subdirectory context issues
created_at: '2026-01-16T12:01:06'
opened_at: '2026-01-16T12:01:06'
updated_at: '2026-01-16T12:01:06'
dependencies: []
related: []
tags: []
---

## FIX-0009: Centralize workspace resolution in CLI to fix subdirectory context issues

## Objective

`monoco` CLI 之前允许在任意目录执行并试图（或计划）进行模糊的上下文推断，这导致了不确定性和错误。为了保证系统的严谨性，我们需要实施严格的工作区边界控制。

目标是：
1.  **禁止模糊推断**：`monoco` 命令必须在明确的 Monoco Workspace 根目录下执行，或者通过参数明确指定根目录。严禁在非 Workspace 目录下通过递归查找来猜测上下文。
2.  **强制参数化**：如果操作针对特定 Project，必须显式提供 Project ID 或 Project Dir。
3.  **依赖 .monoco**：除 `init` 外的所有命令，必须在包含 `.monoco` 目录的 Workspace 根路径下执行（或通过 `--root` 指定）。这是识别 Workspace 的唯一依据。
4.  **扩展规范化**：VS Code 扩展等外部调用者必须在调用 CLI 时显式传递 `--root` 或相关上下文参数，而不是依赖 CLI 的隐式行为。

## Acceptance Criteria

1.  **严格检查**：在非 Monoco Workspace 根目录（无 `.monoco` 目录）下执行命令（除 `init`）应直接报错，除非提供了 `--root` 参数指向有效的根目录。
2.  **显式项目指定**：除 `init` 外的所有命令，如果不提供 Project ID，则默认操作 Workspace 根项目；如果目标是子项目，必须通过参数指定。
3.  **扩展调用修正**：VS Code 扩展在调用 `monoco` CLI 时，必须始终带上 `--root <workspace_root>` 参数。

## Technical Tasks

- [ ] 修改 `monoco.core.config.MonocoConfig.load`，移除或确保不引入任何递归查找逻辑。如果当前目录（或指定 `root`）没有 `.monoco` 目录，则抛出异常或错误（`init` 命令除外）。
- [ ] 确保 CLI 入口点在需要 Workspace 上下文时进行严格校验。
- [ ] 更新 VS Code 扩展 (`Toolkit/extensions/vscode`) 的调用逻辑，确保所有 CLI 调用都显式传递工作区根路径。
- [ ] 验证在子目录直接运行 `monoco` 命令会失败或提示错误。
- [ ] 验证 VS Code 扩展在打开子目录或根目录时均能正常工作（因为参数已显式传递）。
