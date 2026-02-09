"""Core document extractor implementation."""

import asyncio
import hashlib
import json
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

from .models import BlobRef, ExtractConfig, ExtractionResult


class FileTypeDetector:
    """Detect file types using magic numbers and extensions."""
    
    # Magic numbers
    MAGIC_PDF = b"%PDF"
    MAGIC_ZIP = b"PK\x03\x04"
    MAGIC_GZIP = b"\x1f\x8b"
    MAGIC_RAR = b"Rar!"
    MAGIC_7Z = b"7z\xbc\xaf\x27\x1c"
    MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
    MAGIC_JPEG = b"\xff\xd8\xff"
    MAGIC_WEBP = b"RIFF"  # RIFF....WEBP
    
    # Extensions
    EXT_DOCUMENTS = {".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".odt", ".ods", ".odp"}
    EXT_MARKUP = {".html", ".htm", ".md", ".markdown", ".txt", ".rtf"}
    EXT_IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
    EXT_COMPRESS = {".zip", ".tar", ".tar.gz", ".tgz", ".bz2", ".xz", ".rar", ".7z"}
    
    @classmethod
    def detect(cls, path: Path) -> tuple[str, str]:
        """Detect file type.
        
        Returns:
            Tuple of (category, specific_type)
            Categories: pdf, image, document, archive, markup, unknown
        """
        ext = path.suffix.lower()
        header = cls._read_header(path)
        
        # Check magic numbers first
        if header.startswith(cls.MAGIC_PDF):
            return ("pdf", "pdf")
        elif header.startswith(cls.MAGIC_PNG):
            return ("image", "png")
        elif header.startswith(cls.MAGIC_JPEG):
            return ("image", "jpeg")
        elif header.startswith(cls.MAGIC_WEBP) and b"WEBP" in header[:12]:
            return ("image", "webp")
        elif header.startswith(cls.MAGIC_ZIP):
            # Could be zip or docx/pptx/xlsx
            if ext in {".docx", ".pptx", ".xlsx", ".odt", ".ods", ".odp"}:
                return ("document", ext[1:])
            return ("archive", "zip")
        elif header.startswith(cls.MAGIC_GZIP):
            return ("archive", "gzip")
        elif header.startswith(cls.MAGIC_RAR):
            return ("archive", "rar")
        elif header.startswith(cls.MAGIC_7Z):
            return ("archive", "7z")
        
        # Fall back to extension
        if ext in cls.EXT_DOCUMENTS:
            return ("document", ext[1:])
        elif ext in {".html", ".htm"}:
            return ("markup", "html")
        elif ext in {".md", ".markdown"}:
            return ("markup", "markdown")
        elif ext in {".txt", ".rtf"}:
            return ("markup", "text")
        elif ext in cls.EXT_IMAGES:
            return ("image", ext[1:].replace("jpeg", "jpg"))
        elif ext in {".tar"}:
            return ("archive", "tar")
        elif ".tar." in path.name or path.suffixes == [".tar", ".gz"]:
            return ("archive", "tar.gz")
        
        return ("unknown", ext[1:] if ext else "unknown")
    
    @classmethod
    def _read_header(cls, path: Path, size: int = 16) -> bytes:
        """Read file header."""
        try:
            with open(path, "rb") as f:
                return f.read(size)
        except Exception:
            return b""


class PDFRenderer:
    """Render PDF pages to WebP images using PyMuPDF."""
    
    def __init__(self, config: ExtractConfig):
        self.config = config
    
    async def render(self, pdf_path: Path, output_dir: Path) -> list[Path]:
        """Render PDF to WebP pages.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save WebP files
            
        Returns:
            List of paths to rendered WebP files
        """
        import fitz
        from PIL import Image
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open PDF
        doc = fitz.open(pdf_path)
        
        # Determine pages to render
        if self.config.pages:
            pages = [p for p in self.config.pages if 0 <= p < len(doc)]
        else:
            pages = list(range(len(doc)))
        
        rendered = []
        
        # Use thread pool for CPU-intensive rendering
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            futures = [
                loop.run_in_executor(
                    executor,
                    self._render_page,
                    doc,
                    page_num,
                    output_dir,
                )
                for page_num in pages
            ]
            rendered = await asyncio.gather(*futures)
        
        doc.close()
        return [p for p in rendered if p is not None]
    
    def _render_page(self, doc, page_num: int, output_dir: Path) -> Path | None:
        """Render a single page (sync, called in thread pool)."""
        import fitz
        from PIL import Image
        
        try:
            page = doc[page_num]
            
            # Calculate matrix for DPI
            mat = fitz.Matrix(self.config.dpi / 72, self.config.dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Save as WebP
            output_path = output_dir / f"{page_num}.webp"
            img.save(output_path, "WEBP", quality=self.config.quality, method=6)
            
            return output_path
        except Exception as e:
            print(f"Error rendering page {page_num}: {e}")
            return None


class FormatConverter:
    """Convert various formats to PDF."""
    
    @classmethod
    async def convert_to_pdf(cls, input_path: Path, output_path: Path) -> bool:
        """Convert file to PDF.
        
        Args:
            input_path: Input file path
            output_path: Output PDF path
            
        Returns:
            True if successful
        """
        category, file_type = FileTypeDetector.detect(input_path)
        
        if category == "pdf":
            # Already PDF, just copy
            shutil.copy(input_path, output_path)
            return True
        elif category == "image":
            return await cls._image_to_pdf(input_path, output_path)
        elif category in ("document", "markup"):
            return await cls._libreoffice_convert(input_path, output_path)
        
        return False
    
    @classmethod
    async def _image_to_pdf(cls, input_path: Path, output_path: Path) -> bool:
        """Convert image to single-page PDF."""
        from PIL import Image
        
        try:
            img = Image.open(input_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "PDF", resolution=150.0)
            return True
        except Exception as e:
            print(f"Error converting image to PDF: {e}")
            return False
    
    @classmethod
    async def _libreoffice_convert(cls, input_path: Path, output_path: Path) -> bool:
        """Convert using LibreOffice."""
        import subprocess
        
        # Create temp directory for LibreOffice output
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "soffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", tmpdir,
                str(input_path)
            ]
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode != 0:
                    print(f"LibreOffice conversion failed: {stderr.decode()}")
                    return False
                
                # Find the generated PDF
                tmpdir_path = Path(tmpdir)
                pdf_files = list(tmpdir_path.glob("*.pdf"))
                if not pdf_files:
                    print("LibreOffice did not produce output")
                    return False
                
                # Move to final location
                shutil.move(pdf_files[0], output_path)
                return True
                
            except FileNotFoundError:
                print("LibreOffice (soffice) not found. Please install LibreOffice.")
                return False
            except Exception as e:
                print(f"Error in LibreOffice conversion: {e}")
                return False


class ArchiveExtractor:
    """Extract archive files."""
    
    @classmethod
    async def extract(cls, archive_path: Path, output_dir: Path) -> list[Path]:
        """Extract archive and return list of extracted files.
        
        Args:
            archive_path: Path to archive
            output_dir: Directory to extract to
            
        Returns:
            List of extracted file paths (flattened)
        """
        category, archive_type = FileTypeDetector.detect(archive_path)
        
        if category != "archive":
            return []
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if archive_type == "zip":
            return await cls._extract_zip(archive_path, output_dir)
        elif archive_type in ("tar", "tar.gz", "gzip"):
            return await cls._extract_tar(archive_path, output_dir)
        elif archive_type == "rar":
            return await cls._extract_rar(archive_path, output_dir)
        elif archive_type == "7z":
            return await cls._extract_7z(archive_path, output_dir)
        
        return []
    
    @classmethod
    async def _extract_zip(cls, archive_path: Path, output_dir: Path) -> list[Path]:
        """Extract ZIP file with encoding handling."""
        import zipfile
        
        extracted = []
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # Try to fix encoding issues (common with Chinese filenames)
            for member in zf.namelist():
                # Skip directories and hidden files
                if member.endswith('/') or member.startswith('__MACOSX') or member.startswith('.'):
                    continue
                
                # Try to decode/fix encoding
                try:
                    # First try UTF-8
                    decoded_name = member.encode('cp437').decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    try:
                        # Then try GBK (common for Chinese zip files)
                        decoded_name = member.encode('cp437').decode('gbk')
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        # Fall back to original
                        decoded_name = member
                
                # Flatten: use basename only
                safe_name = Path(decoded_name).name
                # Sanitize filename (remove/replace problematic chars)
                safe_name = "".join(c if c.isalnum() or c in '._- ' else '_' for c in safe_name)
                if not safe_name:
                    safe_name = "unnamed_file"
                
                target_path = output_dir / safe_name
                
                # Handle duplicates
                counter = 1
                original_target = target_path
                while target_path.exists():
                    stem = original_target.stem
                    suffix = original_target.suffix
                    target_path = output_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                    
                with zf.open(member) as src, open(target_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                extracted.append(target_path)
        
        return extracted
    
    @classmethod
    async def _extract_tar(cls, archive_path: Path, output_dir: Path) -> list[Path]:
        """Extract TAR/TAR.GZ file."""
        import tarfile
        
        extracted = []
        with tarfile.open(archive_path, 'r:*') as tf:
            for member in tf.getmembers():
                if not member.isfile() or member.name.startswith('.') or '__MACOSX' in member.name:
                    continue
                
                target_path = output_dir / Path(member.name).name
                if not target_path.name:
                    continue
                
                with tf.extractfile(member) as src, open(target_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                extracted.append(target_path)
        
        return extracted
    
    @classmethod
    async def _extract_rar(cls, archive_path: Path, output_dir: Path) -> list[Path]:
        """Extract RAR file using unrar or 7z."""
        # Try 7z first, then unrar
        for cmd in [['7z', 'x', '-y', '-o' + str(output_dir), str(archive_path)],
                    ['unrar', 'x', '-y', str(archive_path), str(output_dir)]]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                
                if proc.returncode == 0:
                    # Collect files (flattened)
                    files = []
                    for f in output_dir.rglob('*'):
                        if f.is_file() and not f.name.startswith('.'):
                            # Move to root if nested
                            if f.parent != output_dir:
                                target = output_dir / f.name
                                shutil.move(f, target)
                                files.append(target)
                            else:
                                files.append(f)
                    return files
            except FileNotFoundError:
                continue
        
        print("No RAR extraction tool found (tried: 7z, unrar)")
        return []
    
    @classmethod
    async def _extract_7z(cls, archive_path: Path, output_dir: Path) -> list[Path]:
        """Extract 7Z file."""
        try:
            proc = await asyncio.create_subprocess_exec(
                '7z', 'x', '-y', '-o' + str(output_dir), str(archive_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            
            if proc.returncode == 0:
                # Collect files (flattened)
                files = []
                for f in output_dir.rglob('*'):
                    if f.is_file() and not f.name.startswith('.'):
                        if f.parent != output_dir:
                            target = output_dir / f.name
                            shutil.move(f, target)
                            files.append(target)
                        else:
                            files.append(f)
                return files
        except FileNotFoundError:
            print("7z not found. Please install p7zip.")
        
        return []


class DocExtractor:
    """Main document extractor."""
    
    BLOBS_DIR = Path.home() / ".monoco" / "blobs"
    
    def __init__(self):
        self.BLOBS_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def compute_hash(path: Path) -> str:
        """Compute SHA256 hash of file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    
    async def extract(
        self, 
        input_path: Path, 
        config: ExtractConfig | None = None,
        source_archive: tuple[str, str, str] | None = None,
    ) -> ExtractionResult:
        """Extract document to blob storage.
        
        Args:
            input_path: Path to input file
            config: Extraction configuration
            
        Returns:
            ExtractionResult with blob reference and page paths
        """
        config = config or ExtractConfig()
        input_path = Path(input_path).resolve()
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Detect file type
        category, file_type = FileTypeDetector.detect(input_path)
        
        # Handle archives: extract first
        if category == "archive":
            return await self._process_archive(input_path, config)
        
        return await self._process_single(input_path, config, source_archive)
    
    async def _process_archive(
        self, 
        archive_path: Path, 
        config: ExtractConfig
    ) -> ExtractionResult:
        """Process archive file, extracting and processing all valid documents."""
        # Compute archive hash
        archive_hash = self.compute_hash(archive_path)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            extracted = await ArchiveExtractor.extract(archive_path, Path(tmpdir))
            if not extracted:
                raise ValueError(f"Failed to extract archive: {archive_path}")
            
            # Process first valid document
            for file in extracted:
                cat, _ = FileTypeDetector.detect(file)
                if cat in ("pdf", "image", "document", "markup"):
                    inner_path = file.name  # Flattened, so just filename
                    return await self._process_single(
                        file, 
                        config,
                        source_archive=(archive_hash, archive_path.name, inner_path)
                    )
            raise ValueError("No valid documents found in archive")

    async def _process_single(
        self,
        input_path: Path,
        config: ExtractConfig,
        source_archive: tuple[str, str, str] | None = None,
    ) -> ExtractionResult:
        """Process a single file with transactional semantics.

        Uses a temporary directory for processing and only moves to final
        location on success. Ensures no incomplete blobs on failure.
        """
        # Compute hash
        file_hash = self.compute_hash(input_path)
        blob = BlobRef(hash=file_hash)

        # Check cache
        if blob.exists():
            # Read metadata to get page count
            meta = json.loads(blob.meta_path.read_text())
            page_count = meta.get("page_count", 0)
            page_paths = sorted(blob.pages_dir.glob("*.webp")) if blob.pages_dir.exists() else []
            return ExtractionResult(
                blob=BlobRef(hash=file_hash, cached=True),
                page_count=page_count,
                page_paths=page_paths,
            )

        # Use temporary directory for atomic processing
        temp_dir = Path(tempfile.mkdtemp(prefix="blob_", dir=self.BLOBS_DIR))
        try:
            # Copy source file
            source_ext = input_path.suffix
            source_path = temp_dir / f"source{source_ext}"
            shutil.copy(input_path, source_path)

            # Convert to PDF
            pdf_path = temp_dir / "source.pdf"
            success = await FormatConverter.convert_to_pdf(input_path, pdf_path)
            if not success:
                raise RuntimeError(f"Failed to convert to PDF: {input_path}")

            # Render to WebP
            pages_dir = temp_dir / "pages"
            renderer = PDFRenderer(config)
            page_paths = await renderer.render(pdf_path, pages_dir)

            # Prepare metadata
            category, file_type = FileTypeDetector.detect(input_path)
            meta = {
                "original_name": input_path.name,
                "original_hash": file_hash,
                "original_path": str(input_path),
                "file_type": file_type,
                "category": category,
                "page_count": len(page_paths),
                "dpi": config.dpi,
                "quality": config.quality,
                "created_at": datetime.now().isoformat(),
                "source_archive": {
                    "hash": source_archive[0],
                    "name": source_archive[1],
                    "inner_path": source_archive[2],
                } if source_archive else None,
            }

            # Write metadata to temp location
            meta_path = temp_dir / "meta.json"
            meta_path.write_text(json.dumps(meta, indent=2))

            # Atomic move: temp -> final
            shutil.move(str(temp_dir), str(blob.path))

            return ExtractionResult(
                blob=blob,
                page_count=len(page_paths),
                page_paths=page_paths,
            )

        except Exception:
            # Clean up temp directory on any failure
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    async def extract_batch(
        self, 
        input_paths: list[Path], 
        config: ExtractConfig | None = None
    ) -> list[ExtractionResult]:
        """Extract multiple documents."""
        tasks = [self.extract(p, config) for p in input_paths]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def list_blobs(self) -> list[BlobRef]:
        """List all stored blobs."""
        blobs = []
        for path in self.BLOBS_DIR.iterdir():
            if path.is_dir() and len(path.name) == 64:  # SHA256 hex
                blobs.append(BlobRef(hash=path.name))
        return blobs
    
    def get_blob(self, hash_prefix: str) -> BlobRef | None:
        """Get blob by hash prefix."""
        for path in self.BLOBS_DIR.iterdir():
            if path.name.startswith(hash_prefix):
                return BlobRef(hash=path.name)
        return None
    
    def delete_blob(self, hash_prefix: str) -> bool:
        """Delete blob by hash prefix."""
        blob = self.get_blob(hash_prefix)
        if blob and blob.exists():
            shutil.rmtree(blob.path)
            return True
        return False


# Import datetime for metadata
from datetime import datetime
