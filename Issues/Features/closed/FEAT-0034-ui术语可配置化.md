---
id: FEAT-0034
type: feature
status: closed
stage: done
title: UI术语可配置化
created_at: '2026-01-12T17:27:04.755703'
opened_at: '2026-01-12T17:27:04.755703'
updated_at: '2026-01-13T08:35:36.579401'
closed_at: '2026-01-13T08:35:36.579422'
parent: EPIC-0004
solution: implemented
dependencies:
- FEAT-0029
- FEAT-0014
related: []
tags:
- '#EPIC-0004'
- '#FEAT-0014'
- '#FEAT-0029'
- '#FEAT-0034'
uid: fd8604
---

## FEAT-0034: UI术语可配置化

## Objective

实现 UI 层面的术语可配置化（Domain Dictionary Injection）。允许用户通过配置文件自定义核心实体（Epic/Feature 等）和生命周期阶段（Todo/Doing 等）的**显示名称**，从而在不修改底层逻辑的前提下，支持不同行业（如弱电工程、行政管理）的术语体系。

## Acceptance Criteria

1. **配置驱动**: 支持在 `monoco.yaml` 中定义 `ui.dictionary` 字段，映射内部枚举值到显示文本。
2. **默认回退**: 若未配置，默认使用标准的软件工程术语（Epic/Feature, To Do/In Progress）。
3. **API 暴露**: Daemon 需提供 `/config/dictionary` 接口，供前端获取当前术语表。
4. **全局替换**: Web 看板中的列名、卡片标签、创建弹窗及过滤器文案均需应用该映射。
5. **多语言支持**: 映射表结构应预留 I18n 支持（虽本阶段仅需支持单语言映射）。

## Technical Tasks

- [x] **Config**: 更新 `CoreConfig` 模型，增加 `ui_dictionary` 字段及默认值。
- [x] **API**: 在 `Daemon` 的配置接口中返回处理后的字典数据。
- [x] **Frontend (Context)**: 创建 `TermContext` (React Context)，全局分发术语定义。
- [x] **Frontend (UI)**: 替换所有硬编码的文本（如 `status === 'open'` 显示为 `dictionary.status_open`）。
- [x] **Docs**: 编写关于如何定制领域术语的用户文档示例。

## Review Comments

- [x] Self-Review
