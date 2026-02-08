---
id: FIX-0026
uid: 0b22a2
type: fix
status: open
stage: review
title: Fix VS Code Extension workflow path
created_at: '2026-02-08T10:31:02'
updated_at: '2026-02-08T10:32:01'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0026'
files:
- .github/workflows/publish-vscode-extension.yml
- uv.lock
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-08T10:31:02'
isolation:
  type: branch
  ref: FIX-0026-fix-vs-code-extension-workflow-path
  created_at: '2026-02-08T10:31:05'
---

## FIX-0026: Fix VS Code Extension workflow path

## Objective
修复 VS Code Extension 发布 workflow 中的路径错误，使其能正确构建 CLI 二进制文件。

## Acceptance Criteria
- [x] Workflow 使用正确的入口文件路径 `src/monoco/main.py`
- [x] CI 能够成功构建各平台二进制

## Technical Tasks
- [x] 修改 `.github/workflows/publish-vscode-extension.yml` 第59行
  - 将 `monoco/main.py` 改为 `src/monoco/main.py`

## Review Comments

- 路径错误导致 pyinstaller 无法找到入口文件
- 修复后 CI 应能正常构建
