---
id: FEAT-0153
uid: mailroom_auto_01
type: feature
status: open
stage: draft
title: 'Monoco Mailroom: Automated Ingestion & Environment Discovery'
owner: IndenScale
parent: EPIC-0025
priority: high
created_at: '2026-02-02'
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0153'
- mailroom
- automation
- discovery
---

## FEAT-0153: Monoco Mailroom: Automated Ingestion & Environment Discovery

## 1. 背景与目标
本 Feature 负责实现 Monoco Mailroom 的 **“自动化最后一公里”**。在具备了核心存储 (FEAT-0151) 和操作规范 (FEAT-0152) 后，我们需要在 Daemon 层实现自动化探测和非阻塞的处理流程。

## 2. 核心功能设计
- **Environment Discovery**: 动态探测系统 `soffice` 等工具的可用路径。
- **Auto-Ingestion Pipeline**: 当 Dropzone 监听到新二进制文件时，自动在后台启动转换进程。
- **Status Callback**: 转换完成后，更新 Artifact 元数据并触发后续的 Agent 调度。

## 3. 验收标准
- [ ] **BinaryDiscovery**: 能够准确识别当前系统的办公套件及 PDF 处理引擎。
- [ ] **Mailroom Worker**: 实现无头的自动化处理任务。
- [ ] **Integration Test**: 检测到文件放入文件夹 -> 自动转换 -> 自动在 local manifest 记录。

## 4. 技术任务
- [ ] 开发 `monoco/core/ingestion/discovery.py` 工具链探测模块。
- [ ] 实现 `monoco/core/ingestion/worker.py` 处理转换流程调优。
- [ ] 集成至 `monoco-daemon` 的事件循环。

## 5. Review Comments
- [ ] 待评审。
