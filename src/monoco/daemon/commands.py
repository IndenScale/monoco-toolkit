"""Monoco Daemon CLI commands for process management and service governance."""

import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from monoco.core.config import get_config
from monoco.core.daemon.pid import PIDManager, PortManager, PIDFileError
from monoco.core.output import print_output

console = Console()

# Create serve subcommand app
serve_app = typer.Typer(
    name="serve",
    help="Monoco Daemon server management",
    no_args_is_help=True,
)


def _get_project_root(root: Optional[str] = None) -> Path:
    """Get Project root path."""
    if root:
        return Path(root).resolve()
    env_root = os.getenv("MONOCO_SERVER_ROOT")
    if env_root:
        return Path(env_root)
    return Path.cwd()


def _setup_signal_handlers(pid_manager: PIDManager):
    """Setup signal handlers for graceful shutdown.
    
    Note: We don't call sys.exit() here to allow uvicorn's graceful shutdown
    to complete, which will execute the lifespan shutdown code and properly
    stop all services (watchers, scheduler, etc.).
    """

    def signal_handler(signum, frame):
        console.print(f"\n[yellow]Received signal {signum}, shutting down gracefully...[/yellow]")
        # Only remove PID file here; let uvicorn handle the rest
        # The lifespan shutdown in app.py will stop all services
        pid_manager.remove_pid_file()
        # Don't call sys.exit() - let uvicorn's signal handler continue
        # to execute the shutdown sequence properly

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def _daemonize(
    project_root: Path,
    host: str,
    port: int,
    log_file: Optional[Path] = None,
) -> int:
    """Daemonize the current process using double-fork technique.

    Args:
        project_root: Project root path
        host: Host to bind
        port: Port to bind
        log_file: Optional log file path (defaults to .monoco/log/daemon.log)

    Returns:
        Parent process returns child PID, child process returns 0
    """
    if log_file is None:
        log_dir = project_root / ".monoco" / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "daemon.log"

    # First fork
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process: wait a moment to check if child started successfully
            time.sleep(0.5)
            return pid
    except OSError as e:
        console.print(f"[red]Fork #1 failed: {e}[/red]")
        sys.exit(1)

    # Child process continues
    os.chdir(str(project_root))
    os.setsid()  # Create new session, detach from terminal

    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            # First child exits
            sys.exit(0)
    except OSError as e:
        console.print(f"[red]Fork #2 failed: {e}[/red]")
        sys.exit(1)

    # Grandchild process continues
    # Redirect stdout/stderr to log file
    sys.stdout.flush()
    sys.stderr.flush()

    with open(log_file, "a+") as log:
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())

    return 0


def serve_start(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8642, "--port", "-p", help="Bind port"),
    daemon: bool = typer.Option(
        False, "--daemon", "-d", help="Run as background daemon"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Project root directory"
    ),
    max_agents: Optional[int] = typer.Option(
        None, "--max-agents", help="Override global maximum concurrent agents"
    ),
    auto_port: bool = typer.Option(
        True, "--auto-port/--no-auto-port", help="Automatically find available port if default is in use"
    ),
):
    """Start the Monoco Daemon server."""
    project_root = _get_project_root(root)
    pid_manager = PIDManager(project_root)

    # Check if already running
    existing = pid_manager.get_daemon_info()
    if existing:
        console.print(
            f"[yellow]Daemon already running (PID: {existing['pid']}, "
            f"http://{existing['host']}:{existing['port']})[/yellow]"
        )
        raise typer.Exit(code=0)

    # Handle port selection
    try:
        if auto_port and PortManager.is_port_in_use(port, host):
            new_port = PortManager.find_available_port(port + 1, host)
            console.print(
                f"[yellow]Port {port} is in use, using port {new_port} instead[/yellow]"
            )
            port = new_port
        elif not auto_port and PortManager.is_port_in_use(port, host):
            console.print(f"[red]Error: Port {port} is already in use[/red]")
            raise typer.Exit(code=1)
    except PIDFileError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # Set environment variables
    os.environ["MONOCO_SERVER_ROOT"] = str(project_root)
    if max_agents is not None:
        os.environ["MONOCO_MAX_AGENTS"] = str(max_agents)

    if daemon:
        # Daemonize
        log_dir = project_root / ".monoco" / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "daemon.log"

        pid = _daemonize(project_root, host, port, log_file)
        if pid > 0:
            # Parent process: show success message and exit
            console.print(f"[green]Daemon started (PID: {pid})[/green]")
            console.print(f"[dim]Logs: {log_file}[/dim]")
            console.print(f"[dim]URL: http://{host}:{port}[/dim]")
            raise typer.Exit(code=0)

        # Child process: continue to start server

    # Create PID file before starting server
    try:
        pid_file = pid_manager.create_pid_file(host, port)
    except PIDFileError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # Setup signal handlers for graceful shutdown in both modes
    # - Foreground: Ctrl+C (SIGINT) or SIGTERM
    # - Daemon: SIGTERM from `serve stop` command
    _setup_signal_handlers(pid_manager)

    try:
        console.print(
            f"[green]Starting Monoco Daemon on http://{host}:{port}[/green]"
        )
        if daemon:
            print(
                f"[{datetime.now().isoformat()}] Daemon started on {host}:{port}",
                flush=True,
            )

        app_str = "monoco.daemon.app:app"
        uvicorn.run(
            app_str,
            host=host,
            port=port,
            reload=False,
            log_level="info",
        )
    finally:
        pid_manager.remove_pid_file()


