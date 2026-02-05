---
# ===== 身份标识 =====
id: "UNKNOWN"                       # 必填：全局唯一标识符（kebab-case）
title: "UNKNOWN"                    # 必填：文章标题

# ===== 来源信息 =====
source: "UNKNOWN"                   # 必填：原始 URL（不知道填 UNKNOWN）
date: "UNKNOWN"                     # 必填：发布日期 ISO 8601（不知道填 UNKNOWN）
author: "UNKNOWN"                   # 可选：作者

# ===== 类型分类 =====
# 必填：article | paper | report | doc | blog | video
type: "UNKNOWN"

# ===== 国际化 =====
language: "UNKNOWN"                 # 可选：en | zh | ja
translations:                       # 可选：翻译版本映射
  # zh: "./zh/UNKNOWN.md"

# ===== 知识治理 =====
company: "UNKNOWN"                  # 可选：所属公司/组织
domain:                             # 可选：领域分类（数组）
  # - "UNKNOWN"
tags:                               # 可选：自由标签（数组）
  # - "UNKNOWN"

# ===== 关联知识 =====
related_repos:                      # 可选：关联的代码仓库
  # - "UNKNOWN"
related_articles:                   # 可选：关联的其他文章
  # - "UNKNOWN"

# ===== 内容摘要（用于 RAG）=====
summary: |
  UNKNOWN
---

# 正文从这里开始

## 填写指南

1. **UNKNOWN 占位符**：所有字段默认 UNKNOWN，不确定就保留 UNKNOWN
2. **必填字段**：id, title, source, date, type 必须替换为实际值或保持 UNKNOWN
3. **可选字段**：不知道就保留 UNKNOWN 或删除整行
4. **后续补充**：运行 `monoco spike lint` 会列出所有 UNKNOWN 字段

## 内容规范

- 保持原始内容完整性
- 可以添加自己的笔记和批注，使用引用格式：
  > 我的批注：这个观点很有启发性
- 使用相对路径引用同目录下的图片
  ![alt](./images/diagram.png)

## i18n 翻译

如需创建翻译版本：
1. 创建 `zh/` 子目录（对应 language 代码）
2. 复制本文档到 `zh/article-name.md`
3. 更新 `language` 字段为 "zh"
4. 更新主文档的 `translations.zh` 指向翻译文件
