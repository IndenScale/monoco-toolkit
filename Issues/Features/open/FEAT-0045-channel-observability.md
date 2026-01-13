---
id: FEAT-0045
uid: f8d3c1
type: feature
status: open
stage: todo
parent: null
title: Channel Observability (Distribution Stats)
created_at: "2026-01-13T11:16:44"
opened_at: "2026-01-13T11:16:44"
updated_at: "2026-01-13T12:22:00"
dependencies: []
related: []
tags:
  - telemetry
  - growth
---

## FEAT-0045: Channel Observability (Distribution Stats)

## Objective

建立分发渠道的宏观指标监控逻辑，重点关注各平台的 **下载量 (Downloads)** 和 **装机量 (Installs)**，以验证推广覆盖度。

## Acceptance Criteria

- [x] **Infrastructure**: 完成 Telemetry 后端选型 (PostHog) 与 SDK 封装 (`monoco.core.telemetry`)。
- [x] **Identity**: 实现匿名的 Device ID 生成与持久化逻辑 (`~/.monoco/state.json`)。
- [x] **Privacy**: 实现 `monoco config set telemetry false` 开关，且在 `monoco init` 时主动询问。
- [x] **Metrics**:

  - [x] CLI: 能够捕获命令执行事件 (活跃 UV)。
  - [ ] Kanban: 能够捕获页面浏览事件 (Pending library installation)。

- [ ] **Market Stats Aggregation** (External Data):
  - [ ] 聚合各分发渠道的 **下载量 (Downloads)** 和 **装机量 (Installs)** 数据。
  - [ ] 覆盖渠道:
    - **VS Code Extension**: VS Marketplace (VSX) & Open VSX (OVSX).
    - **Package Managers**: PyPI (monoco), NPM (web artifacts).
    - **OS Stores**: App Store (Future proofing).
    - **Direct**: 官网下载 (DMG/Brew 统计).

## Technical Tasks

- [x] 初始化 PostHog Project "Monoco Growth" 并获取 API Key。
- [x] 实现 `monoco.core.telemetry` 模块 (Device ID 管理, Event Queue)。
- [x] 集成 Telemetry 到 `monoco` CLI 入口 (Capture Cmd Execution)。
- [ ] 集成 PostHog JS SDK 到 Kanban Next.js 应用 (Capture Page View)。
- [ ] **External Stats ETL**:
  - [x] Create internal analytics scripts.
  - [ ] 实现抓取逻辑: PyPI (BigQuery/JSON), VSX (API/Scrape), NPM (API)。
  - [ ] 实现上报逻辑: 将统计数据作为 Custom Events (`stats_update`) 发送至 PostHog。
- [ ] **Visualization**:
  - [ ] 在 PostHog 中配置 Dashboard，聚合 Internal Events (CLI/Kanban) 和 External Stats。