def serve_stop(
    root: Optional[str] = typer.Option(None, "--root", help="Project root directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Force kill the daemon"),
):
    """Stop the running Monoco Daemon."""
    project_root = _get_project_root(root)
    pid_manager = PIDManager(project_root)

    daemon_info = pid_manager.get_daemon_info()
    if not daemon_info:
        console.print("[yellow]Daemon is not running[/yellow]")
        raise typer.Exit(code=0)

    pid = daemon_info["pid"]
    console.print(f"Stopping daemon (PID: {pid})...")

    if force:
        success = pid_manager.send_signal(signal.SIGKILL)
    else:
        success = pid_manager.terminate(timeout=5)

    if success:
        console.print("[green]Daemon stopped successfully[/green]")
    else:
        console.print("[red]Failed to stop daemon[/red]")
        raise typer.Exit(code=1)


def serve_status(
    root: Optional[str] = typer.Option(None, "--root", help="Project root directory"),
):
    """Show the status of the Monoco Daemon."""
    project_root = _get_project_root(root)
    pid_manager = PIDManager(project_root)

    daemon_info = pid_manager.get_daemon_info()

    if not daemon_info:
        console.print("[yellow]Daemon is not running[/yellow]")
        console.print(f"Project: {project_root}")
        raise typer.Exit(code=0)

    # Calculate uptime
    started_at = datetime.fromisoformat(daemon_info["started_at"])
    uptime = datetime.now() - started_at
    uptime_str = str(uptime).split(".")[0]  # Remove microseconds

    table = Table(title="Monoco Daemon Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Status", "Running")
    table.add_row("PID", str(daemon_info["pid"]))
    table.add_row("Host", daemon_info["host"])
    table.add_row("Port", str(daemon_info["port"]))
    table.add_row("URL", f"http://{daemon_info['host']}:{daemon_info['port']}")
    table.add_row("Version", daemon_info.get("version", "unknown"))
    table.add_row("Started At", daemon_info["started_at"])
    table.add_row("Uptime", uptime_str)
    table.add_row("Project", str(project_root))

    console.print(table)


def serve_restart(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8642, "--port", "-p", help="Bind port"),
    daemon: bool = typer.Option(
        False, "--daemon", "-d", help="Run as background daemon"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Project root directory"
    ),
    max_agents: Optional[int] = typer.Option(
        None, "--max-agents", help="Override global maximum concurrent agents"
    ),
    auto_port: bool = typer.Option(
        True, "--auto-port/--no-auto-port", help="Automatically find available port if default is in use"
    ),
):
    """Restart the Monoco Daemon."""
    project_root = _get_project_root(root)
    pid_manager = PIDManager(project_root)

    # Stop if running
    if pid_manager.get_daemon_info():
        console.print("Stopping existing daemon...")
        serve_stop(root=root)
        time.sleep(1)  # Wait for process to fully terminate

    # Start new daemon
    serve_start(
        host=host,
        port=port,
        daemon=daemon,
        root=root,
        max_agents=max_agents,
        auto_port=auto_port,
    )


