---
id: FEAT-0196
uid: 239aca
type: feature
status: closed
stage: done
title: Agent resources 添加文档智能 skill
created_at: '2026-02-08T20:53:57'
updated_at: '2026-02-08T21:02:24'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0196'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- src/monoco/features/agent/resources/zh/skills/doc_convert/SKILL.md
criticality: medium
solution: implemented
opened_at: '2026-02-08T20:53:57'
closed_at: '2026-02-08T21:02:24'
isolation:
  type: branch
  ref: FEAT-0196-agent-resources-添加文档智能-skill
  created_at: '2026-02-08T20:54:01'
---

## FEAT-0196: Agent resources 添加文档智能 skill

## Objective
在 Agent resources 中添加文档智能 skill，指导 Agent 使用 LibreOffice 同步转换文档为 PDF，然后利用 Vision 能力分析。

不依赖 GPU 服务（如 MinerU），简化架构。

## Acceptance Criteria
- [x] 创建 doc_convert skill 文件
- [x] Skill 包含 LibreOffice 转换命令
- [x] Skill 说明 Vision 分析流程

## Technical Tasks
- [x] 创建 `src/monoco/features/agent/resources/zh/skills/doc_convert/SKILL.md`
- [x] 定义文档转换流程和最佳实践

## Review Comments

- **Self Review**: Skill 内容完整，包含转换命令、支持格式、最佳实践
- **架构验证**: 纯 Skill 方案，无后端代码，符合简化设计目标
