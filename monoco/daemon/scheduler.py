"""
Scheduler Service - Unified event-driven architecture (FEAT-0164).

This module implements a unified event-driven scheduler service that:
1. Uses AgentScheduler for agent lifecycle management (FEAT-0160)
2. Integrates Watcher framework for file system events (FEAT-0161)
3. Uses ActionRouter for event routing (FEAT-0161)
4. Uses new Handler framework from core.automation (FEAT-0162)

Replaces the old architecture based on SessionManager + SemaphoreManager + polling loops.
"""

import asyncio
import logging
import os
from typing import Dict, Optional, List, Any
from pathlib import Path

from monoco.daemon.services import ProjectManager
from monoco.core.scheduler import (
    AgentEventType,
    event_bus,
    AgentScheduler,
    LocalProcessScheduler,
)
from monoco.core.router import ActionRouter
from monoco.core.watcher import WatchConfig, IssueWatcher, MemoWatcher, TaskWatcher
from monoco.core.automation.handlers import start_all_handlers, stop_all_handlers
from monoco.core.config import get_config

logger = logging.getLogger("monoco.daemon.scheduler")


class SchedulerService:
    """
    Unified event-driven scheduler service.
    
    Responsibilities:
    - Initialize and manage AgentScheduler
    - Setup and manage Watchers for file system events
    - Configure ActionRouter for event routing
    - Start/stop all handlers
    
    Architecture:
    ```
    SchedulerService
    ├── AgentScheduler (LocalProcessScheduler)
    │   └── Manages agent process lifecycle
    ├── Watchers
    │   ├── IssueWatcher -> EventBus
    │   ├── MemoWatcher -> EventBus
    │   └── TaskWatcher -> EventBus
    ├── ActionRouter
    │   └── Routes events to Actions
    └── Handlers (from core.automation)
        ├── TaskFileHandler
        ├── IssueStageHandler
        ├── MemoThresholdHandler
        └── PRCreatedHandler
    ```
    """
    
    def __init__(self, project_manager: ProjectManager):
        self.project_manager = project_manager
        
        # AgentScheduler (FEAT-0160)
        scheduler_config = self._load_scheduler_config()
        self.agent_scheduler: AgentScheduler = LocalProcessScheduler(
            max_concurrent=scheduler_config.get("max_concurrent", 5),
            project_root=Path.cwd(),
        )
        
        # ActionRouter (FEAT-0161)
        self.action_router = ActionRouter(event_bus)
        
        # Watchers (FEAT-0161)
        self.watchers: List[Any] = []
        
        # Handlers (FEAT-0162)
        self.handlers: List[Any] = []
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False
    
    def _load_scheduler_config(self) -> Dict[str, Any]:
        """Load scheduler configuration from config files and env vars."""
        config = {"max_concurrent": 5}
        
        try:
            settings = get_config()
            
            # Check for concurrency config
            if hasattr(settings, "agent") and hasattr(settings.agent, "concurrency"):
                concurrency_config = settings.agent.concurrency
                if hasattr(concurrency_config, "global_max"):
                    config["max_concurrent"] = concurrency_config.global_max
            
            # Check for environment variable override
            env_max_agents = os.environ.get("MONOCO_MAX_AGENTS")
            if env_max_agents:
                try:
                    config["max_concurrent"] = int(env_max_agents)
                    logger.info(f"Overriding max_concurrent from environment: {env_max_agents}")
                except ValueError:
                    logger.warning(f"Invalid MONOCO_MAX_AGENTS value: {env_max_agents}")
            
            return config
        except Exception as e:
            logger.warning(f"Failed to load scheduler config: {e}. Using defaults.")
            return config
    
    async def start(self):
        """Start the scheduler service."""
        logger.info("Starting Scheduler Service (unified event-driven architecture)...")
        self._running = True
        
        # 1. Start EventBus
        await event_bus.start()
        
        # 2. Start AgentScheduler
        await self.agent_scheduler.start()
        
        # 3. Setup and start Watchers
        self._setup_watchers()
        for watcher in self.watchers:
            await watcher.start()
        
        # 4. Start Handlers (FEAT-0162)
        self.handlers = start_all_handlers(self.agent_scheduler)
        
        # 5. Start ActionRouter
        await self.action_router.start()
        
        logger.info("Scheduler Service started with unified event-driven architecture")
    
    def stop(self):
        """Stop the scheduler service."""
        logger.info("Stopping Scheduler Service...")
        self._running = False
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Stop ActionRouter
        asyncio.create_task(self.action_router.stop())
        
        # Stop Handlers
        stop_all_handlers(self.handlers)
        self.handlers = []
        
        # Stop Watchers
        for watcher in self.watchers:
            asyncio.create_task(watcher.stop())
        self.watchers = []
        
        # Stop AgentScheduler
        asyncio.create_task(self.agent_scheduler.stop())
        
        # Stop EventBus
        asyncio.create_task(event_bus.stop())
        
        logger.info("Scheduler Service stopped")
    
    def _setup_watchers(self):
        """Initialize all filesystem watchers."""
        for project_ctx in self.project_manager.projects.values():
            # IssueWatcher
            config = WatchConfig(
                path=project_ctx.issues_root,
                patterns=["*.md"],
                recursive=True,
            )
            self.watchers.append(IssueWatcher(config, event_bus))
            
            # MemoWatcher
            memo_path = project_ctx.path / "Memos" / "inbox.md"
            if memo_path.exists():
                memo_config = WatchConfig(
                    path=memo_path,
                    patterns=["*.md"],
                )
                self.watchers.append(MemoWatcher(memo_config, event_bus))
            
            # TaskWatcher (if tasks.md exists)
            task_path = project_ctx.path / "tasks.md"
            if task_path.exists():
                task_config = WatchConfig(
                    path=task_path,
                    patterns=["*.md"],
                )
                self.watchers.append(TaskWatcher(task_config, event_bus))
        
        logger.info(f"Setup {len(self.watchers)} watchers")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler service statistics."""
        return {
            "running": self._running,
            "event_bus": event_bus.get_stats(),
            "agent_scheduler": self.agent_scheduler.get_stats(),
            "watchers": len(self.watchers),
            "handlers": len(self.handlers),
            "action_router": self.action_router.get_stats(),
            "projects": len(self.project_manager.projects),
        }
