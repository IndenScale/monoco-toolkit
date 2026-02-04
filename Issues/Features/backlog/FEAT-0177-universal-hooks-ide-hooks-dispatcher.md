---
id: FEAT-0177
uid: 234a7a
type: feature
status: backlog
stage: freezed
title: 'Universal Hooks: IDE Hooks Dispatcher'
created_at: '2026-02-04T13:27:08'
updated_at: '2026-02-04T21:22:02'
parent: EPIC-0034
dependencies:
- FEAT-0174
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0034'
- '#FEAT-0174'
- '#FEAT-0177'
files:
- docs/zh/90_Spikes/hooks-system/ide_hooks/ide_hooks_standard_ZH.md
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T13:27:08'
---

## FEAT-0177: Universal Hooks: IDE Hooks Dispatcher

## 目标

实现 IDE Hooks 分发器，支持 `type: ide` 的 Hooks 按 `provider` 分发到 VS Code 等 IDE。

## 背景

IDE Hooks 通过配置注入实现（无原生 Hook 机制），详见 [IDE Hooks 标准化方案](../../docs/zh/90_Spikes/hooks-system/ide_hooks/ide_hooks_standard_ZH.md)。

## 验收标准

- [ ] 实现 `IDEHookDispatcher` 基类
- [ ] 实现 `VSCodeDispatcher`：生成 `.vscode/tasks.json` 和 `settings.json`
- [ ] 支持事件：`on-save` (codeActionsOnSave), `on-open` (folderOpen task)
- [ ] 非阻塞设计：IDE hooks 异步执行，200ms 超时保护
- [ ] 静默失败：Hook 失败不干扰正常代码编辑

## 技术任务

### IDEHookDispatcher 框架
- [ ] 实现 `IDEHookDispatcher` 基类
  - [ ] 按 `provider` 字段路由到对应子分发器
- [ ] 实现 `VSCodeDispatcher`
  - [ ] 读取/写入 `.vscode/tasks.json`
  - [ ] 读取/写入 `.vscode/settings.json`
  - [ ] 配置合并（不覆盖用户已有配置）

### 事件实现
- [ ] `on-save` 事件：
  - [ ] 生成 Task 定义在 `tasks.json`
  - [ ] 在 `settings.json` 中配置 `editor.codeActionsOnSave`
  - [ ] 支持 `matcher` 过滤文件类型
- [ ] `on-open` 事件：
  - [ ] 生成 `runOn: folderOpen` 的 Task
  - [ ] 支持任务链（依赖其他任务）

### 配置示例
生成的 `.vscode/tasks.json`：
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "monoco-hook-on-save",
      "type": "shell",
      "command": "monoco hook run ide on-save",
      "problemMatcher": [],
      "isBackground": true
    }
  ]
}
```

生成的 `.vscode/settings.json`：
```json
{
  "editor.codeActionsOnSave": {
    "source.monoco.hooks": "explicit"
  }
}
```

### 非阻塞设计
- [ ] 所有 IDE Hooks 标记为 `isBackground: true`
- [ ] 200ms 超时保护（VS Code 任务配置）
- [ ] 静默失败：不显示错误弹窗，仅记录到 Output 面板

### 集成
- [ ] 注册 `VSCodeDispatcher` 到 `UniversalHookManager`
- [ ] 在 `monoco sync` 中触发 IDE Hooks 同步
- [ ] 在 `monoco uninstall` 中清理 IDE Hooks

## Review Comments
<!-- 评审阶段时填写 -->
