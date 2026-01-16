import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from typing import Optional
from monoco.core.config import get_config, find_monoco_root
from . import core

app = typer.Typer(help="Management tools for Documentation Internationalization (i18n).")
console = Console()

@app.command("scan")
def scan(
    root: str = typer.Option(None, "--root", help="Target root directory to scan. Defaults to the project root."),
    limit: int = typer.Option(10, "--limit", help="Maximum number of missing files to display. Use 0 for unlimited."),
    check_issues: bool = typer.Option(False, "--check-issues", help="Include Issues directory in the scan."),
    check_source_lang: bool = typer.Option(False, "--check-source-lang", help="Verify if source files content matches source language (heuristic)."),
):
    """
    Scan the project for internationalization (i18n) status.

    Scans all Markdown files in the target directory and checks for the existence of
    translation files based on Monoco's i18n conventions:
    - Root files: suffixed pattern (e.g., README_ZH.md)
    - Sub-directories: subdir pattern (e.g., docs/guide/zh/xxx.md)

    Returns a report of files missing translations in the checking target languages.
    """
    if root:
        target_root = Path(root).resolve()
    else:
        target_root = find_monoco_root(Path.cwd())

    # Load config with correct root
    config = get_config(project_root=str(target_root))
    target_langs = config.i18n.target_langs
    source_lang = config.i18n.source_lang
    
    console.print(f"Scanning i18n coverage in [bold cyan]{target_root}[/bold cyan]...")
    console.print(f"Target Languages: [bold yellow]{', '.join(target_langs)}[/bold yellow] (Source: {source_lang})")
    
    all_files = core.discover_markdown_files(target_root, include_issues=check_issues)
    
    source_files = [f for f in all_files if not core.is_translation_file(f, target_langs)]
    
    # Store missing results: { file_path: [missing_langs] }
    missing_map = {}
    # Store lang mismatch results: [file_path]
    lang_mismatch_files = []

    total_checks = len(source_files) * len(target_langs)
    found_count = 0
    
    for f in source_files:
        # Check translation existence
        missing_langs = core.check_translation_exists(f, target_root, target_langs, source_lang)
        if missing_langs:
            missing_map[f] = missing_langs
            found_count += (len(target_langs) - len(missing_langs))
        else:
            found_count += len(target_langs)
            
        # Check source content language if enabled
        if check_source_lang:
            if not core.is_content_source_language(f, source_lang):
                # Try to detect actual language for better error message
                try:
                    content = f.read_text(encoding="utf-8")
                    detected = core.detect_language(content)
                except:
                    detected = "unknown"
                lang_mismatch_files.append((f, detected))
            
    # Reporting
    coverage = (found_count / total_checks * 100) if total_checks > 0 else 100
    
    # Sort missing_map by file path for stable output
    sorted_missing = sorted(missing_map.items(), key=lambda x: str(x[0]))
    
    # Apply limit
    total_missing_files = len(sorted_missing)
    display_limit = limit if limit > 0 else total_missing_files
    displayed_missing = sorted_missing[:display_limit]
    
    # Build table title with count info
    table_title = "i18n Availability Report"
    if total_missing_files > 0:
        if display_limit < total_missing_files:
            table_title = f"i18n Availability Report (Showing {display_limit} / {total_missing_files} missing files)"
        else:
            table_title = f"i18n Availability Report ({total_missing_files} missing files)"
    
    table = Table(title=table_title, box=None)
    table.add_column("Source File", style="cyan", no_wrap=True, overflow="fold")
    table.add_column("Missing Languages", style="red")
    table.add_column("Expected Paths", style="dim", no_wrap=True, overflow="fold")
    
    for f, langs in displayed_missing:
        rel_path = f.relative_to(target_root)
        expected_paths = []
        for lang in langs:
            target = core.get_target_translation_path(f, target_root, lang, source_lang)
            expected_paths.append(str(target.relative_to(target_root)))
            
        table.add_row(
            str(rel_path), 
            ", ".join(langs),
            "\n".join(expected_paths)
        )
        
    console.print(table)
    
    # Show Language Mismatch Warnings
    if lang_mismatch_files:
        console.print("\n")
        mismatch_table = Table(title=f"Source Language Mismatch (Expected: {source_lang})", box=None)
        mismatch_table.add_column("File", style="yellow")
        mismatch_table.add_column("Detected", style="red")
        
        limit_mismatch = 10
        for f, detected in lang_mismatch_files[:limit_mismatch]:
             mismatch_table.add_row(str(f.relative_to(target_root)), detected)
             
        console.print(mismatch_table)
        if len(lang_mismatch_files) > limit_mismatch:
             console.print(f"[dim]... and {len(lang_mismatch_files) - limit_mismatch} more.[/dim]")

    # Show hint if output was truncated
    if display_limit < total_missing_files:
        console.print(f"\n[dim]💡 Tip: Use [bold]--limit 0[/bold] to show all {total_missing_files} missing files.[/dim]\n")
    
    # Calculate partial vs complete missing
    partial_missing = sum(1 for _, langs in sorted_missing if len(langs) < len(target_langs))
    complete_missing = total_missing_files - partial_missing
    
    status_color = "green" if coverage == 100 else "yellow"
    if coverage < 50:
        status_color = "red"
    
    summary_lines = [
        f"Total Source Files: {len(source_files)}",
        f"Target Languages: {len(target_langs)}",
        f"Total Checks: {total_checks}",
        f"Found Translations: {found_count}",
        f"Missing Files: {total_missing_files}",
    ]
    
    if total_missing_files > 0:
        summary_lines.append(f"  - Partial Missing: {partial_missing}")
        summary_lines.append(f"  - Complete Missing: {complete_missing}")
        
    if lang_mismatch_files:
        summary_lines.append(f"Language Mismatches: {len(lang_mismatch_files)}")
    
    summary_lines.append(f"Coverage: [{status_color}]{coverage:.1f}%[/{status_color}]")
    
    summary = "\n".join(summary_lines)
    console.print(Panel(summary, title="I18N STATUS", expand=False))

    if missing_map or lang_mismatch_files:
        raise typer.Exit(code=1)
