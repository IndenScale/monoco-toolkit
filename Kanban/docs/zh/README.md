# Monoco Kanban 文档

本文档目录包含 Monoco Kanban 系统的核心设计与规范。

## 目录索引

1. **[00-vision.md](./00-vision.md)**: 产品愿景

   - 背景与痛点
   - 核心定位
   - 关键特性

2. **[01-architecture.md](./01-architecture.md)**: 技术架构

   - Core + Shells 分层架构
   - 核心层与适配层
   - 状态同步机制 (Toolkit Daemon)

3. **[02-identity.md](./02-identity.md)**: 身份与权限

   - 物理层 (Git Identity)
   - 策略层 (SaaS RBAC)

4. **[03-lifecycle.md](./03-lifecycle.md)**: 任务生命周期
   - 物理三态 (Backlog/Open/Closed)
   - 逻辑五态 (Todo/Doing/Review/Done)
   - 状态机流转规则

## 关联文档

- **Toolkit Issue Manual**: `../../Toolkit/docs/zh/issue/manual.md` (命令行工具使用手册)
