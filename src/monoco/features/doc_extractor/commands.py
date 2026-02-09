"""CLI commands for doc-extractor."""

import asyncio
import json
from pathlib import Path

import typer
from typing_extensions import Annotated

from monoco.core.output import AgentOutput, OutputManager
from . import DocExtractor, ExtractConfig
from .index import BlobIndex

app = typer.Typer(name="doc-extractor", help="Document extraction and rendering tool")


def _parse_pages(pages_str: str) -> list[int]:
    """Parse pages string like '1-5,10,15-20' to 0-indexed list."""
    result = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            result.extend(range(int(start) - 1, int(end)))  # 1-indexed to 0-indexed
        else:
            result.append(int(part) - 1)  # 1-indexed to 0-indexed
    return sorted(set(result))


@app.command()
def extract(
    input_path: Annotated[Path, typer.Argument(help="Path to the document file")],
    dpi: Annotated[int, typer.Option("--dpi", "-d", help="DPI for rendering (72-300)")] = 150,
    quality: Annotated[int, typer.Option("--quality", "-q", help="WebP quality (1-100)")] = 85,
    pages: Annotated[str | None, typer.Option("--pages", "-p", help="Pages to render, e.g., '1-5,10,15-20'")] = None,
    json: AgentOutput = False,
):
    """Extract a document to WebP pages.
    
    Examples:
        monoco doc-extractor extract report.pdf
        monoco doc-extractor extract report.docx --dpi 200
        monoco doc-extractor extract archive.zip --pages 1-5
    """
    if not input_path.exists():
        OutputManager.error(f"File not found: {input_path}")
        raise typer.Exit(1)
    
    # Parse pages
    page_list = None
    if pages:
        try:
            page_list = _parse_pages(pages)
        except ValueError as e:
            OutputManager.error(f"Invalid pages format: {e}")
            raise typer.Exit(1)
    
    config = ExtractConfig(dpi=dpi, quality=quality, pages=page_list)
    extractor = DocExtractor()
    
    try:
        result = asyncio.run(extractor.extract(input_path, config))
        
        # Update index
        index = BlobIndex()
        index.add(result.blob)
        
        # Build output
        output = {
            "status": "cached" if result.is_cached else "extracted",
            "hash": result.blob.hash,
            "pages": result.page_count,
            "location": str(result.blob.path),
        }
        
        if result.page_paths:
            page_info = []
            for i, path in enumerate(result.page_paths):
                size = path.stat().st_size / 1024  # KB
                page_info.append({"page": i, "file": path.name, "size_kb": round(size, 1)})
            output["page_files"] = page_info[:10]
            if len(result.page_paths) > 10:
                output["more_pages"] = len(result.page_paths) - 10
        
        OutputManager.print(output, title="Extraction Result")
        
        # Show preview in human mode
        if not OutputManager.is_agent_mode() and result.page_paths:
            from rich.console import Console
            console = Console()
            console.print("\n[bold]Rendered pages:[/bold]")
            for i, path in enumerate(result.page_paths[:5]):
                size = path.stat().st_size / 1024
                console.print(f"   {path.name} ({size:.1f} KB)")
            if len(result.page_paths) > 5:
                console.print(f"   ... and {len(result.page_paths) - 5} more")
                
    except Exception as e:
        OutputManager.error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("list")
def list_blobs(
    limit: Annotated[int, typer.Option("--limit", "-l", help="Maximum number of blobs to show")] = 20,
    category: Annotated[str | None, typer.Option("--category", "-c", help="Filter by category (pdf, image, document, etc.)")] = None,
    json: AgentOutput = False,
):
    """List all extracted document blobs."""
    index = BlobIndex()
    entries = index.list_all()
    
    if category:
        entries = [e for e in entries if e.get("category") == category.lower()]
    
    if not entries:
        OutputManager.print([], title="Extracted Documents")
        return
    
    # Build output data
    data = []
    for entry in entries[:limit]:
        item = {
            "hash": entry["hash"],
            "name": entry.get("name", "unknown"),
            "pages": entry.get("page_count", 0),
            "created": entry.get("created_at", "")[:10],
            "category": entry.get("category", "unknown"),
        }
        if entry.get("source_archive"):
            item["source_archive"] = entry["source_archive"]["name"]
        data.append(item)
    
    OutputManager.print(data, title=f"Extracted Documents ({len(data)} shown)")
    
    if len(entries) > limit:
        OutputManager.print({"message": f"... and {len(entries) - limit} more"})


