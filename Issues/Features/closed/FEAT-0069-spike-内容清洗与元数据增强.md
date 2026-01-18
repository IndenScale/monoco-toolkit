---
id: FEAT-0069
uid: 939d85
type: feature
status: closed
stage: done
title: Spike 内容清洗与元数据增强
created_at: "2026-01-15T13:35:38"
opened_at: "2026-01-15T13:35:38"
updated_at: "2026-01-15T13:37:41"
closed_at: "2026-01-15T13:37:41"
parent: EPIC-0003
solution: cancelled
dependencies: []
related: []
tags: []
---

## FEAT-0069: Spike 内容清洗与元数据增强

## Objective

在摄入外部 URL 知识时，自动去除 HTML 中的噪音（广告、导航栏、脚本等），并将其转换为结构化的 Markdown 格式。同时增强元数据，记录原始 URL、抓取时间及核心摘要。

## Acceptance Criteria

1. **内容提取**: 集成 `trafilatura` 或类似库，准确提取网页正文。
2. **格式转换**: 输出纯净的 Markdown，保留标题结构和列表。
3. **元数据持久化**: 在导出的 Markdown 文件 Front Matter 中包含 `source_url`, `captured_at`, `title` 等信息。
4. **CLI 集成**: `monoco spike add` 命令支持处理网页 URL 并自动进行清洗。

## Technical Tasks

- [x] 添加 `trafilatura` (或同类) 依赖到 `pyproject.toml`。
- [x] 在 `monoco/features/spike/core.py` 中实现内容抓取与清洗函数。
- [x] 增强 `monoco spike add` 的处理流程，使其能够区分 Git Repo 和普通 URL。
- [x] 编写清洗逻辑的单元测试。

## Review Comments

- [x] Self-Review
