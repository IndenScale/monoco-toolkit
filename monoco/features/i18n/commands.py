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
    
    table = Table(title="i18n Availability Report", box=None)
    table.add_column("Source File", style="cyan")
    table.add_column("Missing Languages", style="red")
    table.add_column("Expected Paths", style="dim")
    
    for f, langs in missing_map.items():
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
    
    status_color = "green" if coverage == 100 else "yellow"
    if coverage < 50:
        status_color = "red"
        
    summary = f"Total Source Files: {len(source_files)}\nTarget Languages: {len(target_langs)}\nTotal Checks: {total_checks}\nFound Translations: {found_count}\nCoverage: [{status_color}]{coverage:.1f}%[/{status_color}]"
    console.print(Panel(summary, title="I18N STATUS", expand=False))

    if missing_map:
        raise typer.Exit(code=1)