@app.command()
def show(
    hash_prefix: Annotated[str, typer.Argument(help="First few characters of the blob hash")],
    json: AgentOutput = False,
):
    """Show details of an extracted document."""
    extractor = DocExtractor()
    blob = extractor.get_blob(hash_prefix)
    
    if not blob or not blob.exists():
        OutputManager.error(f"Blob not found: {hash_prefix}")
        raise typer.Exit(1)
    
    # Build output
    output = {
        "hash": blob.hash,
        "path": str(blob.path),
    }
    
    # Show metadata
    if blob.meta_path.exists():
        meta = json.loads(blob.meta_path.read_text())
        output["metadata"] = meta
    
    # Show pages
    if blob.pages_dir.exists():
        pages = sorted(blob.pages_dir.glob("*.webp"))
        page_info = []
        for page in pages:
            size = page.stat().st_size / 1024
            page_info.append({"file": page.name, "size_kb": round(size, 1)})
        output["pages"] = page_info
    
    OutputManager.print(output, title="Blob Details")


@app.command()
def cat(
    hash_prefix: Annotated[str, typer.Argument(help="First few characters of the blob hash")],
):
    """Display metadata JSON of an extracted document."""
    extractor = DocExtractor()
    blob = extractor.get_blob(hash_prefix)
    
    if not blob or not blob.exists():
        OutputManager.error(f"Blob not found: {hash_prefix}")
        raise typer.Exit(1)
    
    if not blob.meta_path.exists():
        OutputManager.error("No metadata found")
        raise typer.Exit(1)
    
    # Output raw JSON
    typer.echo(blob.meta_path.read_text())


@app.command()
def delete(
    hash_prefix: Annotated[str, typer.Argument(help="First few characters of the blob hash")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    json: AgentOutput = False,
):
    """Delete an extracted document blob."""
    extractor = DocExtractor()
    index = BlobIndex()
    
    blob = extractor.get_blob(hash_prefix)
    if not blob or not blob.exists():
        OutputManager.error(f"Blob not found: {hash_prefix}")
        raise typer.Exit(1)
    
    hash_full = blob.hash
    
    if not force and not OutputManager.is_agent_mode():
        confirm = typer.confirm(f"Delete blob {hash_prefix}?")
        if not confirm:
            OutputManager.print({"status": "cancelled"})
            raise typer.Exit(0)
    
    if extractor.delete_blob(hash_prefix):
        index.remove(hash_full)
        OutputManager.print({"status": "deleted", "hash": hash_full})
    else:
        OutputManager.error(f"Failed to delete blob: {hash_prefix}")
        raise typer.Exit(1)


@app.command()
def clean(
    older_than: Annotated[int | None, typer.Option("--older-than", "-d", help="Delete blobs older than N days")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be deleted without deleting")] = False,
    json: AgentOutput = False,
):
    """Clean up extracted document blobs."""
    from datetime import datetime, timedelta
    
    extractor = DocExtractor()
    index = BlobIndex()
    blobs = extractor.list_blobs()
    
    to_delete = []
    
    for blob in blobs:
        if older_than:
            if not blob.meta_path.exists():
                continue
            try:
                meta = json.loads(blob.meta_path.read_text())
                created = datetime.fromisoformat(meta.get("created_at", ""))
                if datetime.now() - created > timedelta(days=older_than):
                    to_delete.append(blob)
            except Exception:
                pass
    
    if not to_delete:
        OutputManager.print({"status": "empty", "message": "No blobs to clean"})
        return
    
    result = {
        "dry_run": dry_run,
        "to_delete_count": len(to_delete),
        "blobs": [{"hash": b.hash[:16], "full_hash": b.hash} for b in to_delete],
    }
    
    if dry_run:
        OutputManager.print(result, title="Clean Preview")
    else:
        count = 0
        for blob in to_delete:
            if extractor.delete_blob(blob.hash[:8]):
                index.remove(blob.hash)
                count += 1
        result["deleted_count"] = count
        OutputManager.print(result, title="Clean Complete")


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search term (name, hash prefix, file type, archive name)")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Maximum results")] = 10,
    json: AgentOutput = False,
):
    """Search for extracted documents.
    
    Examples:
        monoco doc-extractor search "report"
        monoco doc-extractor search "abc123"  # hash prefix
        monoco doc-extractor search "pdf"     # file type
        monoco doc-extractor search "archive.zip"
    """
    index = BlobIndex()
    results = index.search(query)[:limit]
    
    if not results:
        OutputManager.print({"results": [], "message": f"No results found for '{query}'"})
        return
    
    data = []
    for blob in results:
        entry = index.get_entry(blob.hash)
        if entry:
            item = {
                "hash": entry["hash"],
                "name": entry.get("name", "unknown"),
                "pages": entry.get("page_count", 0),
                "file_type": entry.get("file_type", "unknown"),
            }
            if entry.get("source_archive"):
                item["source_archive"] = entry["source_archive"]["name"]
            data.append(item)
        else:
            data.append({"hash": blob.hash, "name": "unknown"})
    
    OutputManager.print({"query": query, "results": data}, title=f"Search Results ({len(data)})")


