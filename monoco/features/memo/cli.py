import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from monoco.core.config import get_config
from .core import add_memo, load_memos, delete_memo, get_inbox_path, validate_content_language

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
    type: str = typer.Option(
        "insight", "--type", "-t", help="Type of memo (insight, bug, feature, task)."
    ),
    source: str = typer.Option(
        "cli", "--source", "-s", help="Source of the memo."
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

    # TODO: Get actual user name if possible
    author = "User" 
    
    uid = add_memo(
        issues_root, 
        content, 
        context=context,
        author=author,
        source=source,
        memo_type=type
    )

    console.print(f"[green]✔ Memo recorded.[/green] ID: [bold]{uid}[/bold]")


@app.command("list")
def list_command(
    limit: int = typer.Option(None, "--limit", "-n", help="Limit number of memos shown.")
):
    """
    List all memos in the inbox.
    
    Signal Queue Model: Shows current pending signals.
    Once consumed (file cleared), memos are no longer listed here.
    Use git history to see consumed memos.
    """
    issues_root = get_issues_root()

    memos = load_memos(issues_root)

    if not memos:
        console.print("No memos in inbox. (Consumed memos are in git history)")
        return
        
    # Reverse to show newest first
    memos.reverse()
    
    if limit:
        memos = memos[:limit]

    table = Table(title="Memo Inbox (Pending Signals)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta", width=8)
    table.add_column("Source", style="blue", width=10)
    table.add_column("Content")

    for memo in memos:
        # Truncate content for list view
        content_preview = memo.content.split("\n")[0]
        if len(content_preview) > 50:
            content_preview = content_preview[:47] + "..."
        
        table.add_row(
            memo.uid, 
            memo.type,
            memo.source,
            content_preview
        )

    console.print(table)
    console.print(f"\n[yellow]Note:[/yellow] Memos are consumed (deleted) when processed by Architect.")
    console.print("[dim]Use `git log --follow Memos/inbox.md` to see consumed memos.[/dim]")


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


@app.command("delete")
def delete_command(
    memo_id: str = typer.Argument(..., help="The ID of the memo to delete.")
):
    """
    Delete a memo from the inbox by its ID.
    
    Signal Queue Model: This is a manual delete operation.
    Normally memos are consumed automatically by the MemoThresholdHandler.
    """
    issues_root = get_issues_root()

    if delete_memo(issues_root, memo_id):
        console.print(f"[green]✔ Memo [bold]{memo_id}[/bold] deleted successfully.[/green]")
    else:
        console.print(f"[red]Error: Memo with ID [bold]{memo_id}[/bold] not found.[/red]")
        raise typer.Exit(code=1)





