# Doc-Extractor: 文档标准化与渲染工具

将各种文档格式转换为标准化 WebP 页面序列的文档提取和渲染系统，适用于 VLM（视觉语言模型）消费。

## 概述

Doc-Extractor 提供了一个内容寻址的文档存储系统，支持自动格式标准化：

- **输入**: PDF、DOCX、PPTX、XLSX、图片（PNG、JPG）、压缩包（ZIP、TAR、RAR、7Z）
- **输出**: 可配置 DPI 和质量的 WebP 页面序列
- **存储**: 基于 SHA256 的内容寻址，存储在 `~/.monoco/blobs/`

## 命令

### 提取文档
```bash
monoco doc-extractor extract <文件> [选项]
```

选项：
- `--dpi, -d`: 渲染 DPI（72-300，默认：150）
- `--quality, -q`: WebP 质量（1-100，默认：85）
- `--pages, -p`: 指定渲染页面（例如："1-5,10,15-20"）

### 列出提取的文档
```bash
monoco doc-extractor list [--category <类别>] [--limit <数量>]
```

### 搜索文档
```bash
monoco doc-extractor search <查询>
```

### 显示文档详情
```bash
monoco doc-extractor show <哈希前缀>
monoco doc-extractor cat <哈希前缀>    # 显示元数据 JSON
monoco doc-extractor source <哈希前缀> # 显示源文件/压缩包信息
```

### 索引管理
```bash
monoco doc-extractor index rebuild   # 从 blobs 重建索引
monoco doc-extractor index stats     # 显示索引统计
monoco doc-extractor index clear     # 清空索引（保留 blobs）
monoco doc-extractor index path      # 显示索引文件路径
```

### 清理
```bash
monoco doc-extractor clean [--older-than <天数>] [--dry-run]
monoco doc-extractor delete <哈希前缀> [--force]
```

## 存储结构

```
~/.monoco/blobs/
├── index.yaml              # 全局元数据索引
└── {sha256_hash}/          # 内容寻址目录
    ├── meta.json           # 文档元数据
    ├── source.{ext}        # 原始文件（保留扩展名）
    ├── source.pdf          # 标准化 PDF 格式
    └── pages/
        ├── 0.webp          # 第 0 页渲染
        ├── 1.webp          # 第 1 页渲染
        └── ...
```

## Python API

```python
from monoco.features.doc_extractor import DocExtractor, ExtractConfig

extractor = DocExtractor()
config = ExtractConfig(dpi=150, quality=85)
result = await extractor.extract("/path/to/document.pdf", config)

print(f"Hash: {result.blob.hash}")
print(f"Pages: {result.page_count}")
print(f"Cached: {result.is_cached}")
```

## 核心原则

1. **内容寻址**: 文件按 SHA256 哈希存储 - 自动去重
2. **格式标准化**: 所有文档先转为 PDF，再渲染为 WebP
3. **压缩包支持**: 自动解压 ZIP 等压缩包，追踪内部文档来源
4. **缓存感知**: 提取结果被缓存；重复提取立即返回缓存结果