@app.command()
def source(
    hash_prefix: Annotated[str, typer.Argument(help="First few characters of the blob hash")],
    json: AgentOutput = False,
):
    """Show the source/archive information for a blob."""
    extractor = DocExtractor()
    blob = extractor.get_blob(hash_prefix)
    
    if not blob or not blob.exists():
        OutputManager.error(f"Blob not found: {hash_prefix}")
        raise typer.Exit(1)
    
    if not blob.meta_path.exists():
        OutputManager.error("No metadata found")
        raise typer.Exit(1)
    
    meta = json.loads(blob.meta_path.read_text())
    
    output = {
        "hash": blob.hash,
        "name": meta.get("original_name", "unknown"),
        "original_path": meta.get("original_path", "N/A"),
    }
    
    source_archive = meta.get("source_archive")
    if source_archive:
        output["source_archive"] = source_archive
        
        # List other files from same archive
        index = BlobIndex()
        siblings = index.list_by_archive(source_archive["hash"])
        siblings = [s for s in siblings if s.hash != blob.hash]
        
        if siblings:
            output["siblings"] = [
                {"hash": s.hash, "name": index.get_entry(s.hash, {}).get("name", "unknown")}
                for s in siblings[:10]
            ]
            if len(siblings) > 10:
                output["siblings_more"] = len(siblings) - 10
    else:
        output["source_type"] = "direct"
    
    OutputManager.print(output, title="Source Information")


# Index subcommand group
index_app = typer.Typer(help="Manage the document index")
app.add_typer(index_app, name="index")


@index_app.command("rebuild")
def index_rebuild(
    json: AgentOutput = False,
):
    """Rebuild the index from all blob directories."""
    index = BlobIndex()
    count = index.rebuild()
    OutputManager.print({"status": "rebuilt", "entries": count})


@index_app.command("stats")
def index_stats(
    json: AgentOutput = False,
):
    """Show index statistics."""
    index = BlobIndex()
    stats = index.get_stats()
    OutputManager.print(stats, title="Index Statistics")


@index_app.command("clear")
def index_clear(
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    json: AgentOutput = False,
):
    """Clear the index (blobs are not deleted)."""
    if not force and not OutputManager.is_agent_mode():
        confirm = typer.confirm("Clear the entire index? Blobs will NOT be deleted.")
        if not confirm:
            OutputManager.print({"status": "cancelled"})
            raise typer.Exit(0)
    
    index = BlobIndex()
    index.clear()
    OutputManager.print({"status": "cleared", "message": "Index cleared (blobs not deleted)"})


@index_app.command("path")
def index_path():
    """Show the index file path."""
    OutputManager.print({"index_path": str(BlobIndex.INDEX_PATH)})
