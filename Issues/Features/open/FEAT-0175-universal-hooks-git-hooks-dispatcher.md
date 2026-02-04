---
id: FEAT-0175
uid: ddde11
type: feature
status: open
stage: doing
title: 'Universal Hooks: Git Hooks Dispatcher'
created_at: '2026-02-04T13:27:07'
updated_at: '2026-02-04T14:20:03'
parent: EPIC-0034
dependencies:
- FEAT-0174
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0034'
- '#FEAT-0174'
- '#FEAT-0175'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T13:27:07'
---

## FEAT-0175: Universal Hooks: Git Hooks Dispatcher

## 目标

实现 Git Hooks 的分发器，支持将 `type: git` 的 Hooks 安装到 `.git/hooks/` 目录，与现有 Git Hooks 管理机制兼容。

## 验收标准

- [ ] 实现 `GitHookDispatcher` 类
- [ ] 支持事件：pre-commit, prepare-commit-msg, commit-msg, post-merge, pre-push
- [ ] 生成 `monoco-runner` 代理脚本，调用 `monoco hook run git <event>`
- [ ] 支持 Glob matcher：基于 staged files 过滤触发
- [ ] 非破坏性安装：与现有 Husky/pre-commit 配置共存
- [ ] 与现有 Git Hooks Marker 标记机制兼容

## 技术任务

### GitHookDispatcher 实现
- [ ] 实现 `GitHookDispatcher` 类（继承自 `HookDispatcher` 基类）
  - [ ] `install(hook)`: 生成 `.git/hooks/<event>` 代理脚本
  - [ ] `uninstall(hook)`: 移除代理脚本并恢复原始状态
  - [ ] `list()`: 列出当前安装的所有 Git Hooks
- [ ] 代理脚本模板：
  ```bash
  #!/bin/sh
  # MONOCO_HOOK_MARKER: <hook-id>
  exec monoco hook run git <event> "$@"
  ```

### Glob Matcher 支持
- [ ] 在代理脚本中集成 staged files 检测
- [ ] 根据 hook 的 `matcher` 字段（如 `**/*.py`）过滤文件
- [ ] 无匹配文件时静默跳过（exit 0）

### 非破坏性安装
- [ ] 检测 `.git/hooks/<event>` 是否已存在
- [ ] 如果存在且非 Monoco 创建，采取合并执行（Append）策略
- [ ] 备份原始 hook 以便卸载时恢复

### 集成
- [ ] 注册到 `UniversalHookManager`
- [ ] 在 `monoco sync` 中触发 Git Hooks 同步
- [ ] 在 `monoco uninstall` 中清理 Git Hooks

## Review Comments
<!-- 评审阶段时填写 -->
