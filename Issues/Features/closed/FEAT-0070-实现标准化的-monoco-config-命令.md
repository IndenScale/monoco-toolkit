---
id: FEAT-0070
uid: f8a2b9
type: feature
status: closed
stage: done
title: 实现标准化的 monoco config 命令
created_at: '2026-01-15T14:29:26'
opened_at: '2026-01-15T14:29:26'
updated_at: '2026-01-15T14:32:50'
closed_at: '2026-01-15T14:32:50'
parent: EPIC-0013
solution: implemented
dependencies: []
related: []
tags:
- '#EPIC-0013'
- '#FEAT-0070'
---

## FEAT-0070: 实现标准化的 monoco config 命令

## 背景 (Context)

当前系统配置已收敛至 `.monoco/config.yaml`。为了方便开发者查看（Inspect）和修改（Mutate）配置，需要一个标准化的 CLI 命令，该命令必须严格遵循 `monoco.core.config.MonocoConfig` 定义的 Schema。
此功能是 EPIC-0013 "Config Convergence" 的核心组成部分。

## 目标 (Objective)

提供一组符合人体工学的 CLI 命令，用于安全地读写项目及全局配置。

1.  **`monoco config show`**:
    - 展示当前环境的**最终生效配置**（Merged Config: Global < Project）。
    - 支持 `--json` 或 `--yaml` 格式输出，方便脚本集成。
2.  **`monoco config get <key>`**:
    - 获取特定配置项的值（e.g., `monoco config get project.key`）。
3.  **`monoco config set <key> <value>`**:
    - 支持修改 **Project Scope** (`./.monoco/config.yaml`) 或 **Global Scope** (`~/.monoco/config.yaml`)。
    - **关键约束**: 写入前必须通过 `MonocoConfig` Pydantic 模型的校验，防止写入非法配置。

## 验收标准 (Acceptance Criteria)

- [x] **Schema 校验**: 所有的写操作（Set）必须经过 Pydantic Model 校验，非法 Key 或类型错误应被拒绝。
- [x] **层级一致性**: `show` 命令展示的配置必须与 `monoco serve` 运行时实际加载的配置完全一致。
- [x] **Scope 支持**: `set` 命令支持明确指定 `-g/--global` 或默认（Local）作用域。
- [x] **DX 优化**: 当修改嵌套 Key 时（如 `telemetry.enabled`），若父节点不存在应自动创建。

## 技术任务 (Technical Tasks)

- [x] **Core**: 增强 `monoco.core.config`，提供 `ConfigScope` 枚举和特定 Scope 的加载/保存方法。
- [x] **CLI**: 重构 `monoco/features/config/commands.py`。
- [x] **CLI**: 实现 `show` 命令（支持 `--format`）。
- [x] **CLI**: 实现 `get` 命令（支持点号路径访问 `project.name`）。
- [x] **CLI**: 实现 `set` 命令（集成 Pydantic 校验和 YAML 回写）。

## Review Comments

- [x] Self-Review
