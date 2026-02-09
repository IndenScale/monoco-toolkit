---
id: FEAT-0197
uid: a62256
type: feature
status: open
stage: review
title: '实现 doc-extractor: 文档标准化与渲染工具'
created_at: '2026-02-09T21:03:26'
updated_at: '2026-02-10T00:34:14'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0197'
files:
- .gitignore
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Memos/cli_comparison_codex_kimi_gemini.md
- docs/zh/dingtalk-ngrok-guide.md
- docs/zh/dingtalk-stream-quickstart.md
- docs/zh/dingtalk-stream-setup.md
- docs/zh/doc-extractor.md
- src/monoco/features/doc_extractor/__init__.py
- src/monoco/features/doc_extractor/adapter.py
- src/monoco/features/doc_extractor/commands.py
- src/monoco/features/doc_extractor/extractor.py
- src/monoco/features/doc_extractor/index.py
- src/monoco/features/doc_extractor/models.py
- src/monoco/features/doc_extractor/resources/en/AGENTS.md
- src/monoco/features/doc_extractor/resources/en/skills/monoco_atom_doc_extract/SKILL.md
- src/monoco/features/doc_extractor/resources/zh/AGENTS.md
- src/monoco/features/doc_extractor/resources/zh/skills/monoco_atom_doc_extract/SKILL.md
- src/monoco/main.py
- tests/tools/test_doc_extractor.py
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-09T21:03:26'
isolation:
  type: branch
  ref: FEAT-0197-实现-doc-extractor-文档标准化与渲染工具
  created_at: '2026-02-09T21:03:53'
---

## FEAT-0197: 实现 doc-extractor: 文档标准化与渲染工具

## 目标

实现一个极简的文档标准化工具，将任意格式文档转换为统一的 PDF + WebP 页面序列，供 VLM 消费。

**设计原则**: 纯 CPU 运行，零模型依赖，只做格式转换和渲染。

## 目录结构设计

```
~/.monoco/blobs/
└── {sha256_of_original_file}/
    ├── meta.json           # 元数据
    ├── source.docx         # 原始文件（保留扩展名）
    ├── source.pdf          # 统一格式（PDF）
    └── pages/
        ├── 0.webp          # 第 0 页渲染图
        ├── 1.webp
        └── ...
```

## 处理流程

```
输入文件
    │
    ├──→ 压缩文件 (zip/tar.gz/rar/7z)
    │       └── 解压 → 扁平化处理每个文件
    │
    └──→ 单个文件
            │
            ├──→ 已是 PDF → 直接渲染
            │
            └──→ 其他格式 → 转换为 PDF → 渲染
                        (docx/pptx/xlsx/html/md/png/jpg...)
```

## 核心规格

### 1. 哈希计算
- 基于**原始文件内容**计算 SHA256
- 作为 blob 目录名

### 2. 格式转换
| 输入格式 | 转换工具 | 说明 |
|---------|---------|------|
| docx/pptx/xlsx | LibreOffice (soffice) | headless 模式 |
| html/md/txt | LibreOffice 或 pandoc | |
| png/jpg/jpeg | ImageMagick 或 Pillow | 转为单页 PDF |
| pdf | 无需转换 | 直接使用 |

### 3. 渲染参数
- DPI: 默认 150（可配置 100-300）
- 格式: WebP
- 质量: 默认 85
- 索引: 从 0 开始

### 4. 元数据 (meta.json)
```json
{
  "original_name": "report.docx",
  "original_hash": "a1b2c3d4...",
  "original_path": "/path/to/report.docx",
  "file_type": "docx",
  "category": "document",
  "page_count": 5,
  "dpi": 150,
  "quality": 85,
  "created_at": "2026-02-09T21:00:00Z",
  "source_archive": {
    "hash": "xyz789...",
    "name": "archive.zip",
    "inner_path": "report.docx"
  }
}
```

## CLI 接口

```bash
# 基本用法
monoco doc-extractor report.docx

# 指定参数
monoco doc-extractor report.pdf \
  --dpi 200 \
  --quality 90 \
  --pages 1-5,10,15-20

# 查看已提取的文档
monoco doc-extractor list
monoco doc-extractor show <hash>
monoco doc-extractor cat <hash>      # 查看 meta.json
monoco doc-extractor search "report" # 按名称/哈希/类型搜索
monoco doc-extractor source <hash>   # 查看来源档案信息

# 索引管理
monoco doc-extractor index rebuild   # 重建索引
monoco doc-extractor index stats     # 查看索引统计
monoco doc-extractor index clear     # 清空索引

# 清理缓存
monoco doc-extractor clean [--older-than 30d]
```

## 验收标准

- [x] 支持 PDF 渲染为 WebP 页面序列
- [x] 支持 docx/pptx/xlsx 转换为 PDF 后渲染
- [x] 支持图片 (png/jpg) 转为单页 PDF 后渲染
- [x] 支持压缩文件 (zip/tar.gz/rar/7z) 扁平化解压后处理
- [x] 基于原始文件哈希的缓存机制
- [x] 正确的目录结构和元数据生成
- [x] CLI 接口完整实现
- [x] 纯 CPU 运行，无模型依赖
- [x] 元数据追踪（来源档案、原始路径）
- [x] 全局索引和搜索功能

## 技术任务

- [x] 设计 BlobRef 数据模型
- [x] 实现文件类型检测和分类器
- [x] 实现 PDF 渲染器 (PyMuPDF)
- [x] 实现格式转换器 (LibreOffice 封装)
- [x] 实现压缩文件处理器
- [x] 实现缓存管理器
- [x] 实现 CLI 命令 (extract, list, show, cat, delete, clean)
- [x] 实现元数据追踪 (source_archive, original_path)
- [x] 实现全局索引 (BlobIndex)
- [x] 实现搜索命令 (search, source)
- [x] 实现索引管理命令 (index rebuild/stats/clear)
- [x] 编写单元测试
- [x] 编写使用文档

## 依赖

```toml
[dependencies]
PyMuPDF = "^1.25.0"      # PDF 渲染
Pillow = "^11.0.0"       # 图像处理
PyYAML = "^6.0"          # 索引文件
```

可选依赖（外部工具）：
- LibreOffice (soffice) - 格式转换
- p7zip - 7z/rar 解压

## Review Comments

<!-- Reviewer comments go here -->
