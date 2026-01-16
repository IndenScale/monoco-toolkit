---
id: CHORE-0003
uid: ee962c
type: chore
status: closed
stage: done
title: 重构配置加载以统一上下文
created_at: '2026-01-15T12:55:25'
opened_at: '2026-01-15T12:55:25'
updated_at: '2026-01-15T13:06:28'
closed_at: '2026-01-15T13:06:28'
solution: implemented
dependencies: []
related: []
tags: []
---

## CHORE-0003: 重构配置加载以统一上下文

## 上下文

目前，系统同时支持 `monoco.yaml`（在文件根目录）和 `.monoco/config.yaml`。
这种双重支持造成了歧义和维护开销。
**决定**：我们将标准化使用 **`.monoco/` 目录** 作为 Monoco 上下文的唯一标识符。

## 目标

从代码库中移除对 `monoco.yaml` 的所有依赖。
配置必须驻留在 `.monoco/config.yaml` 中。

## 父级

EPIC-0013

## 技术任务

- [x] **更新配置加载器**：修改 `monoco.core.config.py` 以停止查找 `monoco.yaml`。
- [x] **更新工作区扫描器**：修改 `monoco.core.workspace.py`（以及任何 `ProjectManager` 逻辑）仅通过 `.monoco/` 目录的存在来识别项目。
- [x] **迁移工具（可选）**：添加逻辑片段，如果找到 `monoco.yaml` 则警告用户并建议移动它。

## 验收标准

- [x] `monoco.core.config.get_config` 被标记为旧版/已弃用或严格限制在当前工作目录范围内。
- [x] `ProjectManager` 可以加载项目 A 和项目 B，且 `ProjectContext(A).config` 与 `ProjectContext(B).config` 不同。
- [x] `monoco serve` 正确启动。

## 解决方案

重构了配置加载以标准化为 `.monoco/config.yaml`。移除了对 `monoco.yaml` 的所有依赖。
将存储库中现有的 `monoco.yaml` 文件迁移到其各自的 `.monoco/` 目录中。
在 `monoco.core.config.py` 中为仍在使用 `monoco.yaml` 的用户添加了旧版警告。
更新了 `core.workspace.is_project_root` 以仅通过 `.monoco/` 目录的存在来识别项目。

## Review Comments

- [x] Self review
