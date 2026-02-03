"""
Automation Orchestrator - Coordinates watchers, router, and actions.

Part of the Event Automation Framework.
Provides high-level orchestration of the three-layer architecture.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from monoco.core.scheduler import AgentEventType, EventBus, event_bus
from monoco.core.watcher import (
    FilesystemWatcher,
    IssueWatcher,
    MemoWatcher,
    TaskWatcher,
    DropzoneWatcher,
    WatchConfig,
)
from monoco.core.router import ActionRouter, Action, ActionChain
from monoco.core.executor import (
    SpawnAgentAction,
    RunPytestAction,
    GitCommitAction,
    GitPushAction,
    SendIMAction,
)
from monoco.features.agent.manager import SessionManager
from monoco.core.artifacts.manager import ArtifactManager

from .config import AutomationConfig, TriggerConfig, load_automation_config
from .field_watcher import FieldWatcher, FieldCondition

logger = logging.getLogger(__name__)


class AutomationOrchestrator:
    """
    Orchestrates the three-layer automation framework.
    
    Responsibilities:
    - Initialize watchers based on configuration
    - Set up action routing
    - Manage action execution
    - Coordinate lifecycle
    
    Example:
        >>> orchestrator = AutomationOrchestrator()
        >>> 
        >>> # Load configuration
        >>> config = load_automation_config(".monoco/automation.yaml")
        >>> orchestrator.configure(config)
        >>> 
        >>> # Start automation
        >>> await orchestrator.start()
    """
    
    # Mapping of watcher names to classes
    WATCHER_CLASSES = {
        "IssueWatcher": IssueWatcher,
        "MemoWatcher": MemoWatcher,
        "TaskWatcher": TaskWatcher,
        "DropzoneWatcher": DropzoneWatcher,
    }
    
    # Mapping of action types to classes
    ACTION_CLASSES = {
        "SpawnAgentAction": SpawnAgentAction,
        "RunPytestAction": RunPytestAction,
        "GitCommitAction": GitCommitAction,
        "GitPushAction": GitPushAction,
        "SendIMAction": SendIMAction,
    }
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        session_manager: Optional[SessionManager] = None,
        artifact_manager: Optional[ArtifactManager] = None,
    ):
        self.event_bus = event_bus or event_bus
        self.session_manager = session_manager
        self.artifact_manager = artifact_manager
        
        self._config: Optional[AutomationConfig] = None
        self._watchers: Dict[str, FilesystemWatcher] = {}
        self._router: Optional[ActionRouter] = None
        self._field_watcher = FieldWatcher()
        
        self._running = False
    
    def configure(
        self,
        config: AutomationConfig,
        project_root: Optional[Path] = None,
    ) -> None:
        """
        Configure the orchestrator with automation config.
        
        Args:
            config: Automation configuration
            project_root: Project root path (for resolving relative paths)
        """
        self._config = config
        project_root = project_root or Path.cwd()
        
        # Create router
        self._router = ActionRouter(event_bus=self.event_bus)
        
        # Set up watchers and actions from config
        for trigger in config.get_enabled_triggers():
            self._setup_trigger(trigger, project_root)
        
        logger.info(f"Configured orchestrator with {len(config.triggers)} triggers")
    
    def _setup_trigger(self, trigger: TriggerConfig, project_root: Path) -> None:
        """Set up a trigger (watcher + actions)."""
        # Create watcher if not exists
        if trigger.watcher not in self._watchers:
            watcher = self._create_watcher(trigger.watcher, project_root)
            if watcher:
                self._watchers[trigger.watcher] = watcher
        
        # Create actions
        actions = []
        for action_config in trigger.actions:
            action = self._create_action(action_config.type, action_config.params)
            if action:
                actions.append(action)
        
        # Register with router
        if actions and self._router:
            event_type = trigger.to_agent_event_type()
            if event_type:
                for action in actions:
                    # Build condition function if specified
                    condition = None
                    if trigger.condition:
                        condition = self._parse_condition(trigger.condition, trigger.field)
                    
                    self._router.register(
                        event_type,
                        action,
                        condition=condition,
                        priority=trigger.priority,
                    )
                    
                    logger.debug(f"Registered {action.name} for {event_type.value}")
    
    def _create_watcher(
        self,
        watcher_name: str,
        project_root: Path,
    ) -> Optional[FilesystemWatcher]:
        """Create a watcher by name."""
        watcher_class = self.WATCHER_CLASSES.get(watcher_name)
        if not watcher_class:
            logger.warning(f"Unknown watcher: {watcher_name}")
            return None
        
        # Determine watch path based on watcher type
        if watcher_name == "IssueWatcher":
            watch_path = project_root / "Issues"
            config = WatchConfig(
                path=watch_path,
                patterns=["*.md"],
                recursive=True,
            )
            return IssueWatcher(config, self.event_bus)
        
        elif watcher_name == "MemoWatcher":
            watch_path = project_root / "Memos" / "inbox.md"
            config = WatchConfig(
                path=watch_path,
                patterns=["*.md"],
            )
            return MemoWatcher(config, self.event_bus)
        
        elif watcher_name == "TaskWatcher":
            watch_path = project_root / "tasks.md"
            config = WatchConfig(
                path=watch_path,
                patterns=["*.md"],
            )
            return TaskWatcher(config, self.event_bus)
        
        elif watcher_name == "DropzoneWatcher":
            watch_path = project_root / ".monoco" / "dropzone"
            if not self.artifact_manager:
                logger.warning("DropzoneWatcher requires ArtifactManager")
                return None
            config = WatchConfig(path=watch_path)
            return DropzoneWatcher(config, self.artifact_manager, self.event_bus)
        
        return None
    
    def _create_action(
        self,
        action_type: str,
        params: Dict[str, Any],
    ) -> Optional[Action]:
        """Create an action by type."""
        action_class = self.ACTION_CLASSES.get(action_type)
        if not action_class:
            logger.warning(f"Unknown action type: {action_type}")
            return None
        
        try:
            # Handle special cases that require dependencies
            if action_type == "SpawnAgentAction":
                if not self.session_manager:
                    logger.warning("SpawnAgentAction requires SessionManager")
                    return None
                role = params.get("role", "Engineer")
                return SpawnAgentAction(
                    role=role,
                    session_manager=self.session_manager,
                    config=params,
                )
            
            # Generic action creation
            return action_class(**params)
        
        except Exception as e:
            logger.error(f"Failed to create action {action_type}: {e}")
            return None
    
    def _parse_condition(
        self,
        condition_str: str,
        field: Optional[str],
    ):
        """Parse a condition string into a function."""
        # Simple condition parser
        # Supports: "value == 'doing'", "pending_count >= 5", etc.
        
        def condition(event):
            payload = event.payload
            
            # If field is specified, check that field
            if field:
                value = payload.get(field)
                # Parse simple comparisons
                if "==" in condition_str:
                    expected = condition_str.split("==")[1].strip().strip("'\"")
                    return str(value) == expected
                elif "!=" in condition_str:
                    expected = condition_str.split("!=")[1].strip().strip("'\"")
                    return str(value) != expected
            
            # Check for pending_count style conditions
            if ">=" in condition_str:
                parts = condition_str.split(">=")
                key = parts[0].strip()
                threshold = int(parts[1].strip())
                return payload.get(key, 0) >= threshold
            
            return True
        
        return condition
    
    async def start(self) -> None:
        """Start all watchers and the router."""
        if self._running:
            return
        
        self._running = True
        
        # Start event bus
        await self.event_bus.start()
        
        # Start router
        if self._router:
            await self._router.start()
        
        # Start watchers
        for name, watcher in self._watchers.items():
            try:
                await watcher.start()
                logger.info(f"Started watcher: {name}")
            except Exception as e:
                logger.error(f"Failed to start watcher {name}: {e}")
        
        logger.info("Automation orchestrator started")
    
    async def stop(self) -> None:
        """Stop all watchers and the router."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop watchers
        for name, watcher in self._watchers.items():
            try:
                await watcher.stop()
                logger.info(f"Stopped watcher: {name}")
            except Exception as e:
                logger.error(f"Error stopping watcher {name}: {e}")
        
        # Stop router
        if self._router:
            await self._router.stop()
        
        # Stop event bus
        await self.event_bus.stop()
        
        logger.info("Automation orchestrator stopped")
    
    def add_watcher(self, name: str, watcher: FilesystemWatcher) -> None:
        """Add a custom watcher."""
        self._watchers[name] = watcher
    
    def add_action_class(self, name: str, action_class: Type[Action]) -> None:
        """Register a custom action class."""
        self.ACTION_CLASSES[name] = action_class
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "running": self._running,
            "watchers": len(self._watchers),
            "watcher_names": list(self._watchers.keys()),
            "router": self._router.get_stats() if self._router else None,
            "config_triggers": len(self._config.triggers) if self._config else 0,
        }
