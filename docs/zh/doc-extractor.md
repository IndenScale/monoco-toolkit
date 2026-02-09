# Doc-Extractor: Document Normalization and Rendering Tool

**doc-extractor** is a lightweight, CPU-only document processing tool that converts arbitrary document formats into a standardized format (PDF + WebP page sequences) suitable for VLM (Vision Language Model) consumption.

## Design Principles

- **Pure CPU Operation**: Zero model dependencies, only format conversion and rendering
- **Content-Addressed Storage**: SHA256-based caching eliminates duplicate processing
- **Universal Format Support**: Handles documents, images, archives through unified pipeline
- **VLM-Optimized Output**: WebP format with configurable DPI and quality settings

---

## Storage Structure

Documents are stored in `~/.monoco/blobs/` with content-addressed organization:

```
~/.monoco/blobs/
├── index.yaml              # Global metadata index
└── {sha256_hash}/          # Content-addressed directory
    ├── meta.json           # Document metadata
    ├── source.docx         # Original file (preserved extension)
    ├── source.pdf          # Normalized PDF format
    └── pages/
        ├── 0.webp          # Page 0 rendering
        ├── 1.webp          # Page 1 rendering
        └── ...
```

### Metadata Format (`meta.json`)

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

---

## Supported Formats

### Direct Processing
| Format | Category | Notes |
|--------|----------|-------|
| PDF | `pdf` | Direct rendering |
| PNG, JPEG, WebP | `image` | Convert to single-page PDF first |
| DOCX, PPTX, XLSX | `document` | LibreOffice conversion |
| ODT, ODS, ODP | `document` | LibreOffice conversion |
| HTML, MD, TXT, RTF | `markup` | LibreOffice conversion |

### Archive Processing
| Format | Support | Behavior |
|--------|---------|----------|
| ZIP | ✅ Full | Flattened extraction |
| TAR | ✅ Full | Flattened extraction |
| TAR.GZ / TGZ | ✅ Full | Flattened extraction |
| RAR | ✅ Full | Requires `unrar` or `7z` |
| 7Z | ✅ Full | Requires `7z` |

Archives are processed by extracting all valid documents and processing the first match.

---

## CLI Reference

### Basic Commands

#### Extract Document

```bash
# Basic extraction
monoco doc-extractor extract report.pdf

# With custom DPI and quality
monoco doc-extractor extract document.docx --dpi 200 --quality 90

# Extract specific pages (1-indexed in CLI)
monoco doc-extractor extract report.pdf --pages 1-5,10,15-20

# Process archive contents
monoco doc-extractor extract archive.zip
```

#### List Extracted Documents

```bash
# List all documents
monoco doc-extractor list

# Filter by category
monoco doc-extractor list --category pdf

# Limit results
monoco doc-extractor list --limit 50
```

#### View Document Details

```bash
# Show full details
monoco doc-extractor show <hash_prefix>

# View metadata JSON
monoco doc-extractor cat <hash_prefix>

# Show source/archive information
monoco doc-extractor source <hash_prefix>
```

#### Search Documents

```bash
# Search by filename
monoco doc-extractor search "report"

# Search by hash prefix
monoco doc-extractor search "abc123"

# Search by file type
monoco doc-extractor search "pdf"

# Search by archive name
monoco doc-extractor search "archive.zip"
```

#### Delete and Cleanup

```bash
# Delete specific document
monoco doc-extractor delete <hash_prefix>

# Force delete without confirmation
monoco doc-extractor delete <hash_prefix> --force

# Clean old documents
monoco doc-extractor clean --older-than 30d

# Preview cleanup (dry run)
monoco doc-extractor clean --older-than 30d --dry-run
```

### Index Management

```bash
# Rebuild index from blob directories
monoco doc-extractor index rebuild

# View index statistics
monoco doc-extractor index stats

# Clear index (blobs preserved)
monoco doc-extractor index clear

# Show index file path
monoco doc-extractor index path
```

---

## Python API

### Basic Usage

```python
from monoco.features.doc_extractor import DocExtractor, ExtractConfig

# Initialize extractor
extractor = DocExtractor()

# Create configuration
config = ExtractConfig(
    dpi=150,           # 72-300
    quality=85,        # 1-100
    pages=[0, 1, 2]    # Specific pages (0-indexed), None for all
)

# Extract document
result = await extractor.extract("/path/to/document.pdf", config)

print(f"Hash: {result.blob.hash}")
print(f"Pages: {result.page_count}")
print(f"Cached: {result.is_cached}")
print(f"Location: {result.blob.path}")
```

