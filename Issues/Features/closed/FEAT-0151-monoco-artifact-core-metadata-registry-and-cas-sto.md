---
id: FEAT-0151
uid: art_core_01
type: feature
status: closed
stage: done
title: 'Monoco Artifact Core: Metadata Registry and CAS Storage'
created_at: '2026-02-02T00:00:00'
updated_at: '2026-02-02T09:05:23'
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
files:
- monoco/core/artifacts/__init__.py
- monoco/core/artifacts/models.py
- monoco/core/artifacts/manager.py
- tests/core/artifacts/__init__.py
- tests/core/artifacts/test_artifact_manager.py
criticality: medium
closed_at: '2026-02-02T09:05:23'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0151-monoco-artifact-core-metadata-registry-and-cas-sto
  created_at: '2026-02-02T09:00:38'
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
- [x] **ArtifactManager Python 类**: 支持 `store()`, `get()`, `list()`, `delete()` 操作。
- [x] **CAS Implementation**: 实现基于文件内容 SHA256 Hash 的文件去重存储。
- [x] **Manifest Management**: 增删产物时自动原子化地更新 `.monoco/artifacts/manifest.jsonl`。
- [x] **Symlink Logic**: 确保项目本地引用正确指向全局物理存储。

## 4. 技术任务
- [x] 设计并定义 `ArtifactMetadata` 数据模型。
- [x] 开发 `monoco/core/artifacts/manager.py` 核心类。
- [x] 实现基于文件 Hash 的全局物理路径计算算法。
- [x] 实现 `manifest.jsonl` 的追加与解析逻辑。
- [x] 编写核心功能的单元测试。

## 5. Review Comments

### 实现总结

#### 新增文件
1. **monoco/core/artifacts/models.py**
   - `ArtifactMetadata`: Pydantic 数据模型，包含 artifact 完整元数据
   - `ArtifactSourceType`: 枚举（generated, uploaded, imported, derived）
   - `ArtifactStatus`: 枚举（active, archived, expired, deleted）
   - `compute_content_hash()`: SHA256 内容哈希计算
   - `compute_file_hash()`: 文件哈希计算

2. **monoco/core/artifacts/manager.py**
   - `ArtifactManager`: 核心管理类
   - 方法：`store()`, `store_file()`, `get()`, `get_content()`, `list()`, `update()`, `delete()`
   - CAS 存储路径：`{global_store}/{hash[:2]}/{hash[2:4]}/{hash}`
   - 原子化 manifest 更新
   - 软删除和硬删除支持
   - 过期清理机制
   - Symlink 创建功能

3. **tests/core/artifacts/test_artifact_manager.py**
   - 26 个单元测试，全部通过
   - 覆盖：CRUD、CAS 去重、manifest 持久化、并发存储、过期清理等

#### 关键特性
- **CAS 去重**: 相同内容只存储一次
- **原子化操作**: manifest 更新使用临时文件+rename 保证原子性
- **线程安全**: 使用 RLock 保护共享状态
- **双层存储**: 全局物理存储 + 项目本地 manifest 注册表
- **生命周期管理**: active -> expired/archived -> deleted

### 测试状态
```
26 passed, 103 warnings in 0.05s
```
所有验收标准已完成并通过测试。
