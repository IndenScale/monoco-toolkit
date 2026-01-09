---
name: i18n-scan
description: 文档质量控制技能。负责文档的国际化 (i18n) 检查、结构完整性验证和链接有效性扫描。
---

# 文档维护 (Documentation Maintenance)

此技能定义了 Monoco 项目文档的维护标准和自动化检查规则。文档是 Monoco 的 "第一类公民"。

## 核心标准 (Core Standards)

### 1. 国际化 (i18n) 结构

Monoco 采用混合式的 i18n 文件组织策略，以适应不同类型的文件：

- **根目录文件 (Root Files)**: 使用 **后缀模式**。

  - 原件: `README.md`
  - 中文: `README_ZH.md` (注意是大写 `ZH` 或 `CN`，保持项目统一)
  - 其他: `README_JA.md`, etc.

- **文档目录 (Documentation Directories)**: 使用 **子目录模式**。
  - 原件: `docs/guide/intro.md`
  - 中文: `docs/guide/zh/intro.md` (在同级目录下建立 `zh/` 文件夹)
  - 此模式能保持目录结构清晰，避免文件列表过度膨胀。

### 2. 忽略规则 (Exclusion)

以下路径应排除在检查范围之外：

- `.gitignore` 中列出的文件。
- `.reference/` 目录。
- 生成的构建产物 (`dist/`, `build/`).

## 自动化检查 (Checklists)

Agent 或 CI 工具应能够执行以下检查：

### 1. i18n 覆盖率检查 (`i18n-check`)

- **目标**: 确保所有核心文档都有对应的中文翻译。
- **逻辑**:
  1. 扫描所有 Markdown 文件。
  2. 如果文件名是 `README.md`，检查同级目录是否存在 `README_ZH.md`。
  3. 如果是其他 `.md` 文件且不在 `zh/` 目录下，检查其同级 `zh/` 目录下是否存在同名文件。
  4. 报告缺失翻译的文件列表。
- **工具支持**: 计划在未来版本中支持 `monoco check i18n` 命令。

### 2. 链接有效性 (Link Rot) (Planned)

- **目标**: 确保文档中的 `[Link](url)` 和 `[[WikiLink]]` 指向有效目标。
- **逻辑**: 解析 Markdown AST，提取链接，验证 HTTP 状态码或文件存在性。

## 维护者指南

- **添加新文档**: 在创建英文/主语言文档的同时，创建一个占位符或 TODO 状态的中文文档，以避免 `i18n-check` 报错（或者容忍报错作为提醒）。
- **重构**: 移动文档时，务必同步移动其翻译版本。
