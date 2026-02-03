"""
LocalProcessScheduler - Local process-based agent scheduler.

Implements the AgentScheduler ABC using local subprocess execution.
Integrates with SessionManager and Worker for process lifecycle management.
"""

import asyncio
import logging
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Optional, Any

from .base import AgentScheduler, AgentTask, AgentStatus
from .engines import EngineFactory
from .events import AgentEventType, event_bus

logger = logging.getLogger("monoco.core.scheduler.local")


class LocalProcessScheduler(AgentScheduler):
    """
    Local process-based scheduler for agent execution.
    
    This scheduler manages agent tasks as local subprocesses, providing:
    - Process lifecycle management (spawn, monitor, terminate)
    - Concurrency quota control via semaphore
    - Timeout handling
    - Session tracking and status reporting
    
    Attributes:
        max_concurrent: Maximum number of concurrent agent processes
        project_root: Root path of the Monoco project
    
    Example:
        >>> scheduler = LocalProcessScheduler(max_concurrent=5)
        >>> session_id = await scheduler.schedule(task)
        >>> status = scheduler.get_status(session_id)
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        project_root: Optional[Path] = None,
    ):
        self.max_concurrent = max_concurrent
        self.project_root = project_root or Path.cwd()
        
        # Session tracking: session_id -> process info
        self._sessions: Dict[str, Dict[str, Any]] = {}
        
        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Background monitoring task
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the scheduler and monitoring loop."""
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"LocalProcessScheduler started (max_concurrent={self.max_concurrent})")
    
    async def stop(self):
        """Stop the scheduler and terminate all sessions."""
        if not self._running:
            return
        self._running = False
        
        # Cancel monitor loop
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Terminate all active sessions
        for session_id in list(self._sessions.keys()):
            await self.terminate(session_id)
        
        logger.info("LocalProcessScheduler stopped")
    
    async def schedule(self, task: AgentTask) -> str:
        """
        Schedule a task for execution as a local subprocess.
        
        Args:
            task: The task to schedule
            
        Returns:
            session_id: Unique identifier for the scheduled session
            
        Raises:
            RuntimeError: If scheduling fails or engine is not supported
        """
        session_id = str(uuid.uuid4())
        
        # Acquire semaphore slot
        acquired = await self._semaphore.acquire()
        if not acquired:
            # This shouldn't happen with asyncio.Semaphore, but just in case
            raise RuntimeError("Failed to acquire concurrency slot")
        
        try:
            # Get engine adapter
            adapter = EngineFactory.create(task.engine)
            command = adapter.build_command(task.prompt)
            
            logger.info(f"[{session_id}] Starting {task.role_name} with {task.engine} engine")
            
            # Start subprocess
            process = subprocess.Popen(
                command,
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True,
                cwd=self.project_root,
            )
            
            # Track session
            self._sessions[session_id] = {
                "task": task,
                "process": process,
                "status": AgentStatus.RUNNING,
                "started_at": time.time(),
                "role_name": task.role_name,
                "issue_id": task.issue_id,
            }
            
            # Publish session started event
            await event_bus.publish(
                AgentEventType.SESSION_STARTED,
                {
                    "session_id": session_id,
                    "issue_id": task.issue_id,
                    "role_name": task.role_name,
                    "engine": task.engine,
                },
                source="LocalProcessScheduler"
            )
            
            return session_id
            
        except Exception as e:
            # Release semaphore on failure
            self._semaphore.release()
            logger.error(f"[{session_id}] Failed to start task: {e}")
            raise RuntimeError(f"Failed to schedule task: {e}")
    
    async def terminate(self, session_id: str) -> bool:
        """
        Terminate a running or pending session.
        
        Args:
            session_id: The session ID to terminate
            
        Returns:
            True if termination was successful, False otherwise
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"[{session_id}] Session not found for termination")
            return False
        
        process = session.get("process")
        if not process:
            return False
        
        try:
            # Try graceful termination
            process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if still running
                process.kill()
                process.wait()
            
            session["status"] = AgentStatus.TERMINATED
            
            # Publish session terminated event
            await event_bus.publish(
                AgentEventType.SESSION_TERMINATED,
                {
                    "session_id": session_id,
                    "issue_id": session.get("issue_id"),
                    "role_name": session.get("role_name"),
                },
                source="LocalProcessScheduler"
            )
            
            # Release semaphore
            self._semaphore.release()
            
            logger.info(f"[{session_id}] Session terminated")
            return True
            
        except Exception as e:
            logger.error(f"[{session_id}] Error terminating session: {e}")
            return False
    
    def get_status(self, session_id: str) -> Optional[AgentStatus]:
        """
        Get the current status of a session.
        
        Args:
            session_id: The session ID to query
            
        Returns:
            The current AgentStatus, or None if session not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        return session.get("status")
    
    def list_active(self) -> Dict[str, AgentStatus]:
        """
        List all active (pending or running) sessions.
        
        Returns:
            Dictionary mapping session_id to AgentStatus
        """
        return {
            session_id: session["status"]
            for session_id, session in self._sessions.items()
            if session["status"] in (AgentStatus.PENDING, AgentStatus.RUNNING)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary containing scheduler metrics
        """
        active_count = len(self.list_active())
        total_count = len(self._sessions)
        
        return {
            "running": self._running,
            "max_concurrent": self.max_concurrent,
            "active_sessions": active_count,
            "total_sessions": total_count,
            "available_slots": self.max_concurrent - active_count,
        }
    
    async def _monitor_loop(self):
        """Background loop to monitor session statuses."""
        logger.info("Starting session monitor loop")
        
        while self._running:
            try:
                await self._check_sessions()
                await asyncio.sleep(2)  # Check every 2 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(2)
    
    async def _check_sessions(self):
        """Check all sessions and update statuses."""
        for session_id, session in list(self._sessions.items()):
            process = session.get("process")
            if not process:
                continue
            
            current_status = session["status"]
            
            # Skip if already in terminal state
            if current_status in (
                AgentStatus.COMPLETED,
                AgentStatus.FAILED,
                AgentStatus.TERMINATED,
                AgentStatus.TIMEOUT,
            ):
                continue
            
            # Check timeout
            task = session.get("task")
            started_at = session.get("started_at", 0)
            if task and task.timeout and (time.time() - started_at) > task.timeout:
                logger.warning(f"[{session_id}] Task timeout exceeded ({task.timeout}s)")
                await self._handle_timeout(session_id, session)
                continue
            
            # Check process status
            returncode = process.poll()
            if returncode is None:
                # Still running
                continue
            
            # Process finished
            if returncode == 0:
                await self._handle_completion(session_id, session)
            else:
                await self._handle_failure(session_id, session, returncode)
    
    async def _handle_completion(self, session_id: str, session: Dict[str, Any]):
        """Handle successful session completion."""
        session["status"] = AgentStatus.COMPLETED
        
        # Publish completion event
        await event_bus.publish(
            AgentEventType.SESSION_COMPLETED,
            {
                "session_id": session_id,
                "issue_id": session.get("issue_id"),
                "role_name": session.get("role_name"),
            },
            source="LocalProcessScheduler"
        )
        
        # Release semaphore
        self._semaphore.release()
        
        logger.info(f"[{session_id}] Session completed successfully")
    
    async def _handle_failure(self, session_id: str, session: Dict[str, Any], returncode: int):
        """Handle session failure."""
        session["status"] = AgentStatus.FAILED
        
        # Publish failure event
        await event_bus.publish(
            AgentEventType.SESSION_FAILED,
            {
                "session_id": session_id,
                "issue_id": session.get("issue_id"),
                "role_name": session.get("role_name"),
                "reason": f"Process exited with code {returncode}",
            },
            source="LocalProcessScheduler"
        )
        
        # Release semaphore
        self._semaphore.release()
        
        logger.error(f"[{session_id}] Session failed with exit code {returncode}")
    
    async def _handle_timeout(self, session_id: str, session: Dict[str, Any]):
        """Handle session timeout."""
        process = session.get("process")
        
        # Kill the process
        if process:
            try:
                process.kill()
                process.wait()
            except Exception as e:
                logger.error(f"[{session_id}] Error killing timed out process: {e}")
        
        session["status"] = AgentStatus.TIMEOUT
        
        # Publish failure event (timeout is a type of failure)
        await event_bus.publish(
            AgentEventType.SESSION_FAILED,
            {
                "session_id": session_id,
                "issue_id": session.get("issue_id"),
                "role_name": session.get("role_name"),
                "reason": "Timeout exceeded",
            },
            source="LocalProcessScheduler"
        )
        
        # Release semaphore
        self._semaphore.release()
