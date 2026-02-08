---
name: monoco_atom_doc_convert
description: 文档转换与智能分析 - 使用 LibreOffice 将 Office/PDF 文档转换为可分析格式
type: atom
---

## 文档智能

当需要分析 Office 文档（.docx, .xlsx, .pptx 等）或 PDF 时，使用此流程。

### 核心原则

1. **不依赖外部 GPU 服务** - 不使用 MinerU 等需要任务队列的解析服务
2. **利用现有 Vision 能力** - Kimi CLI / Claude Code 自带视觉分析能力
3. **同步调用 LibreOffice** - 本地转换，无需后台服务

### 转换流程

**步骤 1: 检查 LibreOffice 可用性**

```bash
which soffice
```

**步骤 2: 转换文档为 PDF**

```bash
soffice --headless --convert-to pdf "{input_path}" --outdir "{output_dir}"
```

**步骤 3: 使用 Vision 能力分析**

转换后的 PDF 可直接使用 Agent 的视觉能力分析，无需额外 OCR。

### 支持的格式

| 输入格式 | 转换方式 | 备注 |
|---------|---------|------|
| .docx | LibreOffice → PDF | Word 文档 |
| .xlsx | LibreOffice → PDF | Excel 表格 |
| .pptx | LibreOffice → PDF | PowerPoint |
| .odt | LibreOffice → PDF | OpenDocument |
| .pdf | 直接使用 | 无需转换 |

### 最佳实践

- **临时文件管理**: 转换输出到 `/tmp/` 或项目 `.monoco/tmp/`
- **缓存策略**: 如需缓存解析结果，使用 ArtifactManager 存储
- **错误处理**: 转换失败时向用户报告具体错误信息

### 示例

分析 Word 文档:

```bash
# 转换
soffice --headless --convert-to pdf "./report.docx" --outdir "./tmp"

# 分析 (使用 vision 能力)
# 然后读取 ./tmp/report.pdf 进行分析
```
