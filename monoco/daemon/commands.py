import typer
import uvicorn
import os
from monoco.core.output import print_output
from monoco.core.config import get_config

def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8642, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload for dev"),
):
    """
    Start the Monoco Daemon server.
    """
    settings = get_config()
    print_output(f"Starting Monoco Daemon on http://{host}:{port}", title="Monoco Serve")
    
    # We pass the import string to uvicorn to enable reload if needed
    app_str = "monoco.daemon.app:app"
    
    uvicorn.run(
        app_str, 
        host=host, 
        port=port, 
        reload=reload,
        log_level="info"
    )
