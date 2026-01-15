import re
import asyncio
import logging
from pathlib import Path
from typing import Callable, Awaitable, Any, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger("monoco.features.issue.monitor")

class IssueEventHandler(FileSystemEventHandler):
    def __init__(self, loop, on_upsert: Callable[[dict], Awaitable[None]], on_delete: Callable[[dict], Awaitable[None]]):
        self.loop = loop
        self.on_upsert = on_upsert
        self.on_delete = on_delete

    def _process_upsert(self, path_str: str):
        if not path_str.endswith(".md"):
            return
        asyncio.run_coroutine_threadsafe(self._handle_upsert(path_str), self.loop)
    
    async def _handle_upsert(self, path_str: str):
        try:
            from monoco.features.issue.core import parse_issue
            path = Path(path_str)
            if not path.exists():
                return
            issue = parse_issue(path)
            if issue:
                await self.on_upsert(issue.model_dump(mode='json'))
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
                await self.on_delete({"id": issue_id})
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
    Monitor the Issues directory for changes using Watchdog and trigger callbacks.
    """
    def __init__(self, issues_root: Path, on_upsert: Callable[[dict], Awaitable[None]], on_delete: Callable[[dict], Awaitable[None]]):
        self.issues_root = issues_root
        self.on_upsert = on_upsert
        self.on_delete = on_delete
        self.observer = Observer()
        self.loop = None

    async def start(self):
        self.loop = asyncio.get_running_loop()
        event_handler = IssueEventHandler(self.loop, self.on_upsert, self.on_delete)
        
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
        logger.info(f"Issue Monitor stopped for {self.issues_root}")