def serve_cleanup(
    root: Optional[str] = typer.Option(None, "--root", help="Project root directory"),
    port: int = typer.Option(8642, "--port", "-p", help="Default port to check for orphans"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be cleaned without actually doing it"
    ),
):
    """Clean up orphaned daemon processes.

    Scans for and terminates orphaned uvicorn processes that may have been
    left behind when terminals were closed without proper shutdown.
    """
    project_root = _get_project_root(root)
    pid_manager = PIDManager(project_root)

    cleaned = []
    errors = []

    # Check PID file first
    pid_data = pid_manager.read_pid_file()
    if pid_data:
        pid = pid_data["pid"]
        if not PIDManager.is_process_alive(pid):
            if not dry_run:
                pid_manager.remove_pid_file()
            cleaned.append(f"Stale PID file (PID: {pid})")

    # Find uvicorn processes
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True,
        )

        for line in result.stdout.splitlines():
            if "uvicorn" in line.lower() and "monoco.daemon.app" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        uvicorn_pid = int(parts[1])
                        # Check if this is the current valid daemon
                        if pid_data and uvicorn_pid == pid_data["pid"]:
                            continue

                        proc_info = " ".join(parts[10:]) if len(parts) > 10 else line

                        if not dry_run:
                            try:
                                os.kill(uvicorn_pid, signal.SIGTERM)
                                # Wait briefly for graceful termination
                                time.sleep(0.5)
                                if PIDManager.is_process_alive(uvicorn_pid):
                                    os.kill(uvicorn_pid, signal.SIGKILL)
                                cleaned.append(f"Orphan uvicorn (PID: {uvicorn_pid}): {proc_info[:50]}...")
                            except (OSError, ProcessLookupError) as e:
                                errors.append(f"Failed to kill PID {uvicorn_pid}: {e}")
                        else:
                            cleaned.append(f"[DRY RUN] Orphan uvicorn (PID: {uvicorn_pid}): {proc_info[:50]}...")
                    except (ValueError, IndexError):
                        continue

    except subprocess.SubprocessError as e:
        console.print(f"[red]Error scanning processes: {e}[/red]")
        raise typer.Exit(code=1)

    # Check for port conflicts
    for check_port in range(port, port + 10):
        if PortManager.is_port_in_use(check_port, "127.0.0.1"):
            # Try to find which process is using this port
            try:
                result = subprocess.run(
                    ["lsof", "-ti", f":{check_port}"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split("\n")
                    for pid_str in pids:
                        try:
                            pid = int(pid_str.strip())
                            # Skip if it's our known daemon
                            if pid_data and pid == pid_data["pid"]:
                                continue

                            if not dry_run:
                                try:
                                    os.kill(pid, signal.SIGTERM)
                                    cleaned.append(f"Process on port {check_port} (PID: {pid})")
                                except (OSError, ProcessLookupError):
                                    pass
                            else:
                                cleaned.append(f"[DRY RUN] Process on port {check_port} (PID: {pid})")
                        except ValueError:
                            continue
            except (subprocess.SubprocessError, FileNotFoundError):
                # lsof might not be available
                pass

    # Report results
    if cleaned:
        console.print(f"[green]Cleaned {len(cleaned)} item(s):[/green]")
        for item in cleaned:
            console.print(f"  - {item}")
    else:
        console.print("[green]No orphaned processes found[/green]")

    if errors:
        console.print(f"[yellow]Errors ({len(errors)}):[/yellow]")
        for error in errors:
            console.print(f"  - {error}")


def serve_legacy(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8642, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(
        False, "--reload", "-r", help="Enable auto-reload for dev"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Project root directory"
    ),
    max_agents: Optional[int] = typer.Option(
        None, "--max-agents", help="Override global maximum concurrent agents (default: 3)"
    ),
):
    """Start the Monoco Daemon server (legacy command, same as 'serve start')."""
    # For backward compatibility, --reload implies foreground mode
    if reload:
        project_root = _get_project_root(root)
        os.environ["MONOCO_SERVER_ROOT"] = str(project_root)
        if max_agents is not None:
            os.environ["MONOCO_MAX_AGENTS"] = str(max_agents)

        print_output(
            f"Starting Monoco Daemon on http://{host}:{port}", title="Monoco Serve"
        )

        app_str = "monoco.daemon.app:app"
        uvicorn.run(app_str, host=host, port=port, reload=reload, log_level="info")
    else:
        # Without --reload, use the new start command
        serve_start(
            host=host,
            port=port,
            daemon=False,
            root=root,
            max_agents=max_agents,
            auto_port=True,
        )


# Register subcommands
serve_app.command(name="start")(serve_start)
serve_app.command(name="stop")(serve_stop)
serve_app.command(name="status")(serve_status)
serve_app.command(name="restart")(serve_restart)
serve_app.command(name="cleanup")(serve_cleanup)

# Keep 'serve' as alias for 'serve start' for backward compatibility
serve = serve_legacy
