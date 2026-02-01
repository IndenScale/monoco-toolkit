import typer
import uvicorn
import os
from typing import Optional
from monoco.core.output import print_output
from monoco.core.config import get_config

from pathlib import Path


def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8642, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(
        False, "--reload", "-r", help="Enable auto-reload for dev"
    ),
    root: Optional[str] = typer.Option(None, "--root", help="Workspace root directory"),
    max_agents: Optional[int] = typer.Option(
        None, "--max-agents", help="Override global maximum concurrent agents (default: 3)"
    ),
):
    """
    Start the Monoco Daemon server.
    """
    settings = get_config()

    if root:
        os.environ["MONOCO_SERVER_ROOT"] = str(Path(root).resolve())
        print_output(
            f"Workspace Root: {os.environ['MONOCO_SERVER_ROOT']}", title="Monoco Serve"
        )
    
    # Set max agents override if provided
    if max_agents is not None:
        os.environ["MONOCO_MAX_AGENTS"] = str(max_agents)
        print_output(
            f"Max Agents: {max_agents}", title="Monoco Serve"
        )

    print_output(
        f"Starting Monoco Daemon on http://{host}:{port}", title="Monoco Serve"
    )

    # We pass the import string to uvicorn to enable reload if needed
    app_str = "monoco.daemon.app:app"

    uvicorn.run(app_str, host=host, port=port, reload=reload, log_level="info")
