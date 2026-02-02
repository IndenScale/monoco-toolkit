---
name: monoco_atom_artifact
description: 多模态文档处理 Skill。指导 Agent 将 Office 文档转换为 PDF 并渲染为 WebP 图片，注册到 Monoco Artifact 系统。
type: atom
version: 1.0.0
---

# Monoco Artifact: 多模态文档处理

本 Skill 指导 Agent 执行 Office 文档 → PDF → WebP 的完整转换流程，并将结果注册为 Monoco Artifact。

## 概述

多模态文档处理允许 Agent:

1. 将 Office 文档 (.docx, .xlsx, .pptx) 转换为 PDF
2. 将 PDF 页面渲染为 WebP 图片 (150 DPI)
3. 使用 Monoco CLI 注册转换产物为 Artifact

## 环境探测

在执行转换前，Agent 必须探测以下依赖:

### 1. LibreOffice (soffice)

```bash
# 检查 soffice 是否可用
which soffice
soffice --version

# 常见安装路径 (macOS)
# /Applications/LibreOffice.app/Contents/MacOS/soffice

# 常见安装路径 (Linux)
# /usr/bin/soffice
# /usr/lib/libreoffice/program/soffice
```

**如果未安装**:

- **macOS**: `brew install --cask libreoffice`
- **Ubuntu/Debian**: `sudo apt-get install libreoffice`
- **CentOS/RHEL**: `sudo yum install libreoffice`

### 2. Python 依赖

```bash
# 检查 PyMuPDF (fitz)
python3 -c "import fitz; print(fitz.__doc__)"

# 安装依赖
pip install pymupdf pillow
```

### 3. Monoco CLI

```bash
# 验证 monoco 可用
monoco --version
```

## 转换工作流

### 标准转换流程

```mermaid
flowchart LR
    A[Office Doc] -->|soffice| B[PDF]
    B -->|fitz| C[WebP Images]
    C -->|monoco| D[Artifact Registry]
```

### 步骤 1: Office → PDF

使用 LibreOffice Headless 模式进行转换:

```bash
# 基础转换
soffice --headless --convert-to pdf --outdir /output/path /input/document.docx

# 推荐参数 (高质量、安全模式)
soffice \
  --headless \
  --convert-to pdf:writer_pdf_Export:ExportBookmarks=true \
  --outdir /output/path \
  /input/document.docx
```

**参数说明**:

- `--headless`: 无 GUI 模式，适合服务器/自动化环境
- `--convert-to pdf`: 指定输出格式
- `--outdir`: 输出目录
- `ExportBookmarks=true`: 保留文档书签

### 步骤 2: PDF → WebP

使用 PyMuPDF (fitz) 渲染页面:

```python
import fitz  # PyMuPDF
from pathlib import Path

def pdf_to_webp(pdf_path: str, output_dir: str, dpi: int = 150) -> list[str]:
    """
    将 PDF 页面渲染为 WebP 图片。

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        dpi: 渲染分辨率 (默认 150 DPI)

    Returns:
        生成的 WebP 文件路径列表
    """
    doc = fitz.open(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    webp_files = []
    zoom = dpi / 72  # 72 DPI 是 PDF 默认分辨率
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)

        webp_file = output_path / f"page_{page_num + 1:03d}.webp"
        pix.save(str(webp_file))
        webp_files.append(str(webp_file))

    doc.close()
    return webp_files
```

**DPI 选择指南**:
| DPI | 用途 | 文件大小 |
|-----|------|----------|
| 72 | 预览/缩略图 | 小 |
| 150 | 标准阅读 (推荐) | 中等 |
| 300 | 高质量打印 | 大 |

### 步骤 3: 注册 Artifact

使用 Monoco CLI 注册产物:

```bash
# 注册单个文件
monoco artifact register \
  --file /path/to/page_001.webp \
  --type image/webp \
  --source-document original.docx \
  --page 1

# 批量注册整个目录
monoco artifact register-batch \
  --dir /path/to/webp/output \
  --pattern "*.webp" \
  --source-document original.docx
```

> **注意**: 如果 `monoco artifact` 命令不可用，使用 `monoco project` 或文件元数据记录产物信息。

## 辅助脚本

项目提供 `scripts/doc-to-webp.py` 脚本简化转换流程:

```bash
# 完整转换流程
python scripts/doc-to-webp.py /path/to/document.docx --output ./artifacts --dpi 150

# 仅转换特定页面
python scripts/doc-to-webp.py document.docx --pages 1-5,10

# 保留中间 PDF
python scripts/doc-to-webp.py document.docx --keep-pdf
```

## 异常处理

### 常见问题排查

#### 1. 字体缺失

**症状**: PDF 中文字显示为方块或乱码

**解决方案**:

```bash
# macOS: 安装中文字体
brew install font-noto-cjk

# Linux: 安装文泉驿字体
sudo apt-get install fonts-wqy-zenhei

# 或使用 Docker 运行 (包含完整字体)
docker run --rm -v $(pwd):/docs \
  linuxserver/libreoffice \
  soffice --headless --convert-to pdf /docs/input.docx
```

#### 2. 转换锁死/超时

**症状**: soffice 进程无响应

**解决方案**:

```bash
# 设置超时
 timeout 60 soffice --headless --convert-to pdf input.docx

# 检查并清理僵尸进程
pkill -9 soffice
pkill -9 soffice.bin
```

#### 3. PDF 渲染质量差

**症状**: WebP 图片模糊或有锯齿

**解决方案**:

- 提高 DPI (建议 150-300)
- 使用抗锯齿矩阵:

```python
mat = fitz.Matrix(zoom, zoom).prerotate(0)
pix = page.get_pixmap(matrix=mat, alpha=False)
```

#### 4. 内存不足 (大文档)

**症状**: 处理大 PDF 时内存溢出

**解决方案**:

```python
# 逐页处理，及时释放内存
for page_num in range(len(doc)):
    page = doc[page_num]
    pix = page.get_pixmap(matrix=mat)
    pix.save(f"page_{page_num}.webp")
    pix = None  # 显式释放
    page = None
```

## Agent 执行模板

当用户要求处理文档时，按以下步骤执行:

```
1. [探测] 检查 soffice 和 PyMuPDF 是否可用
   └─ 如果缺失 → 提示用户安装并提供命令

2. [转换] Office → PDF
   └─ 使用 soffice --headless --convert-to pdf
   └─ 验证 PDF 生成成功

3. [渲染] PDF → WebP
   └─ 使用 scripts/doc-to-webp.py 或内联代码
   └─ 默认 150 DPI，可根据需求调整

4. [注册] 调用 monoco 注册 Artifact
   └─ 记录 source-document 和 page 元数据

5. [汇报] 向用户展示:
   - 生成的文件列表
   - 文件大小统计
   - 任何警告或错误
```

## 最佳实践

1. **临时文件管理**: 使用 `tempfile.TemporaryDirectory` 管理中间文件
2. **错误重试**: 转换失败时自动重试 1-2 次
3. **并发控制**: 大文档处理时限制并发页面数
4. **元数据保留**: 始终记录原始文档名称和转换参数
5. **清理策略**: 转换完成后可选保留或删除中间 PDF
