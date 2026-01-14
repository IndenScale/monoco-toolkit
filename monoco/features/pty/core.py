
import asyncio
import os
import pty
import select
import signal
import struct
import fcntl
import termios
import logging
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger("monoco.pty")

class PTYSession:
    """
    Manages a single PTY session connected to a subprocess (shell).
    """
    def __init__(self, session_id: str, cmd: list[str], env: Optional[Dict[str, str]] = None, cwd: Optional[str] = None):
        self.session_id = session_id
        self.cmd = cmd
        self.env = env or os.environ.copy()
        self.cwd = cwd or os.getcwd()
        
        self.fd: Optional[int] = None
        self.pid: Optional[int] = None
        self.proc = None # subprocess.Popen object
        self.running = False
        self.loop = asyncio.get_running_loop()

    def start(self, cols: int = 80, rows: int = 24):
        """
        Spawn a subprocess connected to a new PTY using subprocess.Popen.
        This provides better safety in threaded/asyncio environments than pty.fork().
        """
        import subprocess

        # 1. Open PTY pair
        master_fd, slave_fd = pty.openpty()
        
        # 2. Set initial size
        self._set_winsize(master_fd, rows, cols)

        try:
            # 3. Spawn process
            # start_new_session=True executes setsid()
            self.proc = subprocess.Popen(
                self.cmd,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=self.cwd,
                env=self.env,
                start_new_session=True,
                close_fds=True # Important to close other FDs in child
            )
            
            self.pid = self.proc.pid
            self.fd = master_fd
            self.running = True
            
            # 4. Close slave fd in parent (child has it open now)
            os.close(slave_fd)
            
            logger.info(f"Started session {self.session_id} (PID: {self.pid})")
            
        except Exception as e:
            logger.error(f"Failed to spawn process: {e}")
            # Ensure we clean up fds if spawn fails
            try:
                os.close(master_fd)
            except: pass
            try:
                os.close(slave_fd)
            except: pass
            raise e


    def resize(self, cols: int, rows: int):
        """
        Resize the PTY.
        """
        if self.fd and self.running:
            self._set_winsize(self.fd, rows, cols)

    def write(self, data: bytes):
        """
        Write input data (from websocket) to the PTY master fd.
        """
        if self.fd and self.running:
            os.write(self.fd, data)

    async def read(self) -> bytes:
        """
        Read output data from PTY master fd (to forward to websocket).
        """
        if not self.fd or not self.running:
            return b""
            
        try:
            # Run in executor to avoid blocking the event loop
            # pty read is blocking
            return await self.loop.run_in_executor(None, self._read_blocking)
        except OSError:
            return b""

    def _read_blocking(self) -> bytes:
        try:
            return os.read(self.fd, 1024)
        except OSError:
            return b""

    def terminate(self):
        """
        Terminate the process and close the PTY.
        """
        self.running = False
        
        # Use Popen object if available
        if self.proc:
            try:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=1.0)
                except:
                    # Force kill if not terminated
                    self.proc.kill()
                    self.proc.wait()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
            self.proc = None
            self.pid = None
        elif self.pid:
            # Fallback for legacy or if Popen obj lost
            try:
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, 0) # Reap zombie
            except OSError:
                pass
            self.pid = None
            
        if self.fd:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
        logger.info(f"Terminated session {self.session_id}")

    def _set_winsize(self, fd: int, row: int, col: int, xpix: int = 0, ypix: int = 0):
        winsize = struct.pack("HHHH", row, col, xpix, ypix)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


class PTYManager:
    """
    Singleton to manage multiple PTY sessions.
    """
    def __init__(self):
        self.sessions: Dict[str, PTYSession] = {}

    def create_session(self, session_id: str, cwd: str, cmd: list[str] = ["/bin/zsh"], env: Dict = None) -> PTYSession:
        if session_id in self.sessions:
            # In a real app, we might want to attach to existing?
            # For now, kill and recreate (or error)
            self.close_session(session_id)
            
        session = PTYSession(session_id, cmd, env, cwd)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[PTYSession]:
        return self.sessions.get(session_id)

    def close_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].terminate()
            del self.sessions[session_id]

    def close_all_sessions(self):
        """
        Terminate all active PTY sessions.
        """
        for session_id in list(self.sessions.keys()):
            self.close_session(session_id)
