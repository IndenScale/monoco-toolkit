"""
Mailbox Commands - CLI commands for the mailbox feature.

Provides commands:
- list: List messages
- read: Read message content
- send: Create outbound draft
- claim: Claim message (via Courier API)
- done: Mark message complete (via Courier API)
- fail: Mark message failed (via Courier API)
"""

import sys
from datetime import datetime, timezone
from getpass import getuser
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from monoco.core.output import AgentOutput, OutputManager
from monoco.features.connector.protocol.schema import (
    MessageStatus,
    Provider,
)

from .client import (
    CourierError,
    CourierNotRunningError,
    MessageAlreadyClaimedError,
    MessageNotFoundError,
    get_courier_client,
)
from .models import (
    ListFormat,
    MailboxConfig,
    MessageFilter,
    OutboundDraft,
)
from .queries import get_message_query
from .store import get_mailbox_store

app = typer.Typer(help="Manage messages (Mailbox)")
console = Console()


def _get_mailbox_root() -> Path:
    """Get the global mailbox root path.

    CHORE-0050: Changed from project-level (~/.monoco/mailbox) to global-level (~/.monoco/mailbox).
    All projects now share a single global mailbox.
    """
    from monoco.features.connector.protocol.constants import DEFAULT_MAILBOX_ROOT

    return DEFAULT_MAILBOX_ROOT


def _init_mailbox():
    """Initialize mailbox components."""
    mailbox_root = _get_mailbox_root()
    mailbox_config = MailboxConfig(root_path=mailbox_root)
    store = get_mailbox_store(mailbox_config)
    query = get_message_query(store)
    client = get_courier_client()
    return mailbox_config, store, query, client


def _get_agent_id() -> str:
    """Get the current agent ID."""
    # TODO: Get from session/config
    return getuser()