### Batch Processing

```python
# Process multiple documents
documents = ["doc1.pdf", "doc2.docx", "doc3.png"]
results = await extractor.extract_batch(documents, config)

for result in results:
    if isinstance(result, Exception):
        print(f"Error: {result}")
    else:
        print(f"Extracted: {result.blob.hash}")
```

### Index Operations

```python
from monoco.features.doc_extractor import BlobIndex

index = BlobIndex()

# Add entry
index.add(result.blob)

# Search
blobs = index.search("report")

# List all
entries = index.list_all()

# Get statistics
stats = index.get_stats()
print(f"Total: {stats['total_blobs']}")
print(f"Categories: {stats['categories']}")
```

### Working with Blobs

```python
from monoco.features.doc_extractor import BlobRef

# Create reference from hash
blob = BlobRef(hash="a1b2c3d4...")

# Check existence
if blob.exists():
    print(f"PDF path: {blob.pdf_path}")
    print(f"Pages directory: {blob.pages_dir}")
    print(f"Metadata: {blob.meta_path}")
```

---

## Configuration

### Rendering Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `dpi` | 150 | 72-300 | Resolution for PDF rendering |
| `quality` | 85 | 1-100 | WebP compression quality |
| `pages` | `None` | List[int] | Specific pages (0-indexed) |

Higher DPI provides better quality but increases file size and processing time.

### External Dependencies

#### Required Python Packages
```toml
PyMuPDF = "^1.25.0"    # PDF rendering
Pillow = "^11.0.0"     # Image processing
PyYAML = "^6.0"        # Index storage
```

#### Optional System Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| LibreOffice (`soffice`) | DOCX/PPTX/XLSX conversion | System package manager |
| `p7zip` (`7z`) | 7Z/RAR extraction | System package manager |
| `unrar` | RAR extraction (alternative) | System package manager |

---

## Processing Pipeline

```
Input File
    │
    ├──→ Archive (zip/tar.gz/rar/7z)
    │       └── Extract → Flatten → Process First Match
    │
    └──→ Single File
            │
            ├──→ PDF → Render to WebP
            │
            └──→ Other Format
                    │
                    ├──→ Image → Convert to PDF → Render
                    │
                    └──→ Document/Markup → LibreOffice → PDF → Render
```

### Caching Behavior

1. Compute SHA256 of original file content
2. Check if `{hash}/` directory exists
3. If cached: return existing result
4. If new: perform conversion, save to blob directory

---

## Archive Handling

### Flattening Behavior

Archive contents are extracted with flattened structure (no subdirectories):

```
archive.zip
├── folder1/
│   └── doc1.pdf    → extracted as: doc1.pdf
└── folder2/
    └── doc2.pdf    → extracted as: doc2.pdf (renamed if conflict)
```

### Duplicate Handling

If multiple files have the same name during extraction:
```
doc1.pdf
doc1_1.pdf
doc1_2.pdf
```

### Archive Metadata Tracking

When processing files from archives, source information is preserved:

```json
{
  "source_archive": {
    "hash": "sha256_of_archive",
    "name": "original_archive.zip",
    "inner_path": "path/within/archive.docx"
  }
}
```

Use `monoco doc-extractor source <hash>` to view archive relationships.

---

## Best Practices

### For Users

1. **Use appropriate DPI**: 150 DPI is sufficient for most VLM tasks
2. **Process archives**: Upload archives containing multiple documents for batch processing
3. **Clean regularly**: Use `clean --older-than` to manage disk space
4. **Search effectively**: Use hash prefixes for precise lookups

### For Developers

1. **Reuse configurations**: Create ExtractConfig once for batch operations
2. **Handle exceptions**: Batch operations return exceptions in results list
3. **Check cache status**: Use `result.is_cached` to avoid redundant processing
4. **Update index**: Call `index.add()` after manual blob operations

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| LibreOffice not found | `soffice` not in PATH | Install LibreOffice |
| RAR extraction fails | Missing `7z` or `unrar` | Install p7zip |
| Corrupted output | Source file damaged | Verify source file |
| Cache miss | Wrong hash computed | Check file modifications |

### Debug Information

```bash
# Check index location
monoco doc-extractor index path

# Verify blob structure
monoco doc-extractor show <hash>

# View raw metadata
monoco doc-extractor cat <hash>
```

---

## See Also

- [Agent Skills](../../.claude/skills/) - Role-specific automation tools
- [Issue Workflow](../../AGENTS.md) - Development workflow guidelines
