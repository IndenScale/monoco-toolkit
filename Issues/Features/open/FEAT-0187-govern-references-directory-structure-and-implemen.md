---
id: FEAT-0187
uid: d0b994
type: feature
status: open
stage: draft
title: Govern .references directory structure and implement spike lint
created_at: '2026-02-06T05:08:50'
updated_at: '2026-02-06T05:08:50'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0187'
files:
- .references/repos/
- .references/articles/
- .references/articles/ivan-zhao/*.md
- .references/articles/feng-ruohang/*.md
- .references/articles/liao-haibo/*.md
- .references/articles/antigravity/*.md
- .references/articles/cursor/*.md
- .references/articles/openai/*.md
- .references/articles/openai/zh/*.md
- monoco/features/spike/lint.py
- monoco/features/spike/commands.py
- monoco/features/spike/core.py
- CLAUDE.md
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-06T05:08:50'
---

## FEAT-0187: Govern .references directory structure and implement spike lint

## Objective

治理现有的 `.references/` 目录，使其符合 FEAT-0186 定义的规范结构，并实现 `monoco spike lint` 命令进行自动化检查。

当前问题：
- 所有 Git 仓库都在 `.references/` 根目录，未放入 `repos/` 子目录
- 缺少 `monoco spike lint` 命令实现
- 文章可能缺少 front matter 或字段不完整

## Acceptance Criteria

- [x] 现有 Git 仓库迁移到 `.references/repos/` 目录下
- [x] `.references/` 根目录只保留 `repos/` 和 `articles/` 两个子目录
- [x] 实现 `monoco spike lint` 命令
- [x] lint 检查：目录结构合规性
- [x] lint 检查：文章 front matter 完整性
- [x] lint 检查：必填字段非 UNKNOWN (WARNING)
- [x] lint 检查：id 全局唯一性
- [x] 更新 CLAUDE.md 添加 lint 命令文档
- [x] 迁移剩余目录到 `articles/`
- [x] 为所有文章添加 front matter

## Technical Tasks

### 1. 目录治理

- [ ] 创建 `.references/repos/` 目录（如果不存在）
- [ ] 识别当前 `.references/` 根目录下的所有 Git 仓库
- [ ] 迁移仓库到 `repos/` 子目录（保持命名规范：kebab-case）
- [ ] 更新 `.gitignore` 确保 `repos/` 被正确忽略

### 2. monoco spike lint 实现

- [ ] 在 `monoco/features/spike/` 添加 `lint.py` 模块
- [ ] 实现结构检查：验证 `repos/`、`articles/`、`template.md` 存在
- [ ] 实现命名规范检查：目录和文件名为小写 kebab-case
- [ ] 实现 front matter 检查：所有 article 必须包含 YAML front matter
- [ ] 实现 UNKNOWN 检查：列出所有值为 UNKNOWN 的字段
- [ ] 实现唯一性检查：验证 `id` 字段全局唯一
- [ ] 实现链接检查：验证 `related_repos` 和 `related_articles` 指向存在的内容
- [ ] 在 `monoco/features/spike/commands.py` 添加 `lint` 子命令

### 3. 文档更新

- [ ] 更新 CLAUDE.md Spike 章节，添加 `monoco spike lint` 命令说明
- [ ] 添加 lint 规则说明表格

## Review Comments
