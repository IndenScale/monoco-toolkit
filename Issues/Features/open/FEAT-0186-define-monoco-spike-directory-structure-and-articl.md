---
id: FEAT-0186
uid: 6e422d
type: feature
status: open
stage: review
title: Define monoco spike directory structure and article template
created_at: '2026-02-06T04:55:44'
updated_at: '2026-02-06T05:06:12'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0186'
files:
- .claudeignore
- .gitignore
- .prettierignore
- .references/articles/template.md
- CLAUDE.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Memos/2026-02-06_OpenAI_Frontier_Analysis.md
- README.md
- monoco/cli/project.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-06T04:55:44'
isolation:
  type: branch
  ref: FEAT-0186-define-monoco-spike-directory-structure-and-articl
  created_at: '2026-02-06T05:02:54'
---

## FEAT-0186: Define monoco spike directory structure and article template

## Objective

定义 monoco spike 的完整目录结构规范，支持两种知识类型：

1. **repos** - Git 仓库（完整克隆，代码参考）
2. **articles** - 知识文章（带 front matter 元数据治理）

通过 `monoco init` 注入文章模板到 `.references/articles/template.md`。

## Acceptance Criteria

- [x] 定义 `.references/` 层级目录结构规范
- [x] 定义 `repos/` 子目录结构和命名约定
- [x] 定义 `articles/` 子目录结构和命名约定
- [x] 设计 article front matter 模板（YAML 字段规范）
- [x] `monoco init` 命令注入模板到 `.references/articles/template.md`
- [x] 更新 CLAUDE.md 文档中的 Spike 章节

## Technical Tasks

### 1. 目录结构设计

- [x] 定义 `.references/` 根目录结构：
  ```
  .references/
  ├── repos/           # Git 仓库类型
  └── articles/        # 知识文章类型
      └── template.md  # 文章模板（由 monoco init 注入）
  ```

### 2. repos/ 规范

- [x] 命名规则：使用仓库名称小写，kebab-case
- [x] 每个 repo 为完整 git clone（保留 .git 历史）
- [x] 示例：`repos/kimi-cli/`, `repos/claude-code/`

### 3. articles/ 规范

- [x] 二级目录按来源组织（小写）：`articles/openai/`, `articles/anthropic/`
- [x] 文章文件使用 kebab-case：`introducing-frontier.md`
- [x] i18n 支持：`articles/openai/zh/` 子目录存放翻译
- [x] 所有文章必须包含 front matter

### 4. Front Matter 模板设计

- [x] 模板字段默认值使用 `UNKNOWN`，允许不确定时保留占位
- [x] 必需字段：`id`, `title`, `source`, `date`, `type`
- [x] 可选字段：`author`, `tags`, `summary`, `related`
- [x] i18n 字段：`language`, `translations`
- [x] 治理字段：`domain`, `company`

### 5. monoco init 集成

- [x] 修改 `monoco init` 命令
- [x] 创建 `.references/articles/` 目录（如果不存在）
- [x] 注入 `template.md` 到 `.references/articles/template.md`

### 6. 文档更新

- [x] 更新 CLAUDE.md Spike 章节，添加目录结构说明
- [x] 添加 front matter 字段说明

## Design

### 目录结构规范

```
.references/
├── repos/                 # Git 仓库类型（完整 clone）
│   ├── kimi-cli/
│   ├── claude-code/
│   └── ...
└── articles/              # 知识文章类型
    ├── template.md        # 文章模板（monoco init 注入）
    ├── openai/            # 按来源组织
    │   ├── introducing-frontier.md
    │   └── zh/
    │       └── introducing-frontier.md
    └── anthropic/
        └── ...
```

### 命名规范

- 全部小写，kebab-case
- 目录：`openai/`, `kimi-cli/`
- 文件：`introducing-frontier.md`

### Front Matter 字段

| 类别 | 字段 | 说明 | 必需 |
| ---- | ---- | ---- | ---- |
| 身份 | `id` | 全局唯一标识符（kebab-case） | ✓ |
| 身份 | `title` | 文章标题 | ✓ |
| 来源 | `source` | 原始 URL | ✓ |
| 来源 | `date` | 发布日期（ISO 8601） | ✓ |
| 来源 | `author` | 作者 | - |
| 类型 | `type` | article / paper / report / doc / blog | ✓ |
| i18n | `language` | 语言代码：en / zh / ja | - |
| i18n | `translations` | 翻译版本映射 | - |
| 治理 | `company` | 所属公司/组织 | - |
| 治理 | `domain` | 领域分类（数组） | - |
| 治理 | `tags` | 自由标签（数组） | - |
| 关联 | `related_repos` | 关联的 repos 名称 | - |
| 关联 | `related_articles` | 关联的 articles id | - |
| 摘要 | `summary` | 内容摘要（用于 RAG） | - |

### lint 规则（未来扩展）

`monoco spike lint` 检查项：

1. **结构检查**：`repos/`、`articles/`、`articles/template.md` 存在
2. **命名规范**：目录和文件名为小写 kebab-case
3. **Front Matter**：所有 article 文件必须包含 YAML front matter
4. **UNKNOWN 检查**：列出所有值为 UNKNOWN 的字段，提示用户补充
5. **唯一性**：`id` 字段全局唯一
6. **链接有效性**：`related_repos` 和 `related_articles` 指向存在的内容

## Review Comments

### Self-Review

- [x] 目录结构规范已定义完整
- [x] 文章模板包含所有必需字段
- [x] monoco init 正确注入模板
- [x] CLAUDE.md 文档已更新