@app.command("list")
def list_messages(
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Filter by status: new, claimed"
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Filter by provider: lark, email, slack"
    ),
    since: Optional[str] = typer.Option(
        None, "--since", help="Filter by time: 2h, 1d, 30m"
    ),
    correlation: Optional[str] = typer.Option(
        None, "--correlation", "-c", help="Filter by correlation ID"
    ),
    all: bool = typer.Option(
        False, "--all", "-a", help="Show all messages including archived"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, compact, id"
    ),
    with_attachments: bool = typer.Option(
        False, "--with-attachments", help="Include attachment info in output"
    ),
    json: AgentOutput = False,
):
    """List messages in the mailbox."""
    try:
        _, _, query, _ = _init_mailbox()
    except Exception as e:
        OutputManager.error(f"Failed to initialize mailbox: {e}")
        raise typer.Exit(code=1)

    # Build filter
    filter = MessageFilter(all=all)

    if status:
        try:
            filter.status = MessageStatus(status.lower())
        except ValueError:
            valid_statuses = [s.value for s in MessageStatus]
            OutputManager.error(
                f"Invalid status '{status}'. Valid: {', '.join(valid_statuses)}"
            )
            raise typer.Exit(code=1)

    if provider:
        try:
            filter.provider = Provider(provider.lower())
        except ValueError:
            valid_providers = [p.value for p in Provider]
            OutputManager.error(
                f"Invalid provider '{provider}'. Valid: {', '.join(valid_providers)}"
            )
            raise typer.Exit(code=1)

    if since:
        filter.since = query.parse_since(since)

    if correlation:
        filter.correlation_id = correlation

    # Parse format
    try:
        list_format = ListFormat(format.lower())
    except ValueError:
        valid_formats = [f.value for f in ListFormat]
        OutputManager.error(
            f"Invalid format '{format}'. Valid: {', '.join(valid_formats)}"
        )
        raise typer.Exit(code=1)

    # Get messages
    messages = query.list_messages(filter=filter, format=list_format)

    # Handle JSON/Agent mode
    if json or list_format == ListFormat.JSON:
        OutputManager.print([m.to_dict() for m in messages])
        return

    # Handle ID-only format (for piping)
    if list_format == ListFormat.ID:
        for msg in messages:
            console.print(msg.id)
        return

    # Handle compact format
    if list_format == ListFormat.COMPACT:
        for msg in messages:
            time_str = (
                msg.timestamp.strftime("%H:%M")
                if datetime.now().date() == msg.timestamp.date()
                else msg.timestamp.strftime("%m-%d")
            )
            attach_marker = " [📎]" if msg.artifact_count > 0 else ""
            console.print(
                f"{msg.id} | {msg.from_name} | {time_str} | {msg.preview[:40]}{attach_marker}"
            )
        return

    # Table format (default)
    table = Table(
        title=f"Messages ({len(messages)})",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("ID", style="cyan", width=25, no_wrap=True)
    table.add_column("Provider", width=10)
    table.add_column("From", width=15)
    table.add_column("Status", width=10)
    table.add_column("Time", width=12)
    if with_attachments:
        table.add_column("Attachments", width=5)
    table.add_column("Preview", style="white")

    status_colors = {
        MessageStatus.NEW: "green",
        MessageStatus.CLAIMED: "yellow",
        MessageStatus.COMPLETED: "dim",
        MessageStatus.FAILED: "red",
    }

    for msg in messages:
        status_color = status_colors.get(msg.status, "white")
        time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M")

        row_data = [
            msg.id,
            msg.provider.value,
            msg.from_name[:14] if len(msg.from_name) > 14 else msg.from_name,
            f"[{status_color}]{msg.status.value}[/{status_color}]",
            time_str,
        ]

        if with_attachments:
            attach_count = msg.artifact_count if hasattr(msg, "artifact_count") else 0
            attach_display = str(attach_count) if attach_count > 0 else "-"
            row_data.append(attach_display)

        row_data.append(msg.preview[:50])

        table.add_row(*row_data)

    console.print(table)


@app.command("read")
def read_message(
    message_id: str = typer.Argument(..., help="Message ID to read"),
    raw: bool = typer.Option(False, "--raw", help="Show raw file content"),
    content_only: bool = typer.Option(
        False, "--content", help="Show only message body"
    ),
    json: AgentOutput = False,
):
    """Read a message's content."""
    try:
        _, store, query, _ = _init_mailbox()
    except Exception as e:
        OutputManager.error(f"Failed to initialize mailbox: {e}")
        raise typer.Exit(code=1)

    # Handle stdin for piping
    if message_id == "-":
        message_id = sys.stdin.read().strip().split("\n")[0]

    message = query.get_message(message_id)

    if not message:
        OutputManager.error(f"Message '{message_id}' not found")
        raise typer.Exit(code=1)

    # Get status from locks
    status = store.get_message_status(message_id)

    # Raw mode - show file content
    if raw:
        file_path = store.find_message_file(message_id)
        if file_path:
            console.print(file_path.read_text())
        else:
            OutputManager.error(f"Message file not found")
            raise typer.Exit(code=1)
        return

    # Content only mode
    if content_only:
        console.print(message.content.text or message.content.markdown or "")
        return

    # JSON/Agent mode
    if json:
        OutputManager.print(
            {
                "message": message.model_dump(mode="json"),
                "status": status.value,
            }
        )
        return

    # Human-readable format
    sender = message.get_sender()
    sender_str = f"{sender.name} ({sender.id})" if sender else "Unknown"

    session_str = message.session.name or message.session.id

    time_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    time_ago = _format_time_ago(message.timestamp)

    content_text = (
        message.content.text or message.content.markdown or "[No text content]"
    )

    mentions = message.get_mentions()
    mentions_str = ""
    if mentions:
        mention_list = [f"@{m.name} ({m.target})" for m in mentions if m.name]
        mentions_str = "\n".join(f"  • {m}" for m in mention_list)

    panel_content = f"""[bold]Provider:[/bold]    {message.provider.value}
[bold]From:[/bold]       {sender_str}
[bold]To:[/bold]         {session_str}
[bold]Time:[/bold]       {time_str} ({time_ago})
[bold]Type:[/bold]       {message.type.value}
[bold]Status:[/bold]     {status.value}
"""

    if message.correlation_id:
        panel_content += f"[bold]Correlation:[/bold] {message.correlation_id}\n"

    if message.reply_to:
        panel_content += f"[bold]Reply To:[/bold]    {message.reply_to}\n"

    if message.thread_root:
        panel_content += f"[bold]Thread Root:[/bold] {message.thread_root}\n"

    panel_content += f"\n[bold]Content:[/bold]\n{content_text}"

    if mentions_str:
        panel_content += f"\n\n[bold]Mentions:[/bold]\n{mentions_str}"

    if message.artifacts:
        artifacts_str = "\n".join(
            f"  • {a.name} ({a.type.value})" for a in message.artifacts
        )
        panel_content += f"\n\n[bold]Artifacts:[/bold]\n{artifacts_str}"

    console.print(
        Panel(
            panel_content,
            title=f"Message: {message_id}",
            border_style="blue",
        )
    )


def _format_time_ago(timestamp: datetime) -> str:
    """Format a timestamp as a human-readable relative time."""
    now = datetime.now(timezone.utc)
    diff = now - timestamp.replace(tzinfo=timezone.utc)

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} min{'s' if minutes > 1 else ''} ago"
    return "just now"


