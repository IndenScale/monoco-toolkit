# Monoco Kanban

Monoco Kanban 是 Monoco 生态系统的图形化客户端。它旨在为基于 **"Task as Code"** 哲学的项目管理提供极速、丝滑的现代化体验（类似 Linear），同时保持 **Git-Native** 的去中心化特质。

## 核心理念

1.  **Git 即真理 (Git as Truth)**: 所有的任务状态（ToDo/Doing/Done）都直接对应文件系统中的 Markdown 文件变动。没有隐藏的数据库。
2.  **本地优先 (Local First)**: 利用 Tauri 构建，操作零延迟。所有变更先写入本地文件，异步通过 Git 同步。
3.  **无缝集成 (Seamless)**: 它是对 `monoco` CLI 和 Typedown 语言的可视化封装，填补了极客工具与企业级管理之间的鸿沟。

## 文档导航

请按顺序阅读以下文档以理解设计决策：

1.  [**产品愿景**](docs/zh/00-vision.md): 为什么我们需要一个独立的客户端？它解决了什么问题？
2.  [**技术架构**](docs/zh/01-architecture.md): 基于 Tauri + React 的 Monorepo 架构设计。
3.  [**身份与权限**](docs/zh/02-identity.md): 基于 Git 物理身份与 SaaS 策略叠加的双层权限模型。

## 快速开始

_(开发中，暂无构建指令)_
