"""
Channel Commands - CLI commands for channel management.

Provides commands:
- list: List all configured channels
- add: Add a new channel (interactive)
- remove: Remove a channel
- test: Test channel connectivity
- send: Send a message through a channel
- default: Set default channels
"""

import time
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from monoco.core.output import OutputManager

from .models import (
    ChannelDefaults,
    ChannelSendResult,
    ChannelTestResult,
    ChannelType,
    DingtalkChannel,
    EmailChannel,
    LarkChannel,
)
from .store import get_channel_store
from .sender import ChannelSender
from .migrate import migrate_from_env, show_migration_status

app = typer.Typer(help="Manage notification channels (DingTalk, Lark, Email)")
console = Console()


def _get_type_icon(channel_type: ChannelType) -> str:
    """Get icon for channel type."""
    icons = {
        ChannelType.DINGTALK: "📱",
        ChannelType.LARK: "🚀",
        ChannelType.EMAIL: "📧",
    }
    return icons.get(channel_type, "📢")


def _get_status_style(enabled: bool) -> tuple[str, str]:
    """Get status display style."""
    if enabled:
        return "green", "✓ enabled"
    return "red", "✗ disabled"


@app.command("list")
def list_channels(
    type_filter: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type (dingtalk, lark, email)"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all configured channels."""
    store = get_channel_store()
    channels = store.list_all()

    if type_filter:
        try:
            filter_type = ChannelType(type_filter.lower())
            channels = [c for c in channels if c.type == filter_type]
        except ValueError:
            OutputManager.error(f"Invalid channel type: {type_filter}")
            raise typer.Exit(code=1)

    if json:
        import json as json_module

        data = {
            "channels": [c.model_dump(mode="json") for c in channels],
            "defaults": {
                "send": store._config.defaults.send if store._config else None,
                "receive": store._config.defaults.receive if store._config else [],
            },
            "total": len(channels),
        }
        OutputManager.print(data)
        return

    if not channels:
        console.print("[yellow]No channels configured.[/yellow]")
        console.print("Use [bold]monoco channel add <type>[/bold] to add a channel.")
        return

    # Show defaults
    if store._config and store._config.defaults:
        defaults = store._config.defaults
        if defaults.send or defaults.receive:
            console.print("[bold]Defaults:[/bold]")
            if defaults.send:
                console.print(f"  Send: {defaults.send}")
            if defaults.receive:
                console.print(f"  Receive: {', '.join(defaults.receive)}")
            console.print()

    table = Table(title="Configured Channels")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta", width=10)
    table.add_column("Name", style="white")
    table.add_column("Status", style="green", width=12)
    table.add_column("Created", style="dim", width=12)

    for channel in sorted(channels, key=lambda c: c.created_at, reverse=True):
        icon = _get_type_icon(channel.type)
        status_color, status_text = _get_status_style(channel.enabled)

        created_str = channel.created_at.strftime("%Y-%m-%d")

        table.add_row(
            channel.id,
            f"{icon} {channel.type.value}",
            channel.name,
            f"[{status_color}]{status_text}[/{status_color}]",
            created_str,
        )

    console.print(table)
    console.print(f"\nTotal: {len(channels)} channels")


@app.command("add")
def add_channel(
    channel_type: str = typer.Argument(..., help="Channel type (dingtalk, lark, email)"),
    channel_id: Optional[str] = typer.Option(None, "--id", help="Unique channel ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Display name"),
    # DingTalk specific options
    webhook: Optional[str] = typer.Option(None, "--webhook", "-w", help="DingTalk/Lark webhook URL"),
    secret: Optional[str] = typer.Option(None, "--secret", "-s", help="Bot secret for signature"),
    keywords: Optional[str] = typer.Option(None, "--keywords", "-k", help="DingTalk keywords"),
    # Email specific options
    smtp_host: Optional[str] = typer.Option(None, "--smtp-host", help="SMTP server host"),
    smtp_port: int = typer.Option(587, "--smtp-port", help="SMTP server port"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="SMTP username/email"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="SMTP password"),
    use_tls: bool = typer.Option(True, "--tls/--no-tls", help="Use TLS for SMTP"),
    from_address: Optional[str] = typer.Option(None, "--from", help="From email address"),
    to_addresses: Optional[str] = typer.Option(None, "--to", help="Default recipient addresses (comma-separated)"),
    # Mode
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-I", help="Interactive mode"),
):
    """Add a new notification channel."""
    store = get_channel_store()

    # Validate channel type
    try:
        ch_type = ChannelType(channel_type.lower())
    except ValueError:
        OutputManager.error(f"Invalid channel type: {channel_type}")
        console.print("Supported types: dingtalk, lark, email")
        raise typer.Exit(code=1)

    if interactive:
        # Interactive mode
        console.print(Panel.fit(f"Add {ch_type.value.upper()} Channel", style="blue"))

        # Channel ID
        if not channel_id:
            default_id = f"{ch_type.value[:2]}-"
            channel_id = Prompt.ask("Channel ID", default=default_id)

        if store.exists(channel_id):
            OutputManager.error(f"Channel ID '{channel_id}' already exists")
            raise typer.Exit(code=1)

        # Channel name
        if not name:
            default_name = f"My {ch_type.value.title()} Channel"
            name = Prompt.ask("Display name", default=default_name)

        # Type-specific configuration with provided defaults
        try:
            if ch_type == ChannelType.DINGTALK:
                channel = _add_dingtalk_interactive(
                    channel_id, name,
                    default_webhook=webhook,
                    default_secret=secret,
                    default_keywords=keywords
                )
            elif ch_type == ChannelType.LARK:
                channel = _add_lark_interactive(
                    channel_id, name,
                    default_webhook=webhook,
                    default_secret=secret
                )
            elif ch_type == ChannelType.EMAIL:
                channel = _add_email_interactive(
                    channel_id, name,
                    default_smtp_host=smtp_host,
                    default_smtp_port=smtp_port,
                    default_username=username,
                    default_password=password,
                    default_use_tls=use_tls,
                    default_from=from_address,
                    default_to=to_addresses.split(",") if to_addresses else []
                )
        except typer.Abort:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()
    else:
        # Non-interactive mode - require all mandatory parameters
        if not channel_id or not name:
            OutputManager.error("--id and --name are required in non-interactive mode")
            raise typer.Exit(code=1)

        if store.exists(channel_id):
            OutputManager.error(f"Channel ID '{channel_id}' already exists")
            raise typer.Exit(code=1)

        # Create channel with provided parameters
        if ch_type == ChannelType.DINGTALK:
            if not webhook:
                OutputManager.error("--webhook is required for dingtalk in non-interactive mode")
                raise typer.Exit(code=1)
            channel = DingtalkChannel(
                id=channel_id,
                name=name,
                webhook_url=webhook,
                keywords=keywords or "",
                secret=secret or "",
            )
        elif ch_type == ChannelType.LARK:
            if not webhook:
                OutputManager.error("--webhook is required for lark in non-interactive mode")
                raise typer.Exit(code=1)
            channel = LarkChannel(
                id=channel_id,
                name=name,
                webhook_url=webhook,
                secret=secret or "",
            )
        else:  # EMAIL
            if not smtp_host or not username or not password:
                OutputManager.error("--smtp-host, --username, and --password are required for email")
                raise typer.Exit(code=1)
            channel = EmailChannel(
                id=channel_id,
                name=name,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                username=username,
                password=password,
                use_tls=use_tls,
                from_address=from_address,
                to_addresses=to_addresses.split(",") if to_addresses else [],
            )

    # Save channel
    store.add(channel)
    console.print(f"[green]✓[/green] Channel '{channel_id}' added successfully.")


def _add_dingtalk_interactive(
    channel_id: str, name: str,
    default_webhook: Optional[str] = None,
    default_secret: Optional[str] = None,
    default_keywords: Optional[str] = None
) -> DingtalkChannel:
    """Interactive setup for DingTalk channel."""
    console.print("\n[bold]DingTalk Configuration:[/bold]")

    webhook_url = Prompt.ask(
        "Webhook URL",
        default=default_webhook or "https://oapi.dingtalk.com/robot/send?access_token=",
    )

    keywords = Prompt.ask("Keywords (optional)", default=default_keywords or "")

    if default_secret:
        has_secret = Confirm.ask("Use provided secret?", default=True)
        secret = default_secret if has_secret else ""
        if not has_secret:
            has_secret = Confirm.ask("Does your bot have a secret?", default=False)
            if has_secret:
                secret = Prompt.ask("Bot secret", password=True)
    else:
        has_secret = Confirm.ask("Does your bot have a secret?", default=False)
        secret = ""
        if has_secret:
            secret = Prompt.ask("Bot secret", password=True)

    return DingtalkChannel(
        id=channel_id,
        name=name,
        webhook_url=webhook_url,
        keywords=keywords,
        secret=secret,
    )


def _add_lark_interactive(
    channel_id: str, name: str,
    default_webhook: Optional[str] = None,
    default_secret: Optional[str] = None
) -> LarkChannel:
    """Interactive setup for Lark channel."""
    console.print("\n[bold]Lark Configuration:[/bold]")

    webhook_url = Prompt.ask(
        "Webhook URL",
        default=default_webhook or "https://open.feishu.cn/open-apis/bot/v2/hook/",
    )

    if default_secret:
        has_secret = Confirm.ask("Use provided secret?", default=True)
        secret = default_secret if has_secret else ""
        if not has_secret:
            has_secret = Confirm.ask("Does your bot have a secret?", default=False)
            if has_secret:
                secret = Prompt.ask("Bot secret", password=True)
    else:
        has_secret = Confirm.ask("Does your bot have a secret?", default=False)
        secret = ""
        if has_secret:
            secret = Prompt.ask("Bot secret", password=True)

    return LarkChannel(
        id=channel_id,
        name=name,
        webhook_url=webhook_url,
        secret=secret,
    )


def _add_email_interactive(
    channel_id: str, name: str,
    default_smtp_host: Optional[str] = None,
    default_smtp_port: int = 587,
    default_username: Optional[str] = None,
    default_password: Optional[str] = None,
    default_use_tls: bool = True,
    default_from: Optional[str] = None,
    default_to: Optional[list] = None
) -> EmailChannel:
    """Interactive setup for Email channel."""
    console.print("\n[bold]Email (SMTP) Configuration:[/bold]")

    smtp_host = Prompt.ask("SMTP Host", default=default_smtp_host or "smtp.gmail.com")
    smtp_port = int(Prompt.ask("SMTP Port", default=str(default_smtp_port)))

    use_tls = Confirm.ask("Use TLS?", default=default_use_tls)
    use_ssl = Confirm.ask("Use SSL?", default=False) if not use_tls else False

    username = Prompt.ask("Username (email)", default=default_username or "")
    
    if default_password:
        use_default_pass = Confirm.ask("Use provided password?", default=True)
        password = default_password if use_default_pass else Prompt.ask("Password", password=True)
    else:
        password = Prompt.ask("Password", password=True)

    default_from_val = default_from or username
    from_address = Prompt.ask(
        "From address (optional, defaults to username)",
        default=default_from_val,
    )

    return EmailChannel(
        id=channel_id,
        name=name,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        username=username,
        password=password,
        use_tls=use_tls,
        use_ssl=use_ssl,
        from_address=from_address if from_address != username else None,
    )


@app.command("remove")
def remove_channel(
    channel_id: str = typer.Argument(..., help="Channel ID to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a channel configuration."""
    store = get_channel_store()

    channel = store.get(channel_id)
    if not channel:
        OutputManager.error(f"Channel '{channel_id}' not found")
        raise typer.Exit(code=1)

    if not force:
        confirm = Confirm.ask(
            f"Are you sure you want to remove channel '{channel.name}' ({channel_id})?",
            default=False,
        )
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    if store.remove(channel_id):
        console.print(f"[green]✓[/green] Channel '{channel_id}' removed.")
    else:
        OutputManager.error(f"Failed to remove channel '{channel_id}'")
        raise typer.Exit(code=1)


@app.command("test")
def test_channel(
    channel_id: str = typer.Argument(..., help="Channel ID to test"),
):
    """Test channel connectivity."""
    store = get_channel_store()

    channel = store.get(channel_id)
    if not channel:
        OutputManager.error(f"Channel '{channel_id}' not found")
        raise typer.Exit(code=1)

    console.print(f"Testing channel: [bold]{channel.name}[/bold] ({channel_id})")
    console.print(f"Type: {channel.type.value}")
    console.print()

    with console.status("[bold green]Sending test message..."):
        start_time = time.time()
        success, error = channel.test_connection()
        response_time = (time.time() - start_time) * 1000

    if success:
        console.print(f"[green]✓[/green] Test successful! ({response_time:.0f}ms)")
    else:
        console.print(f"[red]✗[/red] Test failed: {error}")
        raise typer.Exit(code=1)


@app.command("send")
def send_message(
    channel_id: str = typer.Argument(..., help="Channel ID to send through"),
    message: list[str] = typer.Argument(..., help="Message to send"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Message title (for markdown)"),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Send as markdown"),
):
    """Send a message through a channel."""
    store = get_channel_store()
    
    # Join message parts into a single string
    message_text = " ".join(message)

    channel = store.get(channel_id)
    if not channel:
        OutputManager.error(f"Channel '{channel_id}' not found")
        raise typer.Exit(code=1)

    if not channel.enabled:
        OutputManager.error(f"Channel '{channel_id}' is disabled")
        raise typer.Exit(code=1)

    sender = ChannelSender()

    with console.status(f"[bold green]Sending message through {channel_id}..."):
        result = sender.send(channel, message_text, title=title, markdown=markdown)

    if result.success:
        console.print(f"[green]✓[/green] Message sent successfully")
        if result.message_id:
            console.print(f"  Message ID: {result.message_id}")
    else:
        console.print(f"[red]✗[/red] Failed to send: {result.error}")
        raise typer.Exit(code=1)


@app.command("default")
def set_default(
    send: Optional[str] = typer.Option(None, "--send", "-s", help="Default channel for sending"),
    receive: Optional[str] = typer.Option(None, "--receive", "-r", help="Default channels for receiving (comma-separated)"),
):
    """Set default channels."""
    store = get_channel_store()

    # Validate channels exist
    if send and not store.exists(send):
        OutputManager.error(f"Send channel '{send}' not found")
        raise typer.Exit(code=1)

    receive_list = None
    if receive:
        receive_list = [r.strip() for r in receive.split(",")]
        for rid in receive_list:
            if not store.exists(rid):
                OutputManager.error(f"Receive channel '{rid}' not found")
                raise typer.Exit(code=1)

    store.set_defaults(send=send, receive=receive_list)

    console.print("[green]✓[/green] Defaults updated.")
    if send:
        console.print(f"  Send: {send}")
    if receive_list:
        console.print(f"  Receive: {', '.join(receive_list)}")


@app.command("show")
def show_channel(
    channel_id: str = typer.Argument(..., help="Channel ID to show"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show detailed channel configuration."""
    store = get_channel_store()

    channel = store.get(channel_id)
    if not channel:
        OutputManager.error(f"Channel '{channel_id}' not found")
        raise typer.Exit(code=1)

    if json:
        OutputManager.print(channel.model_dump(mode="json"))
        return

    icon = _get_type_icon(channel.type)
    status_color, status_text = _get_status_style(channel.enabled)

    console.print(Panel.fit(f"{icon} {channel.name}", style="blue"))

    table = Table(show_header=False, border_style="dim")
    table.add_column("Field", style="bold", width=15)
    table.add_column("Value")

    table.add_row("ID", channel.id)
    table.add_row("Type", channel.type.value)
    table.add_row("Status", f"[{status_color}]{status_text}[/{status_color}]")
    table.add_row("Created", channel.created_at.strftime("%Y-%m-%d %H:%M:%S"))

    if channel.updated_at:
        table.add_row("Updated", channel.updated_at.strftime("%Y-%m-%d %H:%M:%S"))

    # Type-specific fields
    if isinstance(channel, DingtalkChannel):
        table.add_row("Webhook URL", channel.webhook_url[:50] + "..." if len(channel.webhook_url) > 50 else channel.webhook_url)
        if channel.keywords:
            table.add_row("Keywords", channel.keywords)
        if channel.secret:
            table.add_row("Secret", "*" * 10)
    elif isinstance(channel, LarkChannel):
        table.add_row("Webhook URL", channel.webhook_url[:50] + "..." if len(channel.webhook_url) > 50 else channel.webhook_url)
        if channel.secret:
            table.add_row("Secret", "*" * 10)
    elif isinstance(channel, EmailChannel):
        table.add_row("SMTP Host", f"{channel.smtp_host}:{channel.smtp_port}")
        table.add_row("Username", channel.username)
        table.add_row("Password", "*" * 10)
        table.add_row("TLS", "Yes" if channel.use_tls else "No")
        table.add_row("SSL", "Yes" if channel.use_ssl else "No")
        if channel.from_address:
            table.add_row("From", channel.from_address)

    console.print(table)


@app.command("migrate")
def migrate_command(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be migrated without making changes"),
    channel_id: str = typer.Option("dingtalk-default", "--id", help="Channel ID for migrated config"),
    channel_name: str = typer.Option("DingTalk (migrated)", "--name", "-n", help="Channel display name"),
    status: bool = typer.Option(False, "--status", "-s", help="Show migration status only"),
):
    """Migrate notification configuration from .env to channels.yaml."""
    from pathlib import Path
    from monoco.core.config import find_monoco_root

    if status:
        project_root = find_monoco_root()
        show_migration_status(project_root)
        return

    project_root = find_monoco_root()

    success, messages = migrate_from_env(
        project_root=project_root,
        dry_run=dry_run,
        channel_id=channel_id,
        channel_name=channel_name,
    )

    for msg in messages:
        if msg.startswith("✓"):
            console.print(f"[green]{msg}[/green]")
        elif msg.startswith("["):
            console.print(msg)
        elif "Error" in msg or "not found" in msg.lower():
            console.print(f"[yellow]{msg}[/yellow]")
        else:
            console.print(msg)

    if not success:
        raise typer.Exit(code=1)