@app.command("send")
def send_message(
    file: Optional[Path] = typer.Argument(None, help="Draft file to send"),
    provider: Optional[str] = typer.Option(
        None, "--provider", help="Target provider: lark, email"
    ),
    to: Optional[str] = typer.Option(None, "--to", help="Target recipient/group ID"),
    text: Optional[str] = typer.Option(
        None, "--text", "-t", help="Message text content"
    ),
    reply_to: Optional[str] = typer.Option(
        None, "--reply-to", help="Message ID being replied to"
    ),
    correlation: Optional[str] = typer.Option(
        None, "--correlation", "-c", help="Correlation ID"
    ),
    json: AgentOutput = False,
):
    """Create an outbound message draft."""
    try:
        _, store, _, client = _init_mailbox()
    except Exception as e:
        OutputManager.error(f"Failed to initialize mailbox: {e}")
        raise typer.Exit(code=1)

    # If file is provided, read and validate it
    if file:
        if not file.exists():
            OutputManager.error(f"Draft file not found: {file}")
            raise typer.Exit(code=1)

        # TODO: Parse draft file and create OutboundMessage
        OutputManager.error("File-based drafts not yet implemented")
        raise typer.Exit(code=1)

    # Quick send mode
    if not provider or not to or not text:
        OutputManager.error(
            "Must provide either --file or all of --provider, --to, and --text"
        )
        raise typer.Exit(code=1)

    try:
        provider_enum = Provider(provider.lower())
    except ValueError:
        valid_providers = [p.value for p in Provider]
        OutputManager.error(
            f"Invalid provider '{provider}'. Valid: {', '.join(valid_providers)}"
        )
        raise typer.Exit(code=1)

    # Generate draft ID
    import uuid

    draft_id = f"out_{provider_enum.value}_{uuid.uuid4().hex[:8]}"

    draft = OutboundDraft(
        id=draft_id,
        to=to,
        provider=provider_enum,
        content_text=text,
        reply_to=reply_to,
    )

    # Create the draft file
    try:
        file_path = store.create_outbound_draft(draft)
    except Exception as e:
        OutputManager.error(f"Failed to create draft: {e}")
        raise typer.Exit(code=1)

    # Try to notify Courier
    courier_notified = False
    try:
        if client.health_check():
            courier_notified = True
    except Exception:
        pass

    result = {
        "draft_id": draft_id,
        "file_path": str(file_path.relative_to(Path.cwd()))
        if file_path.is_relative_to(Path.cwd())
        else str(file_path),
        "provider": provider_enum.value,
        "to": to,
        "courier_notified": courier_notified,
    }

    if json:
        OutputManager.print(result)
    else:
        console.print(f"[green]✓[/green] Created draft: {draft_id}")
        console.print(f"  File: {result['file_path']}")
        if not courier_notified:
            console.print(
                "  [yellow]⚠ Courier not running - draft will be sent when service starts[/yellow]"
            )


