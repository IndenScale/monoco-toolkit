---
id: FEAT-0151
uid: art_core_01
type: feature
status: open
stage: doing
title: 'Monoco Artifact Core: Metadata Registry and CAS Storage'
created_at: '2026-02-02T00:00:00'
updated_at: '2026-02-02T09:00:38'
priority: high
parent: EPIC-0025
dependencies: []
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0151'
- artifacts
- storage
- metadata
files: []
criticality: medium
owner: IndenScale
---

## FEAT-0151: Monoco Artifact Core: Metadata Registry and CAS Storage

## 1. 背景与目标
为了支持 Monoco 处理多模态数据（如文档截图、生成式 UI 等非源码资产），需要建立一套标准化的 **Artifacts（产物）** 管理系统。本 Feature 负责实现核心资产的 CURD 逻辑、基于内容寻址（CAS）的存储机制以及基于 `manifest.jsonl` 的元数据注册表。

## 2. 核心功能设计
- **Hybrid Storage**: 实现全局存储池 (`~/.monoco/artifacts`) 与项目本地引用 (`./.monoco/artifacts`) 的双层架构。
- **Metadata Registry**: 在项目目录下维护 `manifest.jsonl`，记录每个 Artifact 的 ID、Hash、来源类型、创建时间及过期策略。
- **CRUD 接口**: 提供统一的 Python API 用于创建、读取、更新和删除（清理）产物。

## 3. 验收标准
- [ ] **ArtifactManager Python 类**: 支持 `store()`, `get()`, `list()`, `delete()` 操作。
- [ ] **CAS Implementation**: 实现基于文件内容 SHA256 Hash 的文件去重存储。
- [ ] **Manifest Management**: 增删产物时自动原子化地更新 `.monoco/artifacts/manifest.jsonl`。
- [ ] **Symlink Logic**: 确保项目本地引用正确指向全局物理存储。

## 4. 技术任务
- [ ] 设计并定义 `ArtifactMetadata` 数据模型。
- [ ] 开发 `monoco/core/artifacts/manager.py` 核心类。
- [ ] 实现基于文件 Hash 的全局物理路径计算算法。
- [ ] 实现 `manifest.jsonl` 的追加与解析逻辑。
- [ ] 编写核心功能的单元测试。

## 5. Review Comments
- [ ] 待评审。
