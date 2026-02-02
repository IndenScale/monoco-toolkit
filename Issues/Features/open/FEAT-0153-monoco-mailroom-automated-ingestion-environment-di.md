---
id: FEAT-0153
uid: mailroom_auto_01
type: feature
status: open
stage: review
title: 'Monoco Mailroom: Automated Ingestion & Environment Discovery'
created_at: '2026-02-02T00:00:00'
updated_at: '2026-02-02T09:13:39'
priority: high
parent: EPIC-0025
dependencies: []
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0153'
- mailroom
- automation
- discovery
files:
- monoco/core/ingestion/__init__.py
- monoco/core/ingestion/discovery.py
- monoco/core/ingestion/worker.py
- monoco/core/ingestion/watcher.py
- monoco/daemon/mailroom_service.py
- monoco/daemon/app.py
- tests/test_ingestion_discovery.py
- tests/test_ingestion_worker.py
- tests/test_ingestion_integration.py
- pyproject.toml
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
isolation:
  type: branch
  ref: feat/feat-0153-monoco-mailroom-automated-ingestion-environment-di
  created_at: '2026-02-02T09:07:47'
owner: IndenScale
---

## FEAT-0153: Monoco Mailroom: Automated Ingestion & Environment Discovery

## 1. 背景与目标
本 Feature 负责实现 Monoco Mailroom 的 **"自动化最后一公里"**。在具备了核心存储 (FEAT-0151) 和操作规范 (FEAT-0152) 后，我们需要在 Daemon 层实现自动化探测和非阻塞的处理流程。

## 2. 核心功能设计
- **Environment Discovery**: 动态探测系统 `soffice` 等工具的可用路径。
- **Auto-Ingestion Pipeline**: 当 Dropzone 监听到新二进制文件时，自动在后台启动转换进程。
- **Status Callback**: 转换完成后，更新 Artifact 元数据并触发后续的 Agent 调度。

## 3. 验收标准
- [x] **BinaryDiscovery**: 能够准确识别当前系统的办公套件及 PDF 处理引擎。
- [x] **Mailroom Worker**: 实现无头的自动化处理任务。
- [x] **Integration Test**: 检测到文件放入文件夹 -> 自动转换 -> 自动在 local manifest 记录。

## 4. 技术任务
- [x] 开发 `monoco/core/ingestion/discovery.py` 工具链探测模块。
- [x] 实现 `monoco/core/ingestion/worker.py` 处理转换流程调优。
- [x] 集成至 `monoco-daemon` 的事件循环。

## 5. Review Comments

### 5.1 实现概述

本 Feature 实现了 Monoco Mailroom 的自动化摄取系统，包含以下核心组件：

#### 5.1.1 Environment Discovery (`discovery.py`)
- 自动探测 LibreOffice (soffice)、Pandoc、PDF 工具 (pdftotext, pdftohtml)
- 支持工具优先级排序，选择最佳可用工具
- 提供能力查询接口 (has_capability, get_best_tool)

#### 5.1.2 Conversion Worker (`worker.py`)
- 异步转换处理，支持并发控制 (Semaphore)
- 支持多种文档格式：DOCX, PDF, ODT, XLSX, PPTX
- 提供进度回调和完成回调机制
- 超时控制和错误处理

#### 5.1.3 Dropzone Watcher (`watcher.py`)
- 基于 watchdog 的文件系统监控
- 自动检测新文件并触发转换流程
- 集成 ArtifactManager 自动注册转换后的产物
- 提供事件广播机制 (IngestionEvent)

#### 5.1.4 Mailroom Service (`mailroom_service.py`)
- Daemon 服务集成
- 提供 REST API 端点 (/api/v1/mailroom/status, /api/v1/mailroom/discover)
- SSE 事件广播支持

#### 5.1.5 Daemon 集成 (`app.py`)
- 在 Daemon 启动时自动启动 Mailroom 服务
- 在 Daemon 关闭时优雅停止服务

### 5.2 测试覆盖
- 单元测试：`test_ingestion_discovery.py` (10 个测试)
- 单元测试：`test_ingestion_worker.py` (11 个测试)
- 集成测试：`test_ingestion_integration.py` (8 个测试)
- 所有测试通过

### 5.3 API 端点
- `GET /api/v1/mailroom/status` - 获取服务状态、能力和统计信息
- `POST /api/v1/mailroom/discover` - 触发环境重新发现

### 5.4 使用方式
```python
# 获取服务状态
curl http://localhost:8000/api/v1/mailroom/status

# 触发重新发现
curl -X POST http://localhost:8000/api/v1/mailroom/discover
```

文件放入 `{workspace}/.monoco/dropzone/` 后将自动触发转换流程。
