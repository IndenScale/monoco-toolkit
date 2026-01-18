---
name: monoco-core
description: Monoco Toolkit 的核心技能。提供项目初始化、配置管理和工作空间管理的基础命令。
---

# Monoco 核心

Monoco Toolkit 的核心功能和命令。

## 概述

Monoco 是一个开发者生产力工具包，提供:

- **项目初始化**: 标准化的项目结构
- **配置管理**: 全局和项目级别的配置
- **工作空间管理**: 多项目设置

## 核心命令

### 项目设置

- **`monoco init`**: 初始化新的 Monoco 项目
  - 创建 `.monoco/` 目录及默认配置
  - 设置项目结构（Issues/, .references/ 等）
  - 生成初始文档

### 配置管理

- **`monoco config`**: 管理配置
  - `monoco config get <key>`: 查看配置值
  - `monoco config set <key> <value>`: 更新配置
  - 支持全局（`~/.monoco/config.yaml`）和项目（`.monoco/config.yaml`）作用域

### Agent 集成

- **`monoco sync`**: 与 agent 环境同步
  - 将系统提示注入到 agent 配置文件（GEMINI.md, CLAUDE.md 等）
  - 分发 skills 到 agent 框架目录
  - 遵循 `i18n.source_lang` 的语言配置

- **`monoco uninstall`**: 清理 agent 集成
  - 从 agent 配置文件中移除托管块
  - 清理已分发的 skills

## 配置结构

配置以 YAML 格式存储在:

- **全局**: `~/.monoco/config.yaml`
- **项目**: `.monoco/config.yaml`

关键配置段:

- `core`: 编辑器、日志级别、作者
- `paths`: 目录路径（issues, spikes, specs）
- `project`: 项目元数据、spike repos、工作空间成员
- `i18n`: 国际化设置
- `agent`: Agent 框架集成设置

## 最佳实践

1. **优先使用 CLI 命令**，而不是手动编辑文件
2. **配置更改后运行 `monoco sync`** 以更新 agent 环境
3. **将 `.monoco/config.yaml` 提交到版本控制**，保持团队一致性
4. **保持全局配置最小化** - 大多数设置应该是项目特定的
