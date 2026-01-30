import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from monoco.core.config import get_config
from .core import add_memo, list_memos, get_inbox_path, validate_content_language

app = typer.Typer(help="Manage memos (fleeting notes).")
console = Console()


def get_issues_root(config=None) -> Path:
    if config is None:
        config = get_config()
    # Resolve absolute path for issues
    from monoco.core.config import find_monoco_root

    project_root = find_monoco_root()
    return project_root / config.paths.issues


@app.command("add")
def add_command(
    content: str = typer.Argument(..., help="The content of the memo."),
    context: Optional[str] = typer.Option(
        None, "--context", "-c", help="Context reference (e.g. file:line)."
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Bypass i18n language validation."
    ),
):
    """
    Capture a new idea or thought into the Memo Inbox.
    """
    config = get_config()
    issues_root = get_issues_root(config)

    # Language Validation
    source_lang = config.i18n.source_lang
    if not force and not validate_content_language(content, source_lang):
        console.print(
            f"[red]Error: Content language mismatch.[/red] Content does not match configured source language: [bold]{source_lang}[/bold]."
        )
        console.print(
            "[yellow]Tip: Use --force to bypass this check if you really want to add this content.[/yellow]"
        )
        raise typer.Exit(code=1)

    uid = add_memo(issues_root, content, context)

    console.print(f"[green]✔ Memo recorded.[/green] ID: [bold]{uid}[/bold]")


@app.command("list")
def list_command():
    """
    List all memos in the inbox.
    """
    issues_root = get_issues_root()

    memos = list_memos(issues_root)

    if not memos:
        console.print("No memos found. Use `monoco memo add` to create one.")
        return

    table = Table(title="Memo Inbox")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Timestamp", style="magenta")
    table.add_column("Content")

    for memo in memos:
        # Truncate content for list view
        content_preview = memo["content"].split("\n")[0]
        if len(memo["content"]) > 50:
            content_preview = content_preview[:47] + "..."

        table.add_row(memo["id"], memo["timestamp"], content_preview)

    console.print(table)


@app.command("open")
def open_command():
    """
    Open the inbox file in the default editor.
    """
    issues_root = get_issues_root()
    inbox_path = get_inbox_path(issues_root)

    if not inbox_path.exists():
        console.print("[yellow]Inbox does not exist yet.[/yellow]")
        return

    typer.launch(str(inbox_path))
