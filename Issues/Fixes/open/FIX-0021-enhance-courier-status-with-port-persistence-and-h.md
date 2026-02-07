---
id: FIX-0021
uid: 666b55
type: fix
status: open
stage: review
title: Enhance Courier Status with Port Persistence and Health Check
created_at: '2026-02-07T11:45:43'
updated_at: '2026-02-07T12:03:04'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0021'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Fixes/closed/FIX-0020-fix-courier-daemon-importerror.md
- Issues/Fixes/open/FIX-0020-fix-courier-daemon-importerror.md
- src/monoco/features/courier/commands.py
- src/monoco/features/courier/constants.py
- src/monoco/features/courier/service.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T11:45:43'
isolation:
  type: branch
  ref: FIX-0021-enhance-courier-status-with-port-persistence-and-h
  created_at: '2026-02-07T11:45:52'
---

## FIX-0021: Enhance Courier Status with Port Persistence and Health Check

## Objective

增强 Courier Status 的准确性，实现端口持久化和更强的健康检查。
当前的 `status` 命令无法感知非默认端口启动的服务，导致健康检查失败。需要将运行时的端口和 Host 信息持久化。

## Acceptance Criteria

- [x] `monoco courier start` 将运行参数（Host, Port, PID）写入状态文件（`.monoco/run/courier.json`）。
- [x] `monoco courier status` 读取状态文件，正确连接到服务 API。
- [x] `monoco courier status` 显示精确的健康检查结果（Validating /v1/health）。
- [x] `monoco courier stop` 清理状态文件。

## Technical Tasks

- [x] Update `src/monoco/features/courier/constants.py`: 添加 `COURIER_STATE_FILE` 常量。
- [x] Update `src/monoco/features/courier/service.py`:
  - `start()`: 写入状态文件。
  - `stop()`/`kill()`: 清理状态文件。
  - `get_status()`: 优先读取状态文件获取 URL。
- [x] Update `src/monoco/features/courier/api.py`: 确认健康检查接口路径。

## Review Comments

待实现。
