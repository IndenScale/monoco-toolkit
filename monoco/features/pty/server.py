import logging
import signal
import sys
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from monoco.features.pty.router import router as pty_router, pty_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    logging.info("Shutting down PTY manager and cleaning up sessions...")
    pty_manager.close_all_sessions()

def run_pty_server(host: str = "127.0.0.1", port: int = 3124, cwd: Optional[Path] = None):
    """
    Entry point for the 'monoco pty' command.
    """
    # Configure Logging
    logging.basicConfig(level=logging.INFO)
    
    # Register a manual signal handler to ensure we catch termination even if uvicorn misses it
    # or if we are stuck before uvicorn starts.
    def handle_signal(signum, frame):
        logging.info(f"Received signal {signum}, initiating shutdown...")
        # We rely on uvicorn to handle the actual exit loop for SIGINT/SIGTERM usually,
        # but having this log confirms propagation.
        # If uvicorn is running, it should catch this first. 
        # If not, we exit manually.
        sys.exit(0)

    # Note: Uvicorn overwrites SIGINT/SIGTERM handlers by default. 
    # relying on lifespan is the standard "Uvicorn way".
    
    app = FastAPI(title="Monoco PTY Service", lifespan=lifespan)
    app.include_router(pty_router)
    
    # If cwd is provided, we might want to set it as current process CWD
    # so that new sessions default to it.
    if cwd and cwd.exists():
        import os
        os.chdir(cwd)
        logging.info(f"PTY Service Root: {cwd}")

    logging.info(f"Starting Monoco PTY Service on ws://{host}:{port}")
    try:
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        pass
    finally:
        # Final safety net
        pty_manager.close_all_sessions()
