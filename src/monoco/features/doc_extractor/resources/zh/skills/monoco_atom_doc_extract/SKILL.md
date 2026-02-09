---
name: monoco_atom_doc_extract
description: 将文档提取为 WebP 页面以进行 VLM 分析 - 将 PDF、Office、图片转换为标准化 WebP 格式
type: atom
---

## 文档提取

将文档提取为适用于视觉语言模型（VLM）分析的 WebP 页面。

### 使用场景

在以下情况下使用此技能：
- 使用视觉能力分析 PDF 文档
- 处理 Office 文档（DOCX、PPTX、XLSX）提取内容
- 将图片或扫描文档转换为页面序列
- 处理来自 ZIP 压缩包的文档

### 命令

**提取文档：**

```bash
monoco doc-extractor extract <文件路径> [--dpi 150] [--quality 85] [--pages "1-5,10"]
```

**列出提取的文档：**

```bash
monoco doc-extractor list [--category pdf] [--limit 20]
```

**搜索文档：**

```bash
monoco doc-extractor search <查询>
```

**显示文档详情：**

```bash
monoco doc-extractor show <哈希前缀>
monoco doc-extractor cat <哈希前缀>  # 显示元数据 JSON
```

### 参数

| 参数 | 默认值 | 说明 |
|-----------|---------|-------------|
| `--dpi` | 150 | 渲染 DPI（72-300） |
| `--quality` | 85 | WebP 质量（1-100） |
| `--pages` | all | 页面范围（例如："1-5,10,15-20"） |

### 输出

文档存储在 `~/.monoco/blobs/{sha256_hash}/`：
- `source.{ext}` - 原始文件
- `source.pdf` - 标准化 PDF
- `pages/*.webp` - 渲染的页面图片
- `meta.json` - 文档元数据

### 示例

```bash
# 高质量提取 PDF
monoco doc-extractor extract ./report.pdf --dpi 200 --quality 90

# 提取文档的特定页面
monoco doc-extractor extract ./presentation.pptx --pages "1-10"

# 列出所有 PDF 文档
monoco doc-extractor list --category pdf

# 显示提取文档的详情
monoco doc-extractor show a1b2c3d4
```

### 最佳实践

- 小字体文档使用 `--dpi 200` 或更高
- 更好的图像质量使用 `--quality 90`（文件更大）
- 提取的文档按内容哈希缓存 - 重复提取即时完成
- 压缩包（ZIP）自动解压并处理
