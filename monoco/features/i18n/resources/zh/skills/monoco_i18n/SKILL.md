---
name: monoco-i18n
description: 文档国际化质量控制。确保多语言文档保持同步。
type: standard
version: 1.0.0
---

# 文档国际化

管理 Monoco 项目文档的国际化。

## 概述

I18n 功能提供:

- **自动扫描**缺失的翻译
- **标准化结构**用于多语言文档
- **质量控制**以维护文档一致性

## 核心命令

### 扫描缺失的翻译

```bash
monoco i18n scan
```

扫描项目中的 markdown 文件并报告缺失的翻译。

**输出**:

- 列出没有对应翻译的源文件
- 显示缺少哪些目标语言
- 遵循 `.gitignore` 和默认排除规则

## 配置

I18n 设置在 `.monoco/config.yaml` 中配置:

```yaml
i18n:
  source_lang: en # 源语言代码
  target_langs: # 目标语言代码
    - zh
    - ja
```

## 文档结构

### 根文件（后缀模式）

对于项目根目录中的文件:

- 源文件: `README.md`
- 中文: `README_ZH.md`
- 日文: `README_JA.md`

### 子目录文件（目录模式）

对于 `docs/` 或其他目录中的文件:

```
docs/
├── en/
│   ├── guide.md
│   └── api.md
├── zh/
│   ├── guide.md
│   └── api.md
└── ja/
    ├── guide.md
    └── api.md
```

## 排除规则

以下内容会自动从 i18n 扫描中排除:

- `.gitignore` 模式（自动遵循）
- `.references/` 目录
- 构建产物（`dist/`, `build/`, `node_modules/`）
- `Issues/` 目录

## 最佳实践

1. **先创建英文版**: 首先用源语言编写文档
2. **遵循命名约定**: 使用适当的模式（后缀或目录）
3. **定期运行扫描**: 使用 `monoco i18n scan` 验证覆盖率
4. **提交所有语言**: 将翻译保存在版本控制中

## 工作流程

1. 用源语言（如英语）编写文档
2. 按照命名约定创建翻译文件
3. 运行 `monoco i18n scan` 验证所有翻译是否存在
4. 修复扫描报告的任何缺失翻译
