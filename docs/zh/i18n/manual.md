# Monoco i18n 系统用户手册

Monoco 将国际化 (i18n) 视为项目的"一等公民"。本手册介绍了 Monoco i18n 系统的设计理念、文件组织规范以及维护工具的使用方法。

## 核心理念

为了确保知识资产的普适性，Monoco 要求核心文档必须具备多语言支持。我们的 i18n 系统旨在通过轻量级的规范和自动化工具，协助开发者维护文档的多语言同步。

## 文件组织规范

Monoco 采用混合式的文件组织策略，以适应不同层级文档的需求。

### 1. 后缀模式 (Suffix Pattern)

适用于项目根目录下的关键文件。通过文件名后缀区分语言版本。

- **适用范围**: `Root Directory`
- **命名规则**: `{Filename}_{LANG}.{ext}` (其中 `{LANG}` 必须大写)
- **示例**:
  - `README.md` (源文件，默认为英语)
  - `README_ZH.md` (中文版)

### 2. 子目录模式 (Subdirectory Pattern)

适用于文档目录下的结构化文档。通过同级目录下的语言子文件夹管理翻译。

- **适用范围**: `docs/`, `arch/` 等文档目录
- **命名规则**: `{dir}/{LANG}/{filename}` (其中 `{LANG}` 为小写目录名)
- **示例**:
  - 源文件: `docs/guide/intro.md`
  - 中文版: `docs/guide/zh/intro.md`

## 命令行工具

Monoco Toolkit 提供了开箱即用的 i18n 维护命令。

### coverage 扫描 (`scan`)

`scan` 命令用于检查项目文档的翻译覆盖率。它会扫描所有源文件，并根据上述规范查找是否存在对应的翻译文件。

**基本用法**:

```bash
monoco i18n scan
```

**参数说明**:

- `--root {path}`: 指定扫描的根目录。默认为项目根目录。

**输出解读**:

扫描结束后，控制台将输出一份详细报告：

- **Source File**: 未找到对应翻译的源文件路径。
- **Missing Languages**: 缺失的具体语言版本 (如 `ZH`)。
- **Expected Paths**: 按照规范，系统期望找到翻译文件的路径。

**示例输出**:

```text
Scanning i18n coverage in /path/to/project...
Target Languages: ZH (Source: EN)

i18n Availability Report
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Source File      ┃ Missing Languages ┃ Expected Paths               ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ README.md        │ ZH                │ README_ZH.md                 │
│ docs/foo.md      │ ZH                │ docs/zh/foo.md               │
└──────────────────┴───────────────────┴──────────────────────────────┘

I18N STATUS
Total Source Files: 10
Coverage: 80.0%
```

## 配置

i18n 的行为可以通过项目配置文件 `monoco.yaml` (如有) 或全局配置进行微调。

(注：系统默认源语言为 EN，目标语言包含 ZH)

## 常见问题

### Q: 为什么我的翻译文件没有被识别？

A: 请检查文件名大小写是否严格符合规范。

- 根目录后缀模式要求大写 (e.g. `_ZH`)。
- 子目录模式要求目录名小写 (e.g. `/zh/`)。

### Q: 如何忽略某些不需要翻译的文件？

A: 系统自动遵循 `.gitignore` 规则。此外，构建产物目录 (如 `dist/`) 和非文档目录会被自动排除。
