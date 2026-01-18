---
name: monoco-spike
description: 管理用于研究和学习的外部参考仓库。提供对精选代码库的只读访问。
---

# Spike (研究)

在 Monoco 项目中管理外部参考仓库。

## 概述

Spike 功能允许你:

- **添加外部仓库**作为只读参考
- **同步仓库内容**到本地 `.references/` 目录
- **访问精选知识**而不修改源代码

## 核心命令

### 添加仓库

```bash
monoco spike add <url>
```

将外部仓库添加为参考。仓库将被克隆到 `.references/<name>/`，其中 `<name>` 从仓库 URL 派生。

**示例**:

```bash
monoco spike add https://github.com/example/awesome-project
# 可在以下位置访问: .references/awesome-project/
```

### 同步仓库

```bash
monoco spike sync
```

从 `.monoco/config.yaml` 下载或更新所有配置的 spike 仓库。

### 列出 Spikes

```bash
monoco spike list
```

显示所有配置的 spike 仓库及其同步状态。

## 配置

Spike 仓库在 `.monoco/config.yaml` 中配置:

```yaml
project:
  spike_repos:
    awesome-project: https://github.com/example/awesome-project
    another-ref: https://github.com/example/another-ref
```

## 最佳实践

1. **只读访问**: 永远不要编辑 `.references/` 中的文件。将它们视为外部知识。
2. **精选选择**: 只添加高质量、相关的仓库。
3. **定期同步**: 定期运行 `monoco spike sync` 以获取更新。
4. **提交配置**: 将 spike 仓库 URL 添加到版本控制以保持团队一致性。

## 使用场景

- **从示例中学习**: 研究架构良好的代码库
- **API 参考**: 在本地保存框架文档
- **模式库**: 维护设计模式集合
- **竞品分析**: 参考类似项目
