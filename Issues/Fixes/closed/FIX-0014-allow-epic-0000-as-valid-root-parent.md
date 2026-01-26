---
id: FIX-0014
uid: 9c31d5
type: fix
status: closed
stage: done
title: 允许 EPIC-0000 作为有效根父节点
created_at: '2026-01-26T22:14:48'
updated_at: '2026-01-26T22:21:48'
parent: null # <EPIC-ID> Optional
dependencies: []
related: []
domains: []
tags:
- '#FIX-0014'
files: []
opened_at: '2026-01-26T22:14:48'
closed_at: '2026-01-26T22:21:39'
solution: implemented
isolation:
  type: branch
  ref: feat/fix-0014-allow-epic-0000-as-valid-root-parent
  created_at: '2026-01-26T22:18:50'
---

## FIX-0014: 允许 EPIC-0000 作为有效根父节点

## 问题陈述 (Problem Statement)
初始化新的 Monoco Workspace (如 Cortex) 时，用户通常会创建 "Genesis Epic" (例如 EPIC-0001)。然而，Monoco Linter 强制执行严格的层级结构，要求每个 Epic 必须有一个父级。
目前，将 `EPIC-0000` 或 `null` 指定为父级会触发 `Broken Reference` 错误，因为 `EPIC-0000` 在文件系统中物理不存在。
这造成了一个启动死锁，导致第一个 Epic 无法通过验证。

## 解决方案设计 (Solution Design)
我们将 `EPIC-0000` 视为 **虚拟根 Epic** (Sentinel Value)。

1.  **Linter 修改**:
    - 在层级验证逻辑中，检查 `parent_id`。
    - 如果 `parent_id == 'EPIC-0000'`，跳过 "存在性检查" (不查找 `Issues/Epics/*/EPIC-0000.md`)。
    - 视指向 `EPIC-0000` 的引用为有效出站链接。
2.  **替代方案 (未来)**:
    - `monoco init` 可以自动创建一个物理的 `EPIC-0000-genesis.md` 文件，但在现有工作区中，虚拟根更为整洁。

## 影响 (Impact)
- 允许用户定义顶层 Epic 的 `parent: EPIC-0000`。
- 修复新工作区中的 `monoco issue lint` 失败问题。

## 技术任务 (Technical Tasks)

- [x] 修改 Linter 逻辑以豁免 EPIC-0000 的存在性检查。
- [x] 更新验证测试用例。

## 验证 (Verification)
- 创建一个 `parent: EPIC-0000` 的 Epic。
- 运行 `monoco issue lint`。
- 预期：没有关于父级引用的错误/警告。

## 评审备注 (Review Comments)
<!-- Required for Review/Done stage. Record review feedback here. -->
