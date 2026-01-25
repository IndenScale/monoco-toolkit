---
id: EPIC-0009
uid: baa5a5
type: epic
status: closed
stage: done
title: CICD 基建
created_at: '2026-01-13T13:21:48'
opened_at: '2026-01-13T13:21:48'
updated_at: '2026-01-15T13:25:55'
closed_at: '2026-01-15T13:25:55'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0009'
progress: 5/5
files_count: 0
parent: EPIC-0000
---

## EPIC-0009: CICD 基建

## Objective

建立 Monoco 生态的自动化构建、测试与多渠道发布流程，确保代码质量与分发效率。

## Acceptance Criteria

- [x] 自动化部署: 网站修改自动同步至 GitHub Pages。
- [x] 自动化测试: Pull Request 触发全量测试套件执行。
- [x] 自动化分发: Git Tag 触发 PyPI (Toolkit) 和 NPM (Kanban) 的发布。
- [x] 自动化校验: 所有 Issue 元数据与 Lint 检查通过。

## Technical Tasks

- [x] 配置 GitHub Pages 自动部署流程 (Next.js SSG)。
- [x] 构建 Toolkit 的 GitHub Action 发布流水线 (FEAT-0051)。
- [x] 构建 Kanban 的 GitHub Action 发布流水线 (FEAT-0058)。
- [x] 集成代码质量检查 (Lint, Type Check, Pytest) 到 CI。
- [x] 优化缓存策略，减少 CI 运行时间。

## Review Comments

- [x] Self-Review
