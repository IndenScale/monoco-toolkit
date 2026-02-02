#!/usr/bin/env python3
"""
doc-to-webp.py: Office Document to WebP Converter

将 Office 文档 (.docx, .xlsx, .pptx) 转换为 PDF，
然后将 PDF 页面渲染为 WebP 图片。

Usage:
    python doc-to-webp.py <input.docx> [options]

Examples:
    # 基本转换
    python doc-to-webp.py document.docx

    # 指定输出目录和 DPI
    python doc-to-webp.py document.docx -o ./artifacts --dpi 200

    # 仅转换特定页面
    python doc-to-webp.py document.docx --pages 1-5,10,12-15

    # 保留中间 PDF
    python doc-to-webp.py document.docx --keep-pdf
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional


def check_dependency(command: str, name: str) -> bool:
    """检查系统依赖是否可用。"""
    try:
        subprocess.run(
            [command, "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def find_soffice() -> Optional[str]:
    """查找 soffice 可执行文件。"""
    # 常见路径
    common_paths = [
        "soffice",
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]

    for path in common_paths:
        if check_dependency(path, "LibreOffice"):
            return path

    return None


def office_to_pdf(input_path: str, output_dir: str, soffice_path: str) -> str:
    """
    使用 LibreOffice 将 Office 文档转换为 PDF。

    Args:
        input_path: Office 文档路径
        output_dir: 输出目录
        soffice_path: soffice 可执行文件路径

    Returns:
        生成的 PDF 文件路径

    Raises:
        RuntimeError: 转换失败
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # 构建命令
    cmd = [
        soffice_path,
        "--headless",
        "--convert-to",
        "pdf:writer_pdf_Export:ExportBookmarks=true",
        "--outdir",
        output_dir,
        str(input_file.absolute()),
    ]

    print(f"Converting {input_file.name} to PDF...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2分钟超时
        )

        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        # 清理可能的僵尸进程
        subprocess.run(["pkill", "-9", "soffice"], capture_output=True)
        subprocess.run(["pkill", "-9", "soffice.bin"], capture_output=True)
        raise RuntimeError("LibreOffice conversion timed out (120s)")

    # 查找生成的 PDF
    pdf_name = input_file.stem + ".pdf"
    pdf_path = Path(output_dir) / pdf_name

    if not pdf_path.exists():
        raise RuntimeError(f"PDF not generated: {pdf_path}")

    print(f"  ✓ PDF generated: {pdf_path}")
    return str(pdf_path)


def parse_page_ranges(pages_str: str) -> List[int]:
    """
    解析页面范围字符串。

    Args:
        pages_str: 例如 "1-5,10,12-15"

    Returns:
        页面编号列表 (0-based)
    """
    pages = set()

    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            pages.update(range(int(start) - 1, int(end)))
        else:
            pages.add(int(part) - 1)

    return sorted(pages)


