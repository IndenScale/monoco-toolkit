"""
Ralph Loop CLI - Agent Session Relay Commands.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from monoco.core.config import get_config, find_monoco_root
from .core import (
    relay_issue,
    get_relay_status,
    clear_relay_status,
    prepare_last_words,
    get_ralph_dir,
)
app = typer.Typer(help="Ralph Loop - Agent session relay for long-running issues.")
console = Console()


@app.command("relay")
def relay_command(
    issue: str = typer.Option(..., "--issue", "-i", help="Issue ID to relay (e.g., FEAT-0123)"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Last words as a string"),
    path: Optional[Path] = typer.Option(None, "--path", help="Path to last words file"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-generate summary"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
):
    """
    Relay the current Issue to a successor Agent.

    Examples:
        monoco ralph --issue FEAT-0123 --prompt "Completed X, need to do Y"
        monoco ralph --issue FEAT-0123 --path ./last-words.md
        monoco ralph --issue FEAT-0123 --auto
    """
    # Validate that at least one input method is provided
    if not any([prompt, path, auto]):
        console.print("[red]Error: Must provide one of --prompt, --path, or --auto[/red]")
        console.print("\n[yellow]Examples:[/yellow]")
        console.print('  monoco ralph --issue FEAT-0123 --prompt "Completed X, need Y"')
        console.print("  monoco ralph --issue FEAT-0123 --path ./last-words.md")
        console.print("  monoco ralph --issue FEAT-0123 --auto")
        raise typer.Exit(code=1)

    # Validate issue ID format
    if not _validate_issue_id(issue):
        console.print(f"[red]Error: Invalid Issue ID format: {issue}[/red]")
        console.print("[yellow]Expected format: FEAT-XXXX, FIX-XXXX, CHORE-XXXX, etc.[/yellow]")
        raise typer.Exit(code=1)

    # Normalize issue ID (remove # prefix if present)
    issue = issue.lstrip("#")

    try:
        relay = relay_issue(
            issue_id=issue,
            prompt=prompt,
            prompt_path=path,
            auto_generate=auto,
            dry_run=dry_run,
        )

        if dry_run:
            console.print(Panel(
                f"[yellow]DRY RUN - Would relay Issue {issue}[/yellow]\n"
                f"Last Words: {relay.last_words_path}\n"
                f"Status: {relay.status}",
                title="Ralph Loop",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                f"[green]✓ Relay initiated for {issue}[/green]\n"
                f"Last Words: {relay.last_words_path}\n"
                f"Status: {relay.status}",
                title="Ralph Loop",
                border_style="green"
            ))

            if relay.successor_pid:
                console.print(f"[dim]Successor Agent PID: {relay.successor_pid}[/dim]")
                console.print(f"[dim]Log file: .monoco/ralph/{issue}-agent.log[/dim]")
                console.print("\n[yellow]Important:[/yellow] The successor agent is running independently.")
                console.print("You can safely exit this session.")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("status")
def status_command(
    issue: str = typer.Option(..., "--issue", "-i", help="Issue ID to check"),
):
    """
    Check the relay status for an Issue.
    """
    issue = issue.lstrip("#")

    relay = get_relay_status(issue)

    if not relay:
        console.print(f"[yellow]No relay found for {issue}[/yellow]")
        raise typer.Exit(code=0)

    # Color based on status
    status_colors = {
        "pending": "yellow",
        "active": "blue",
        "completed": "green",
        "failed": "red",
    }
    color = status_colors.get(relay.status, "white")

    console.print(Panel(
        f"Issue: [bold]{relay.issue_id}[/bold]\n"
        f"Status: [{color}]{relay.status}[/{color}]\n"
        f"Created: {relay.created_at}\n"
        f"Started: {relay.started_at or 'N/A'}\n"
        f"Last Words: {relay.last_words_path}",
        title="Ralph Loop Status",
        border_style=color
    ))


@app.command("clear")
def clear_command(
    issue: str = typer.Option(..., "--issue", "-i", help="Issue ID to clear"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Clear the relay status and files for an Issue.
    """
    issue = issue.lstrip("#")

    if not force:
        confirm = typer.confirm(f"Clear relay status for {issue}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(code=0)

    deleted = clear_relay_status(issue)

    if deleted:
        console.print(f"[green]✓ Relay status cleared for {issue}[/green]")
    else:
        console.print(f"[yellow]No relay files found for {issue}[/yellow]")


@app.command("prepare")
def prepare_command(
    issue: str = typer.Option(..., "--issue", "-i", help="Issue ID"),
    editor: bool = typer.Option(False, "--editor", "-e", help="Open in editor"),
):
    """
    Prepare Last Words for manual editing.

    Creates a Last Words template file for you to fill in.
    """
    issue = issue.lstrip("#")

    # Create template
    template = f"""# Ralph Loop - Last Words

**Issue**: {issue}
**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 已完成的工作
<!-- 描述已完成的工作和验证结果 -->

## 当前状态
<!-- 描述当前代码/文件状态 -->

## 遇到的障碍
<!-- 描述遇到的障碍或不确定的问题（可选） -->

## 建议的下一步
<!-- 为继任者提供清晰的操作指引 -->
"""

    ralph_dir = get_ralph_dir()
    last_words_path = ralph_dir / f"{issue}-last-words.md"
    last_words_path.write_text(template, encoding="utf-8")

    console.print(f"[green]✓ Last Words template created:[/green] {last_words_path}")

    if editor:
        typer.launch(str(last_words_path))
    else:
        console.print("\n[dim]Edit this file and then run:[/dim]")
        console.print(f'  monoco ralph --issue {issue} --path {last_words_path}')


def _validate_issue_id(issue_id: str) -> bool:
    """Validate Issue ID format."""
    import re
    pattern = r'^#?(FEAT|FIX|CHORE|EPIC|DOCS|REFACTOR)-\d+$'
    return bool(re.match(pattern, issue_id, re.IGNORECASE))


# For backward compatibility, also support direct invocation
@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    issue: Optional[str] = typer.Option(None, "--issue", "-i"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p"),
    path: Optional[Path] = typer.Option(None, "--path"),
):
    """
    Ralph Loop - Agent session relay.

    When the current Agent hits a bottleneck, launch a successor Agent
to continue the Issue.

    Usage:
        monoco ralph --issue FEAT-0123 --prompt "last words"
        monoco ralph --issue FEAT-0123 --path last-words.md
    """
    # If no subcommand invoked and no issue provided, show help
    if ctx.invoked_subcommand is None:
        if issue is None:
            console.print(ctx.get_help())
            raise typer.Exit()

        # Legacy direct invocation: monoco ralph --issue X --prompt Y
        if prompt or path:
            # Call relay command logic
            relay_command(issue=issue, prompt=prompt, path=path)
        else:
            console.print("[red]Error: Must provide --prompt or --path when using direct invocation[/red]")
            console.print("\n[yellow]Use --help for usage information[/yellow]")
            raise typer.Exit(code=1)
