---
id: FEAT-0127
uid: 3f9296
type: feature
status: open
stage: doing
title: Implement Core Resource Package
created_at: '2026-01-31T17:36:28'
updated_at: 2026-01-31 17:37:09
parent: EPIC-0023
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0023'
- '#FEAT-0127'
files: []
criticality: high
opened_at: '2026-01-31T17:36:28'
isolation:
  type: branch
  ref: feat/feat-0127-implement-core-resource-package
  path: null
  created_at: '2026-01-31T17:37:09'
---

## FEAT-0127: Implement Core Resource Package

## Objective
实现 `monoco.core.resource` 包，提供统一的资源发现、加载和提取 API。
这是 Package-Based Architecture 的核心基础设施，用于让 Monoco Kernel 能够标准地访问分布在各个 Feature 模块中的静态资源（Prompts, Rules, Skills 等）。

## Acceptance Criteria
- [ ] 提供 `ResourceManager` 类，支持基于包路径（如 `monoco.features.agent`）的资源访问。
- [ ] 支持标准的资源目录结构解析：`resources/{type}/{lang}/...`。
- [ ] 提供资源遍历 API，能够列出指定类型的所有资源文件。
- [ ] 提供资源提取 API，支持将资源内容复制或软链接到目标目录。
- [ ] 包含完整的单元测试，覆盖常见场景（文件存在、文件缺失、语言回退等）。

## Technical Tasks
- [x] 初始化 `monoco/core/resource` 包结构
- [x] 实现 `ResourceFinder`：利用 `importlib.resources` (Python 3.9+) 遍历包资源
- [x] 实现 `ResourceManager`：封装上层业务逻辑（语言过滤、类型过滤）
- [x] 编写单元测试 `tests/core/test_resource.py`

## Review Comments
- Initial creation.