@app.command("claim")
def claim_message(
    message_ids: List[str] = typer.Argument(..., help="Message ID(s) to claim"),
    timeout: int = typer.Option(300, "--timeout", help="Claim timeout in seconds"),
    json: AgentOutput = False,
):
    """Claim message(s) for processing."""
    try:
        _, _, _, client = _init_mailbox()
    except Exception as e:
        OutputManager.error(f"Failed to initialize mailbox: {e}")
        raise typer.Exit(code=1)

    # Handle stdin for piping
    if len(message_ids) == 1 and message_ids[0] == "-":
        message_ids = [line.strip() for line in sys.stdin.readlines() if line.strip()]

    agent_id = _get_agent_id()
    results = []
    exit_code = 0

    for message_id in message_ids:
        try:
            lock_info = client.claim_message(message_id, agent_id, timeout)
            results.append(
                {
                    "message_id": message_id,
                    "status": "claimed",
                    "claimed_by": lock_info.claimed_by,
                    "expires_at": lock_info.expires_at.isoformat()
                    if lock_info.expires_at
                    else None,
                }
            )
        except MessageNotFoundError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "not_found",
                    "message": str(e),
                }
            )
            exit_code = 1
        except MessageAlreadyClaimedError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "already_claimed",
                    "claimed_by": e.claimed_by,
                    "message": str(e),
                }
            )
            exit_code = 2
        except CourierNotRunningError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "courier_not_running",
                    "message": str(e),
                }
            )
            exit_code = 3
        except CourierError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "courier_error",
                    "message": str(e),
                }
            )
            exit_code = 4

    if json:
        OutputManager.print(results)
    else:
        for r in results:
            if r["status"] == "claimed":
                console.print(
                    f"[green]✓[/green] Claimed: {r['message_id']} (expires: {r.get('expires_at', 'N/A')})"
                )
            else:
                console.print(f"[red]✗[/red] {r['message_id']}: {r['message']}")

    raise typer.Exit(code=exit_code)


@app.command("done")
def complete_message(
    message_ids: List[str] = typer.Argument(..., help="Message ID(s) to mark complete"),
    json: AgentOutput = False,
):
    """Mark message(s) as complete (processed successfully)."""
    try:
        _, _, _, client = _init_mailbox()
    except Exception as e:
        OutputManager.error(f"Failed to initialize mailbox: {e}")
        raise typer.Exit(code=1)

    # Handle stdin for piping
    if len(message_ids) == 1 and message_ids[0] == "-":
        message_ids = [line.strip() for line in sys.stdin.readlines() if line.strip()]

    agent_id = _get_agent_id()
    results = []
    exit_code = 0

    for message_id in message_ids:
        try:
            client.complete_message(message_id, agent_id)
            results.append(
                {
                    "message_id": message_id,
                    "status": "completed",
                }
            )
        except MessageNotFoundError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "not_found",
                    "message": str(e),
                }
            )
            exit_code = 1
        except CourierError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "courier_error",
                    "message": str(e),
                }
            )
            exit_code = 2

    if json:
        OutputManager.print(results)
    else:
        for r in results:
            if r["status"] == "completed":
                console.print(f"[green]✓[/green] Completed: {r['message_id']}")
            else:
                console.print(f"[red]✗[/red] {r['message_id']}: {r['message']}")

    raise typer.Exit(code=exit_code)


@app.command("fail")
def fail_message(
    message_ids: List[str] = typer.Argument(..., help="Message ID(s) to mark failed"),
    reason: str = typer.Option("", "--reason", "-r", help="Failure reason"),
    retryable: bool = typer.Option(
        True, "--retryable/--no-retryable", help="Whether failure is retryable"
    ),
    json: AgentOutput = False,
):
    """Mark message(s) as failed."""
    try:
        _, _, _, client = _init_mailbox()
    except Exception as e:
        OutputManager.error(f"Failed to initialize mailbox: {e}")
        raise typer.Exit(code=1)

    # Handle stdin for piping
    if len(message_ids) == 1 and message_ids[0] == "-":
        message_ids = [line.strip() for line in sys.stdin.readlines() if line.strip()]

    agent_id = _get_agent_id()
    results = []
    exit_code = 0

    for message_id in message_ids:
        try:
            client.fail_message(message_id, agent_id, reason, retryable)
            results.append(
                {
                    "message_id": message_id,
                    "status": "failed",
                    "retryable": retryable,
                    "reason": reason,
                }
            )
        except MessageNotFoundError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "not_found",
                    "message": str(e),
                }
            )
            exit_code = 1
        except CourierError as e:
            results.append(
                {
                    "message_id": message_id,
                    "status": "error",
                    "error": "courier_error",
                    "message": str(e),
                }
            )
            exit_code = 2

    if json:
        OutputManager.print(results)
    else:
        for r in results:
            if r["status"] == "failed":
                retry_str = "(will retry)" if retryable else "(deadletter)"
                console.print(
                    f"[yellow]⚠[/yellow] Failed: {r['message_id']} {retry_str}"
                )
                if reason:
                    console.print(f"       Reason: {reason}")
            else:
                console.print(f"[red]✗[/red] {r['message_id']}: {r['message']}")

    raise typer.Exit(code=exit_code)