def pdf_to_webp(
    pdf_path: str,
    output_dir: str,
    dpi: int = 150,
    pages: Optional[List[int]] = None,
    quality: int = 90,
) -> List[str]:
    """
    将 PDF 页面渲染为 WebP 图片。

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        dpi: 渲染分辨率 (默认 150)
        pages: 要渲染的页面列表 (0-based)，None 表示全部
        quality: WebP 质量 (0-100)

    Returns:
        生成的 WebP 文件路径列表
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Error: PyMuPDF (fitz) is required.")
        print("Install: pip install pymupdf")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 确定要处理的页面
    if pages is None:
        pages = list(range(len(doc)))
    else:
        # 过滤无效页面
        pages = [p for p in pages if 0 <= p < len(doc)]

    zoom = dpi / 72  # 72 DPI 是 PDF 默认分辨率
    mat = fitz.Matrix(zoom, zoom)

    webp_files = []
    pdf_name = Path(pdf_path).stem

    print(f"Rendering {len(pages)} pages at {dpi} DPI...")

    for page_num in pages:
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat, alpha=False)

        webp_file = output_path / f"{pdf_name}_page_{page_num + 1:03d}.webp"
        pix.save(str(webp_file), quality=quality)
        webp_files.append(str(webp_file))

        # 显式释放内存
        pix = None
        page = None

    doc.close()

    total_size = sum(Path(f).stat().st_size for f in webp_files)
    print(f"  ✓ Generated {len(webp_files)} WebP files ({total_size / 1024 / 1024:.2f} MB)")

    return webp_files


def register_artifacts(
    webp_files: List[str],
    source_document: str,
    output_dir: str,
) -> None:
    """
    注册产物到 Monoco Artifact 系统。

    创建 artifact.json 元数据文件。
    """
    import json

    artifacts = []
    for webp_file in sorted(webp_files):
        path = Path(webp_file)
        # 从文件名提取页码
        match = re.search(r"page_(\d+)", path.name)
        page_num = int(match.group(1)) if match else None

        artifacts.append({
            "file": str(path.absolute()),
            "type": "image/webp",
            "source_document": source_document,
            "page": page_num,
            "size": path.stat().st_size,
        })

    # 写入元数据文件
    metadata_path = Path(output_dir) / "artifact.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": source_document,
            "count": len(artifacts),
            "artifacts": artifacts,
        }, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Artifact metadata: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Office documents to WebP images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.docx
  %(prog)s document.docx -o ./artifacts --dpi 200
  %(prog)s document.docx --pages 1-5,10
  %(prog)s document.docx --keep-pdf -q 95
        """,
    )

    parser.add_argument("input", help="Input Office document (.docx, .xlsx, .pptx)")
    parser.add_argument(
        "-o", "--output",
        default="./artifacts",
        help="Output directory (default: ./artifacts)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Rendering DPI (default: 150)",
    )
    parser.add_argument(
        "--pages",
        help="Page ranges to render, e.g., '1-5,10,12-15'",
    )
    parser.add_argument(
        "--quality",
        "-q",
        type=int,
        default=90,
        help="WebP quality 0-100 (default: 90)",
    )
    parser.add_argument(
        "--keep-pdf",
        action="store_true",
        help="Keep intermediate PDF file",
    )
    parser.add_argument(
        "--soffice",
        help="Path to soffice executable",
    )

    args = parser.parse_args()

    # 验证输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # 检查文件扩展名
    valid_exts = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".ods", ".odp"}
    if input_path.suffix.lower() not in valid_exts:
        print(f"Warning: Unrecognized extension '{input_path.suffix}'")
        print(f"Supported: {', '.join(valid_exts)}")

    # 查找 soffice
    soffice_path = args.soffice or find_soffice()
    if not soffice_path:
        print("Error: LibreOffice (soffice) not found.")
        print("Please install LibreOffice:")
        print("  macOS: brew install --cask libreoffice")
        print("  Ubuntu: sudo apt-get install libreoffice")
        print("  Or specify path with --soffice")
        sys.exit(1)

    print(f"Using LibreOffice: {soffice_path}")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="doc-to-webp-")

    try:
        # 步骤 1: Office → PDF
        pdf_path = office_to_pdf(str(input_path.absolute()), temp_dir, soffice_path)

        # 步骤 2: PDF → WebP
        pages = parse_page_ranges(args.pages) if args.pages else None
        webp_files = pdf_to_webp(
            pdf_path,
            args.output,
            dpi=args.dpi,
            pages=pages,
            quality=args.quality,
        )

        # 步骤 3: 注册 Artifact
        register_artifacts(webp_files, input_path.name, args.output)

        # 可选: 保留 PDF
        if args.keep_pdf:
            import shutil
            pdf_dest = Path(args.output) / f"{input_path.stem}.pdf"
            shutil.copy2(pdf_path, pdf_dest)
            print(f"  ✓ PDF kept: {pdf_dest}")

        print(f"\n✅ Conversion complete: {len(webp_files)} pages → {args.output}/")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
