---
id: FEAT-0072
uid: c2d9e1
type: feature
status: closed
stage: done
title: Core Agent Environment Manager (Sync & Uninstall)
created_at: "2026-01-15T15:35:00"
opened_at: "2026-01-15T15:35:00"
updated_at: "2026-01-15T15:59:58"
closed_at: "2026-01-15T15:59:58"
parent: EPIC-0014
solution: implemented
dependencies:
  - FEAT-0071
related: []
tags:
  - agent-native
  - cli
  - core
---

## FEAT-0072: Core Agent Environment Manager (Sync & Uninstall)

## 背景 (Context)

`FEAT-0071` 完成了 Agent Environment Injection 的 MVP 实现（主要是写入逻辑）。但为了满足 `EPIC-0014` 的最终验收标准，核心引擎仍缺失以下关键能力：

1. **无法撤销**: 缺少 `uninstall` 命令，用户无法一键清理注入的内容。
2. **配置硬编码**: `sync` 目前仅针对硬编码的文件列表，无法通过 `.monoco/config.yaml` 定制（如指定 Framework 或 Target File）。
3. **协议不完善**: 尚未通过 `MonocoFeature` 协议完全解耦，`sync` 命令中仍包含特定的 Feature 类引用。

## 目标 (Objective)

完善 Monoco Agent Environment Manager 的核心引擎，实现全生命周期管理（Sync + Uninstall）与配置驱动（Configuration Driven）。

1. **Uninstall Command**: 实现 `monoco uninstall`，彻底清理所有 "Managed Block"。
2. **Config Driven**: 让 `sync` 读取 `.monoco/config.yaml` 中的 `agent` 配置段。
3. **Protocol Refactor**: 重构 Core Bus，使其通过通用协议遍历 Feature，而非硬编码。

## 验收标准 (Acceptance Criteria)

- [x] **Uninstall**: 运行 `monoco uninstall` 后，目标文件（如 `GEMINI.md` 或 `.cursorrules`）中的 `## Monoco Toolkit` 及其内容应被完全移除，且不破坏文件其他部分。
- [x] **Configurable Targets**: 支持在配置中定义 `agent.targets`，`sync` 命令应遵循该配置及其注入策略。
- [x] **Framework Awareness**: 能够识别配置中的 `agent.framework` 并据此调整注入格式（虽然目前主要都是 Markdown，但需预留接口）。
- [x] **Idempotency**: `sync` 和 `uninstall` 都必须是幂等的。
- [x] **Rigorous Testing**: 核心逻辑必须有 Pytest 覆盖，特别是 `PromptInjector` 的文件操作，必须验证如果不做恶（Do No Harm），不破坏用户现有数据。

## 技术任务 (Technical Tasks)

- [x] **Core**: 扩展 `PromptInjector` 类，新增 `remove()` 方法 (Reverse of `inject`)。
  - 逻辑: 定位 `MANAGED_HEADER`，识别 Block 边界，执行删除并清理多余空行。
- [x] **QA**: 编写 `tests/core/test_injector.py` 单元测试。
  - Case: 空文件/新文件注入（自动初始化一级标题，如 ` # AGENTS``# Gemini Memory `）。
  - Case: 现有文件追加/插入/覆盖。
  - Case: 幂等性验证（重复注入不改变内容）。
  - Case: 删除逻辑验证（完美还原，不残留空行）。
- [x] **CLI**: 实现 `monoco uninstall` 命令。
  - 流程: Load Config -> Detect Targets -> Injector.remove() -> Report.
- [x] **Config**: 更新 `Config`模型，增加 `AgentConfig` 字段 (Pydantic Model)。
  - `includes`: List[str] (Optional features)
- [x] **Refactor**: 重构 `monoco/core/sync.py`。
  - 移除 `from monoco.features.xxx import XxxFeature` 硬编码。
  - 使用 `monoco.core.registry.get_features()` 动态获取。
- [x] **NOTE**: Skill synchronization logic is DEFERRED to FEAT-0073. Only Prompt Injection is covered here.
