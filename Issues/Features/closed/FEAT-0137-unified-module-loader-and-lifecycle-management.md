---
id: FEAT-0137
uid: c4bb18
type: feature
status: closed
stage: done
title: Unified Module Loader and Lifecycle Management
created_at: '2026-02-01T10:30:04'
updated_at: '2026-02-01T23:45:28'
parent: EPIC-0028
dependencies: []
related: []
domains:
- Foundation
tags:
- '#EPIC-0028'
- '#FEAT-0137'
- kernel
- loader
files:
- monoco/core/loader.py
- monoco/core/registry.py
- monoco/main.py
- monoco/features/issue/adapter.py
- monoco/features/agent/adapter.py
- monoco/features/spike/adapter.py
- monoco/features/memo/adapter.py
- monoco/features/i18n/adapter.py
- monoco/features/glossary/adapter.py
criticality: high
solution: implemented
opened_at: '2026-02-01T10:30:04'
closed_at: '2026-02-01T23:45:28'
isolation:
  type: branch
  ref: feat/feat-0137-unified-module-loader-and-lifecycle-management
  created_at: '2026-02-01T23:38:08'
---

## FEAT-0137: Unified Module Loader and Lifecycle Management

## Objective
统一管理 Monoco 生态系统中的 Feature 模块加载与生命周期。Monoco 现在拥有越来越多的功能模块（Issue, Memo, Agent 等），我们需要一个标准化的 Loader 来处理 `monoco/features/` 目录下的动态加载、依赖解析以及 `mount/unmount` 生命周期钩子。这有助于减少启动时间并实现“按需加载”。

## Acceptance Criteria
- [x] **Dynamic Discovery**: 能够自动发现 `monoco/features` 下的所有子模块。
- [x] **Lifecycle Hooks**: 支持标准模块协议 (`mount()`, `unmount()`)。
- [x] **Dependency Injection**: 自动将模块注册到 IoC 容器中。
- [x] **Lazy Loading**: 验证非关键模块可以延迟加载以加快 CLI 启动。

## Technical Tasks
- [x] **Spec Definition**: 定义 `FeatureModule` 抽象基类。
- [x] **Loader Impl**: 实现 `FeatureLoader` 类，利用 `importlib` 动态加载。
- [x] **Integration**: 在 `monoco/main.py` 中集成 Loader (替代 kernel.py)。
- [x] **Migration**: 将所有模块 (Issue, Agent, Spike, Memo, I18n, Glossary) 适配到新 Loader 协议。

## Review Comments

### 2026-02-01: Implementation Complete

**Summary**: Successfully implemented the Unified Module Loader and migrated all feature adapters.

**Changes Made**:
1. **monoco/core/loader.py**: Already implemented (pre-existing)
   - `FeatureModule` abstract base class with lifecycle hooks
   - `FeatureLoader` with dynamic discovery via `importlib`
   - `FeatureRegistry` for managing feature instances
   - `FeatureContext` for dependency injection
   - `ServiceContainer` for IoC
   - Lazy loading support for non-critical features

2. **monoco/core/registry.py**: Updated to wrap `FeatureLoader`
   - Maintains backward compatibility
   - Delegates to `FeatureLoader` for dynamic discovery

3. **monoco/main.py**: Integrated `FeatureLoader` into CLI lifecycle
   - Added `get_feature_loader()` function
   - Features are discovered, loaded (with lazy loading), and mounted when workspace is available

4. **Feature Adapters Migrated** (all now extend `FeatureModule`):
   - `monoco/features/issue/adapter.py`: IssueFeature with priority=10
   - `monoco/features/agent/adapter.py`: AgentFeature with priority=20
   - `monoco/features/spike/adapter.py`: SpikeFeature with priority=30
   - `monoco/features/memo/adapter.py`: MemoFeature with priority=40, lazy=True
   - `monoco/features/i18n/adapter.py`: I18nFeature with priority=50, lazy=True
   - `monoco/features/glossary/adapter.py`: GlossaryFeature with priority=60, lazy=True

**Testing**: All 358 tests pass (excluding 6 pre-existing failures unrelated to this change).
