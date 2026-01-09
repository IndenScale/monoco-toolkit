import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from monoco.core.config import get_config
from . import core

app = typer.Typer(help="Management tools for Documentation Internationalization (i18n).")
console = Console()

@app.command("scan")
def scan(
    root: str = typer.Option(None, "--root", help="Target root directory to scan. Defaults to the project root."),
    limit: int = typer.Option(10, "--limit", help="Maximum number of missing files to display. Use 0 for unlimited."),
):
    """
    Scan the project for internationalization (i18n) status.

    Scans all Markdown files in the target directory and checks for the existence of
    translation files based on Monoco's i18n conventions:
    - Root files: suffixed pattern (e.g., README_ZH.md)
    - Sub-directories: subdir pattern (e.g., docs/guide/zh/xxx.md)

    Returns a report of files missing translations in the checking target languages.
    """
    config = get_config()
    target_root = Path(root).resolve() if root else Path(config.paths.root)
    target_langs = config.i18n.target_langs
    
    console.print(f"Scanning i18n coverage in [bold cyan]{target_root}[/bold cyan]...")
    console.print(f"Target Languages: [bold yellow]{', '.join(target_langs)}[/bold yellow] (Source: {config.i18n.source_lang})")
    
    all_files = core.discover_markdown_files(target_root)
    
    source_files = [f for f in all_files if not core.is_translation_file(f, target_langs)]
    
    # Store missing results: { file_path: [missing_langs] }
    missing_map = {}
    total_checks = len(source_files) * len(target_langs)
    found_count = 0
    
    for f in source_files:
        missing_langs = core.check_translation_exists(f, target_root, target_langs)
        if missing_langs:
            missing_map[f] = missing_langs
            found_count += (len(target_langs) - len(missing_langs))
        else:
            found_count += len(target_langs)
            
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
            target = core.get_target_translation_path(f, target_root, lang)
            expected_paths.append(str(target.relative_to(target_root)))
            
        table.add_row(
            str(rel_path), 
            ", ".join(langs),
            "\n".join(expected_paths)
        )
        
    console.print(table)
    
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
    
    summary_lines.append(f"Coverage: [{status_color}]{coverage:.1f}%[/{status_color}]")
    
    summary = "\n".join(summary_lines)
    console.print(Panel(summary, title="I18N STATUS", expand=False))

    if missing_map:
        raise typer.Exit(code=1)
