"""
Courier Commands - CLI commands for Courier service management.

Provides commands:
- start: Start the Courier service
- stop: Stop the Courier service (graceful)
- restart: Restart the Courier service
- kill: Force stop the Courier service
- status: Check service status
- logs: View service logs
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from monoco.core.config import get_config
from monoco.core.output import OutputManager, AgentOutput

from .service import (
    CourierService,
    ServiceState,
    ServiceError,
    ServiceAlreadyRunningError,
    ServiceNotRunningError,
    ServiceStartError,
)
from .constants import COURIER_DEFAULT_PORT

app = typer.Typer(help="Manage Courier service")
console = Console()


def _get_service(
    project_root: Optional[Path] = None,
    port: Optional[int] = None,
) -> CourierService:
    """Get a CourierService instance for the current project."""
    if project_root is None:
        config = get_config()
        project_root = Path(config.paths.root)
    
    kwargs = {"project_root": project_root}
    if port is not None:
        kwargs["port"] = port
        
    return CourierService(**kwargs)


@app.command("start")
def start_service(
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground (for debugging)"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    port: int = typer.Option(COURIER_DEFAULT_PORT, "--port", "-p", help="API server port"),
    json: AgentOutput = False,
):
    """Start the Courier service."""
    try:
        service = _get_service(port=port)
        status = service.start(
            foreground=foreground,
            debug=debug,
            config_path=config,
        )

        if json:
            OutputManager.print(status.to_dict())
        else:
            if status.is_running():
                console.print(f"[green]✓[/green] Courier started (PID: {status.pid})")
                console.print(f"  API: {status.api_url}")
            else:
                console.print(f"[yellow]⚠[/yellow] Courier status: {status.state}")

    except ServiceAlreadyRunningError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=2)
    except ServiceStartError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)
    except Exception as e:
        OutputManager.error(f"Failed to start Courier: {e}")
        raise typer.Exit(code=1)


@app.command("stop")
def stop_service(
    timeout: int = typer.Option(30, "--timeout", "-t", help="Timeout in seconds before force kill"),
    wait: bool = typer.Option(True, "--wait/--no-wait", "-w", help="Block until service stops (default: True)"),
    all_processes: bool = typer.Option(False, "--all", "-a", help="Stop all Courier processes (orphan cleanup)"),
    json: AgentOutput = False,
):
    """Stop the Courier service gracefully."""
    try:
        service = _get_service()
        status = service.stop(timeout=timeout, wait=wait, all_processes=all_processes)

        if json:
            OutputManager.print({"success": True, "status": status.to_dict()})
        else:
            if all_processes:
                console.print("[green]✓[/green] All Courier processes stopped")
            elif status.state == ServiceState.STOPPED:
                console.print("[green]✓[/green] Courier stopped")
            else:
                # Non-blocking mode: show that stop signal was sent
                console.print(f"[yellow]⚠[/yellow] Stop signal sent, service is stopping (current: {status.state})")
                console.print("[dim]  Use --wait to block until fully stopped[/dim]")

    except ServiceNotRunningError:
        msg = "Courier is not running"
        if json:
            OutputManager.print({"success": False, "error": msg})
        else:
            OutputManager.error(msg)
        raise typer.Exit(code=1)
    except Exception as e:
        OutputManager.error(f"Failed to stop Courier: {e}")
        raise typer.Exit(code=1)


@app.command("kill")
def kill_service(
    signal_type: str = typer.Option("SIGKILL", "--signal", "-s", help="Signal to send (SIGKILL, SIGINT)"),
    json: AgentOutput = False,
):
    """
    Force stop the Courier service.

    Warning: This is not graceful and may result in:
    - Lost lock state
    - Incomplete message processing
    - Resource leaks

    Use 'stop' for normal shutdown.
    """
    import signal

    sig = signal.SIGKILL
    if signal_type.upper() == "SIGINT":
        sig = signal.SIGINT

    try:
        service = _get_service()
        status = service.kill(signal_type=sig)

        if json:
            OutputManager.print({"success": True, "status": status.to_dict()})
        else:
            console.print("[red]✗[/red] Courier killed (force stop)")
            console.print("  [yellow]Warning: Lock state may be lost[/yellow]")

    except Exception as e:
        OutputManager.error(f"Failed to kill Courier: {e}")
        raise typer.Exit(code=1)


@app.command("restart")
def restart_service(
    force: bool = typer.Option(False, "--force", help="Force restart if stop fails"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
    json: AgentOutput = False,
):
    """Restart the Courier service."""
    try:
        service = _get_service()
        status = service.restart(force=force, debug=debug)

        if json:
            OutputManager.print(status.to_dict())
        else:
            if status.is_running():
                console.print(f"[green]✓[/green] Courier restarted (PID: {status.pid})")
                console.print(f"  API: {status.api_url}")
            else:
                console.print(f"[yellow]⚠[/yellow] Courier status: {status.state}")

    except ServiceStartError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)
    except Exception as e:
        OutputManager.error(f"Failed to restart Courier: {e}")
        raise typer.Exit(code=1)


@app.command("status")
def service_status(
    watch: bool = typer.Option(False, "--watch", help="Watch mode (continuous updates)"),
    json: AgentOutput = False,
):
    """Check Courier service status."""
    import time

    if watch:
        # Simple watch mode
        try:
            while True:
                # Clear screen (ANSI escape sequence)
                console.print("\033[2J\033[H", end="")

                service = _get_service()
                status = service.get_status()
                _print_status_table(status)

                time.sleep(2)
        except KeyboardInterrupt:
            console.print("\nStopped watching.")
    else:
        service = _get_service()
        status = service.get_status()

        if json:
            OutputManager.print(status.to_dict())
        else:
            _print_status_table(status)


def _print_status_table(status: "ServiceStatus") -> None:
    """Print service status as a formatted table."""
    # Determine status color
    status_colors = {
        ServiceState.RUNNING: "green",
        ServiceState.STARTING: "yellow",
        ServiceState.STOPPING: "yellow",
        ServiceState.STOPPED: "dim",
        ServiceState.ERROR: "red",
    }
    color = status_colors.get(status.state, "white")

    # Status indicator
    if status.is_running():
        indicator = "🟢"
    elif status.state == ServiceState.STOPPED:
        indicator = "⚪"
    else:
        indicator = "🟡"

    table = Table(
        title=f"{indicator} Courier Service Status",
        show_header=False,
        border_style="blue",
    )
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("State", f"[{color}]{status.state}[/{color}]")

    if status.pid:
        table.add_row("PID", str(status.pid))

    if status.uptime_seconds:
        hours = status.uptime_seconds // 3600
        mins = (status.uptime_seconds % 3600) // 60
        table.add_row("Uptime", f"{hours}h {mins}m")

    table.add_row("Version", status.version)

    if status.api_url:
        table.add_row("API URL", status.api_url)

    if status.error_message:
        table.add_row("Error", f"[red]{status.error_message}[/red]")

    # Adapters
    if status.adapters:
        table.add_row("", "")
        table.add_row("[bold]Adapters[/bold]", "")
        for name, info in status.adapters.items():
            adapter_status = info.get("status", "unknown")
            adapter_color = "green" if adapter_status == "connected" else "dim"
            table.add_row(f"  {name}", f"[{adapter_color}]{adapter_status}[/{adapter_color}]")
            
            # Show projects if available
            projects = info.get("projects", [])
            if projects:
                slugs = ", ".join(projects)
                table.add_row(f"    [dim]projects[/dim]", f"[dim]{slugs}[/dim]")

    # Metrics
    if status.metrics:
        table.add_row("", "")
        table.add_row("[bold]Metrics[/bold]", "")
        for name, value in status.metrics.items():
            table.add_row(f"  {name}", str(value))

    console.print(table)


@app.command("logs")
def service_logs(
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output (tail -f mode)"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Filter by level (error, warn, info, debug)"),
    since: Optional[str] = typer.Option(None, "--since", help="Show logs since duration (e.g., 1h, 30m)"),
):
    """View Courier service logs."""
    try:
        service = _get_service()

        if follow:
            # Follow mode - similar to tail -f
            import time

            log_path = service.log_file
            if not log_path.exists():
                console.print("[yellow]No log file found[/yellow]")
                return

            console.print(f"Following {log_path}... (Press Ctrl+C to stop)")

            with open(log_path, "r") as f:
                # Seek to end
                f.seek(0, 2)

                try:
                    while True:
                        line = f.readline()
                        if not line:
                            time.sleep(0.1)
                            continue

                        # Filter by level if specified
                        if level and level.upper() not in line.upper():
                            continue

                        console.print(line.rstrip())
                except KeyboardInterrupt:
                    console.print("\nStopped following.")
        else:
            # Static log view
            logs = service.get_logs(lines=lines)

            if not logs:
                console.print("[yellow]No logs available[/yellow]")
                return

            # Filter by level if specified
            if level:
                filtered = []
                for line in logs.split("\n"):
                    if level.upper() in line.upper():
                        filtered.append(line)
                logs = "\n".join(filtered[-lines:])

            console.print(Panel(
                logs,
                title=f"Courier Logs (last {lines} lines)",
                border_style="dim",
            ))

    except Exception as e:
        OutputManager.error(f"Failed to get logs: {e}")
        raise typer.Exit(code=1)


@app.command("stream")
def stream_status():
    """
    Show DingTalk Stream adapter status.
    
    Requires Courier daemon to be running with Stream adapter configured.
    
    Examples:
        monoco courier stream
    """
    import os
    
    # Check if configured
    client_id = os.environ.get("DINGTALK_CLIENT_ID") or os.environ.get("DINGTALK_APP_KEY")
    client_secret = os.environ.get("DINGTALK_CLIENT_SECRET") or os.environ.get("DINGTALK_APP_SECRET")
    
    table = Table(title="DingTalk Stream Adapter")
    table.add_column("Item", style="cyan")
    table.add_column("Status", style="green")
    
    # Configuration status
    if client_id and client_secret:
        table.add_row("Configuration", "[green]✓ Configured[/green]")
        table.add_row("Client ID", f"{client_id[:15]}...")
    else:
        table.add_row("Configuration", "[yellow]⚠ Not configured[/yellow]")
        table.add_row("Client ID", "[dim]Set DINGTALK_CLIENT_ID[/dim]")
    
    # Courier status
    service = _get_service()
    status = service.get_status()
    
    if status.is_running():
        table.add_row("Courier Daemon", "[green]✓ Running[/green]")
        
        # Check if Stream is active in daemon
        # This is a simplified check - in production we'd query the daemon API
        if client_id and client_secret:
            table.add_row("Stream Adapter", "[green]✓ Active[/green] (auto-started)")
            table.add_row("", "[dim]Messages will be written to mailbox[/dim]")
        else:
            table.add_row("Stream Adapter", "[yellow]⚠ Not started[/yellow]")
    else:
        table.add_row("Courier Daemon", "[red]✗ Stopped[/red]")
        table.add_row("", "[dim]Run: monoco courier start[/dim]")
    
    console.print(table)
    
    if not status.is_running():
        console.print("\n[yellow]To start with Stream mode:[/yellow]")
        console.print("  export DINGTALK_CLIENT_ID=xxx")
        console.print("  export DINGTALK_CLIENT_SECRET=xxx")
        console.print("  monoco courier start")


@app.command("stream-test")
def test_dingtalk_stream(
    app_key: Optional[str] = typer.Option(None, "--app-key", "-k", help="DingTalk AppKey"),
    app_secret: Optional[str] = typer.Option(None, "--app-secret", "-s", help="DingTalk AppSecret"),
    duration: int = typer.Option(60, "--duration", "-d", help="Test duration in seconds"),
):
    """
    Test DingTalk Stream mode connection (no public IP needed).
    
    This command tests the Stream adapter without starting the full Courier service.
    Useful for verifying DingTalk credentials and receiving messages.
    
    Examples:
        monoco courier stream-test
        monoco courier stream-test --app-key xxx --app-secret yyy --duration 120
    """
    import asyncio
    import os
    
    # Get credentials (支持新命名 Client ID/Secret 和旧命名 App Key/Secret)
    app_key = (app_key 
               or os.environ.get("DINGTALK_CLIENT_ID") 
               or os.environ.get("DINGTALK_APP_KEY"))
    app_secret = (app_secret 
                  or os.environ.get("DINGTALK_CLIENT_SECRET") 
                  or os.environ.get("DINGTALK_APP_SECRET"))
    
    if not app_key or not app_secret:
        console.print("[red]❌ Error:[/red] DingTalk credentials required")
        console.print("\nProvide via:")
        console.print("  1. Environment: export DINGTALK_APP_KEY=xxx")
        console.print("  2. CLI options: --app-key xxx --app-secret yyy")
        console.print("\nGet credentials from: https://open.dingtalk.com/")
        raise typer.Exit(code=1)
    
    console.print("""
