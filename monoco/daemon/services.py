import logging
from typing import List, Optional, Dict, Any
from asyncio import Queue
from pathlib import Path

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

        message = {"event": event_type, "data": json.dumps(payload)}

        # Dispatch to all queues
        for queue in self.subscribers:
            await queue.put(message)

        logger.debug(f"Broadcasted {event_type} to {len(self.subscribers)} clients.")


# Monitors moved to monoco.core.git and monoco.features.issue.monitor


from monoco.core.workspace import MonocoProject, Workspace


class ProjectContext:
    """
    Holds the runtime state for a single project.
    Now wraps the core MonocoProject primitive.
    """

    def __init__(self, project: MonocoProject, broadcaster: Broadcaster):
        self.project = project
        self.id = project.id
        self.name = project.name
        self.path = project.path
        self.issues_root = project.issues_root
        self.monitor = IssueMonitor(self.issues_root, broadcaster, project_id=self.id)

    async def start(self):
        await self.monitor.start()

    def stop(self):
        self.monitor.stop()


class ProjectManager:
    """
    Discovers and manages multiple Monoco projects within a workspace.
    Uses core Workspace primitive for discovery.
    """

    def __init__(self, workspace_root: Path, broadcaster: Broadcaster):
        self.workspace_root = workspace_root
        self.broadcaster = broadcaster
        self.projects: Dict[str, ProjectContext] = {}

    def scan(self):
        """
        Scans workspace for Monoco projects using core logic.
        """
        logger.info(f"Scanning workspace: {self.workspace_root}")
        workspace = Workspace.discover(self.workspace_root)

        for project in workspace.projects:
            if project.id not in self.projects:
                ctx = ProjectContext(project, self.broadcaster)
                self.projects[ctx.id] = ctx
                logger.info(f"Registered project: {ctx.id} ({ctx.path})")

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
                "issues_path": str(p.issues_root),
            }
            for p in self.projects.values()
        ]


from monoco.features.issue.monitor import IssueMonitor


class ProjectContext:
    """
    Holds the runtime state for a single project.
    Now wraps the core MonocoProject primitive.
    """

    def __init__(self, project: MonocoProject, broadcaster: Broadcaster):
        self.project = project
        self.id = project.id
        self.name = project.name
        self.path = project.path
        self.issues_root = project.issues_root

        async def on_upsert(issue_data: dict):
            await broadcaster.broadcast(
                "issue_upserted", {"issue": issue_data, "project_id": self.id}
            )

        async def on_delete(issue_data: dict):
            # We skip broadcast here if it's part of a move?
            # Actually, standard upsert/delete is fine, but we need a specialized event for MOVE
            # to help VS Code redirect without closing/reopening.
            await broadcaster.broadcast(
                "issue_deleted", {"id": issue_data["id"], "project_id": self.id}
            )

        self.monitor = IssueMonitor(self.issues_root, on_upsert, on_delete)

    async def notify_move(self, old_path: str, new_path: str, issue_data: dict):
        """Explicitly notify frontend about a logical move (Physical path changed)."""
        await self.broadcaster.broadcast(
            "issue_moved",
            {
                "old_path": old_path,
                "new_path": new_path,
                "issue": issue_data,
                "project_id": self.id,
            },
        )

    async def start(self):
        await self.monitor.start()

    def stop(self):
        self.monitor.stop()
