import asyncio
import logging
import subprocess
import os
import re
from typing import List, Optional, Dict, Any
from asyncio import Queue
from pathlib import Path

from monoco.features.issue.core import parse_issue, IssueMetadata
import json

logger = logging.getLogger("monoco.daemon.services")

class Broadcaster:
    """
    Manages SSE subscriptions and broadcasts events to all connected clients.
    """
    def __init__(self):
        self.subscribers: List[Queue] = []

    async def subscribe(self) -> Queue:
        queue = Queue()
        self.subscribers.append(queue)
        logger.info(f"New client subscribed. Total clients: {len(self.subscribers)}")
        return queue

    async def unsubscribe(self, queue: Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            logger.info(f"Client unsubscribed. Total clients: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, payload: dict):
        if not self.subscribers:
            return
        
        message = {
            "event": event_type,
            "data": json.dumps(payload)
        }
        
        # Dispatch to all queues
        for queue in self.subscribers:
            await queue.put(message)
        
        logger.debug(f"Broadcasted {event_type} to {len(self.subscribers)} clients.")


class GitMonitor:
    """
    Polls the Git repository for HEAD changes and triggers updates.
    """
    def __init__(self, broadcaster: Broadcaster, poll_interval: float = 2.0):
        self.broadcaster = broadcaster
        self.poll_interval = poll_interval
        self.last_head_hash: Optional[str] = None
        self.is_running = False

    async def get_head_hash(self) -> Optional[str]:
        try:
            # Run git rev-parse HEAD asynchronously
            process = await asyncio.create_subprocess_exec(
                "git", "rev-parse", "HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode().strip()
            return None
        except Exception as e:
            logger.error(f"Git polling error: {e}")
            return None

    async def start(self):
        self.is_running = True
        logger.info("Git Monitor started.")
        
        # Initial check
        self.last_head_hash = await self.get_head_hash()
        
        while self.is_running:
            await asyncio.sleep(self.poll_interval)
            current_hash = await self.get_head_hash()
            
            if current_hash and current_hash != self.last_head_hash:
                logger.info(f"Git HEAD changed: {self.last_head_hash} -> {current_hash}")
                self.last_head_hash = current_hash
                await self.broadcaster.broadcast("HEAD_UPDATED", {
                    "ref": "HEAD",
                    "hash": current_hash
                })

    def stop(self):
        self.is_running = False
        logger.info("Git Monitor stopping...")

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from monoco.core.config import MonocoConfig, get_config

class ProjectContext:
    """
    Holds the runtime state for a single project.
    """
    def __init__(self, path: Path, config: MonocoConfig, broadcaster: Broadcaster):
        self.path = path
        self.config = config
        self.id = path.name  # Use directory name as ID for now
        self.name = config.project.name
        self.issues_root = path / config.paths.issues
        self.monitor = IssueMonitor(self.issues_root, broadcaster, project_id=self.id)

    async def start(self):
        await self.monitor.start()

    def stop(self):
        self.monitor.stop()

class ProjectManager:
    """
    Discovers and manages multiple Monoco projects within a workspace.
    """
    def __init__(self, workspace_root: Path, broadcaster: Broadcaster):
        self.workspace_root = workspace_root
        self.broadcaster = broadcaster
        self.projects: Dict[str, ProjectContext] = {}

    def scan(self):
        """
        Scans workspace for potential Monoco projects.
        A directory is a project if it has monoco.yaml or .monoco/config.yaml or an Issues directory.
        """
        logger.info(f"Scanning workspace: {self.workspace_root}")
        from monoco.core.workspace import find_projects
        
        projects = find_projects(self.workspace_root)
        for p in projects:
            self._register_project(p)

    def _register_project(self, path: Path):
        try:
            config = get_config(str(path))
            # If name is default, try to use directory name
            if config.project.name == "Monoco Project":
                config.project.name = path.name
            
            ctx = ProjectContext(path, config, self.broadcaster)
            self.projects[ctx.id] = ctx
            logger.info(f"Registered project: {ctx.id} ({ctx.path})")
        except Exception as e:
            logger.error(f"Failed to register project at {path}: {e}")

    async def start_all(self):
        self.scan()
        for project in self.projects.values():
            await project.start()

    def stop_all(self):
        for project in self.projects.values():
            project.stop()

    def get_project(self, project_id: str) -> Optional[ProjectContext]:
        return self.projects.get(project_id)

    def list_projects(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "path": str(p.path),
                "issues_path": str(p.issues_root)
            }
            for p in self.projects.values()
        ]

class IssueEventHandler(FileSystemEventHandler):
    def __init__(self, loop, broadcaster: Broadcaster, project_id: str):
        self.loop = loop
        self.broadcaster = broadcaster
        self.project_id = project_id

    def _process_upsert(self, path_str: str):
        if not path_str.endswith(".md"):
            return
        asyncio.run_coroutine_threadsafe(self._handle_upsert(path_str), self.loop)
    
    async def _handle_upsert(self, path_str: str):
        try:
            path = Path(path_str)
            if not path.exists():
                return
            issue = parse_issue(path)
            if issue:
                await self.broadcaster.broadcast("issue_upserted", {
                    "issue": issue.model_dump(mode='json'),
                    "project_id": self.project_id
                })
        except Exception as e:
            logger.error(f"Error handling upsert for {path_str}: {e}")

    def _process_delete(self, path_str: str):
        if not path_str.endswith(".md"):
            return
        asyncio.run_coroutine_threadsafe(self._handle_delete(path_str), self.loop)

    async def _handle_delete(self, path_str: str):
        try:
            filename = Path(path_str).name
            match = re.match(r"([A-Z]+-\d{4})", filename)
            if match:
                issue_id = match.group(1)
                await self.broadcaster.broadcast("issue_deleted", {
                    "id": issue_id,
                    "project_id": self.project_id
                })
        except Exception as e:
            logger.error(f"Error handling delete for {path_str}: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self._process_upsert(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._process_upsert(event.src_path)
            
    def on_deleted(self, event):
        if not event.is_directory:
            self._process_delete(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._process_delete(event.src_path)
            self._process_upsert(event.dest_path)

class IssueMonitor:
    """
    Monitor the Issues directory for changes using Watchdog and broadcast update events.
    """
    def __init__(self, issues_root: Path, broadcaster: Broadcaster, project_id: str):
        self.issues_root = issues_root
        self.broadcaster = broadcaster
        self.project_id = project_id
        self.observer = Observer()
        self.loop = None

    async def start(self):
        self.loop = asyncio.get_running_loop()
        event_handler = IssueEventHandler(self.loop, self.broadcaster, self.project_id)
        
        # Ensure directory exists
        if not self.issues_root.exists():
            logger.warning(f"Issues root {self.issues_root} does not exist. creating...")
            self.issues_root.mkdir(parents=True, exist_ok=True)

        self.observer.schedule(event_handler, str(self.issues_root), recursive=True)
        self.observer.start()
        logger.info(f"Issue Monitor started (Watchdog). Watching {self.issues_root}")

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        logger.info("Issue Monitor stopped.")
