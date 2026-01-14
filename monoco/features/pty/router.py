
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from typing import Optional, Dict
import json
import asyncio
import logging
import os
from pathlib import Path
from monoco.features.pty.core import PTYManager
from monoco.core.config import get_config

# We will use dependency injection or a global singleton for now
# Ideally attached to app state
pty_manager = PTYManager()

router = APIRouter(prefix="/api/v1/pty", tags=["pty"])

logger = logging.getLogger("monoco.pty")

@router.websocket("/ws/{session_id}")
async def websocket_pty_endpoint(
    websocket: WebSocket, 
    session_id: str,
    cwd: Optional[str] = Query(None),
    cols: int = Query(80), 
    rows: int = Query(24),
    env: Optional[str] = Query(None) # JSON-encoded env vars
):
    await websocket.accept()
    
    # Determine working directory
    # 1. Provide explicit CWD in query
    # 2. Or fallback to ProjectRoot from env (if integrated)
    # 3. Or fallback to process CWD
    
    # Since monoco pty runs as a separate service, we expect CWD to be passed
    # or we default to where monoco pty was started
    working_dir = cwd if cwd else os.getcwd()
    
    # Prepare environment
    env_vars = os.environ.copy()
    env_vars["TERM"] = "xterm-256color"
    env_vars["COLORTERM"] = "truecolor"
    if "SHELL" not in env_vars:
        env_vars["SHELL"] = "/bin/zsh"
    if "HOME" not in env_vars:
        import pathlib
        env_vars["HOME"] = str(pathlib.Path.home())

    # Filter out Trae/Gemini specific variables to avoid shell integration conflicts
    # This prevents the shell from trying to write to IDE-specific logs which causes EPERM
    keys_to_remove = [k for k in env_vars.keys() if k.startswith("TRAE_") or k.startswith("GEMINI_") or k == "AI_AGENT"]
    for k in keys_to_remove:
        del env_vars[k]

    if env:
        try:
            custom_env = json.loads(env)
            env_vars.update(custom_env)
        except:
            logger.warning("Failed to parse custom env vars")

    # Start Session
    try:
        session = pty_manager.create_session(
            session_id=session_id, 
            cwd=working_dir,
            cmd=["/bin/zsh", "-l"], # Use login shell to ensure full user environment
            env=env_vars
        )
        session.start(cols, rows)
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        await websocket.close(code=1011)
        return

    # Pipe Loop
    reader_task = None
    try:
        # Task to read from PTY and send to WebSocket
        async def pty_reader():
            while session.running:
                data = await session.read()
                if not data:
                    break
                # xterm.js expects string or binary. We send string/bytes.
                # Usually text is fine, but binary is safer for control codes.
                await websocket.send_bytes(data)
            
            # If PTY exits, close WS
            await websocket.close()

        reader_task = asyncio.create_task(pty_reader())

        # Main loop: Read from WebSocket and write to PTY
        try:
            while True:
                # Receive message from Client (xterm.js)
                # Message can be simple input string, or a JSON command (resize)
                message = await websocket.receive()
                
                if message["type"] == "websocket.disconnect":
                    raise WebSocketDisconnect(code=message.get("code", 1000))
                
                if "text" in message:
                    payload = message["text"]
                    
                    # Check if it's a control message (Hack: usually client sends raw input)
                    # We can enforce a protocol: binary for Input, text JSON for Control.
                    try:
                        # Try parsing as JSON control message
                        cmd = json.loads(payload)
                        if cmd.get("type") == "resize":
                            session.resize(cmd["cols"], cmd["rows"])
                            continue
                    except:
                        pass # Not JSON, treat as raw input
                    
                    session.write(payload.encode())
                    
                elif "bytes" in message:
                    session.write(message["bytes"])
        except RuntimeError:
            # Handle "Cannot call 'receive' once a disconnect message has been received"
            # This happens if Starlette/FastAPI already processed the disconnect internally
            # but we called receive() again.
            logger.info(f"Runtime disconnect for session {session_id}")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        pty_manager.close_session(session_id)
        if reader_task and not reader_task.done():
            reader_task.cancel()
