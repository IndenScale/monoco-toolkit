---
id: FIX-0020
uid: 717e9d
type: fix
status: open
stage: review
title: Fix Courier Daemon ImportError
created_at: '2026-02-07T11:39:24'
updated_at: '2026-02-07T11:45:35'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0020'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- src/monoco/features/courier/daemon.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T11:39:24'
isolation:
  type: branch
  ref: FIX-0020-fix-courier-daemon-importerror
  created_at: '2026-02-07T11:39:33'
---

## FIX-0020: Fix Courier Daemon ImportError

## Objective

修复 Courier Daemon 启动时的 `ImportError`。
`daemon.py` 尝试从 `monoco.features.connector.protocol.constants` 导入 `COURIER_DEFAULT_HOST` 和 `COURIER_DEFAULT_PORT`，但这些常量实际定义在 `monoco.features.courier.constants`。

## Acceptance Criteria

- [x] `monoco courier start` 成功启动服务。
- [x] `monoco courier status` 显示服务为 `running` 状态。
- [x] `monoco courier logs` 中不再出现 `ImportError`。

## Technical Tasks

- [x] 修正 `src/monoco/features/courier/daemon.py` 中的导入语句。

## Review Comments

修复已验证。
