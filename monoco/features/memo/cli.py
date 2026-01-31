import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from monoco.core.config import get_config
from .core import add_memo, load_memos, delete_memo, update_memo, get_inbox_path, validate_content_language

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
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (pending, tracked, resolved)."),
    limit: int = typer.Option(None, "--limit", "-n", help="Limit number of memos shown.")
):
    """
    List all memos in the inbox.
    """
    issues_root = get_issues_root()

    memos = load_memos(issues_root)
    
    if status:
        memos = [m for m in memos if m.status == status]

    if not memos:
        console.print("No memos found.")
        return
        
    # Reverse sort by timestamp (newest first) usually? 
    # But file is appended. Let's show newest at bottom (log style) or newest at top?
    # Usually list shows content. Newest at bottom is standard for logs, but for "Inbox" maybe newest top?
    # Let's keep file order (oldest first) unless user asks otherwise, or maybe reverse it for "Inbox" feel?
    # Let's reverse it to see latest first.
    memos.reverse()
    
    if limit:
        memos = memos[:limit]

    table = Table(title="Memo Inbox")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Stat", style="yellow", width=4)
    table.add_column("Type", style="magenta", width=8)
    table.add_column("Ref", style="blue")
    table.add_column("Content")

    for memo in memos:
        # Truncate content for list view
        content_preview = memo.content.split("\n")[0]
        if len(content_preview) > 50:
            content_preview = content_preview[:47] + "..."
            
        status_icon = " "
        if memo.status == "pending": status_icon = "P"
        elif memo.status == "tracked": status_icon = "T"
        elif memo.status == "resolved": status_icon = "✔"
        
        table.add_row(
            memo.uid, 
            status_icon,
            memo.type,
            memo.ref or "",
            content_preview
        )

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


@app.command("delete")
def delete_command(
    memo_id: str = typer.Argument(..., help="The ID of the memo to delete.")
):
    """
    Delete a memo from the inbox by its ID.
    """
    issues_root = get_issues_root()

    if delete_memo(issues_root, memo_id):
        console.print(f"[green]✔ Memo [bold]{memo_id}[/bold] deleted successfully.[/green]")
    else:
        console.print(f"[red]Error: Memo with ID [bold]{memo_id}[/bold] not found.[/red]")
        raise typer.Exit(code=1)


@app.command("link")
def link_command(
    memo_id: str = typer.Argument(..., help="Memo ID"),
    issue_id: str = typer.Argument(..., help="Issue ID to link to")
):
    """
    Link a memo to an issue (Traceability).
    Sets status to 'tracked'.
    """
    issues_root = get_issues_root()
    
    updates = {
        "status": "tracked",
        "ref": issue_id
    }
    
    if update_memo(issues_root, memo_id, updates):
        console.print(f"[green]✔ Memo {memo_id} linked to {issue_id}.[/green]")
    else:
        console.print(f"[red]Error: Memo {memo_id} not found.[/red]")
        raise typer.Exit(code=1)


@app.command("resolve")
def resolve_command(
    memo_id: str = typer.Argument(..., help="Memo ID")
):
    """
    Mark a memo as resolved.
    """
    issues_root = get_issues_root()
    
    updates = {
        "status": "resolved"
    }
    
    if update_memo(issues_root, memo_id, updates):
        console.print(f"[green]✔ Memo {memo_id} resolved.[/green]")
    else:
        console.print(f"[red]Error: Memo {memo_id} not found.[/red]")
        raise typer.Exit(code=1)





