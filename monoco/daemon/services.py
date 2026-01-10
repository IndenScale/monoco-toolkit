import asyncio
import logging
import subprocess
import os
import re
from typing import List, Optional, Dict
from asyncio import Queue
from pathlib import Path

from monoco.features.issue.core import parse_issue, IssueMetadata

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
            "data": payload
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

class IssueMonitor:
    """
    Monitor the Issues directory for changes and broadcast update events.
    """
    def __init__(self, issues_root: Path, broadcaster: Broadcaster, poll_interval: float = 2.0):
        self.issues_root = issues_root
        self.broadcaster = broadcaster
        self.poll_interval = poll_interval
        self.is_running = False
        self.file_state: Dict[Path, float] = {}

    async def scan(self):
        """
        Scan for changes in the Issues directory.
        """
        current_state: Dict[Path, float] = {}
        
        # Traverse recursively
        for root, dirs, files in os.walk(self.issues_root):
            for file in files:
                if file.endswith(".md"):
                    path = Path(root) / file
                    try:
                        mtime = path.stat().st_mtime
                        current_state[path] = mtime
                    except FileNotFoundError:
                        continue 

        # Detect changes
        added = set(current_state.keys()) - set(self.file_state.keys())
        removed = set(self.file_state.keys()) - set(current_state.keys())
        modified = {
            p for p, m in current_state.items() 
            if p in self.file_state and m != self.file_state[p]
        }

        # Handle events
        for path in added | modified:
            issue: Optional[IssueMetadata] = parse_issue(path)
            if issue:
                payload = issue.model_dump(mode='json')
                await self.broadcaster.broadcast("issue_upserted", payload)
        
        for path in removed:
            filename = path.name
            # Infer ID from filename (e.g., FEAT-0001-title.md)
            match = re.match(r"([A-Z]+-\d{4})", filename)
            if match:
                issue_id = match.group(1)
                await self.broadcaster.broadcast("issue_deleted", {"id": issue_id})
                
        self.file_state = current_state

    async def start(self):
        self.is_running = True
        logger.info(f"Issue Monitor started. Watching {self.issues_root}")
        
        # Initial scan to populate state
        current_state = {}
        for root, dirs, files in os.walk(self.issues_root):
            for file in files:
                if file.endswith(".md"):
                    path = Path(root) / file
                    try:
                        current_state[path] = path.stat().st_mtime
                    except FileNotFoundError:
                        pass
        self.file_state = current_state

        while self.is_running:
            await asyncio.sleep(self.poll_interval)
            await self.scan()

    def stop(self):
        self.is_running = False
        logger.info("Issue Monitor stopping...")