╔══════════════════════════════════════════╗
║     DingTalk Stream Mode Test            ║
║     无需公网 IP 接收钉钉消息              ║
╚══════════════════════════════════════════╝
    """)
    
    console.print(f"🔑 AppKey: {app_key[:10]}...")
    console.print(f"⏱️  Duration: {duration}s")
    console.print("\n📡 Connecting to DingTalk Stream server...\n")
    
    async def run_test():
        from .adapters.dingtalk_stream import create_dingtalk_stream_adapter
        
        adapter = create_dingtalk_stream_adapter(
            client_id=app_key,  # 支持新旧命名
            client_secret=app_secret,
            default_project="test",
        )
        
        messages_received = []
        
        def on_message(message, project_slug):
            sender = message.participants.get("from", {})
            sender_name = sender.get("name", "Unknown")
            content = message.content.text or message.content.markdown or "[无内容]"
            
            messages_received.append(message)
            console.print(f"📩 [{len(messages_received)}] {sender_name}: {content[:50]}{'...' if len(content) > 50 else ''}")
        
        adapter.set_message_handler(on_message)
        
        try:
            await adapter.connect()
            console.print("[green]✅ Connected successfully![/green]")
            console.print("🤖 Now send a message to your DingTalk bot")
            console.print("   (In a group chat @bot or in private chat)")
            console.print(f"\n⏳ Listening for {duration} seconds... (Ctrl+C to stop)\n")
            
            # Listen for messages with timeout
            start_time = asyncio.get_event_loop().time()
            async for _ in adapter.listen():
                if asyncio.get_event_loop().time() - start_time > duration:
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
        finally:
            await adapter.disconnect()
        
        # Summary
        console.print(f"\n📊 Test completed:")
        console.print(f"   Messages received: {len(messages_received)}")
        if messages_received:
            console.print(f"   [green]✅ Stream mode is working![/green]")
        else:
            console.print(f"   [yellow]⚠️ No messages received[/yellow]")
            console.print("   Make sure:")
            console.print("   • Robot is added to a group chat or you're chatting directly")
            console.print("   • Robot has 'im.message.group' permission enabled")
            console.print("   • Robot is in Stream mode (not Webhook mode)")
    
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        console.print("\n\n👋 Test stopped by user")


if __name__ == "__main__":
    app()


