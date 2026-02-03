"""
Agent Event Handlers - Event-driven agent scheduling (FEAT-0155).

Replaces hardcoded trigger logic in SchedulerService with event handlers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

from monoco.core.scheduler import AgentEvent, AgentEventType, event_bus
from monoco.features.agent.manager import SessionManager
from monoco.features.agent.models import RoleTemplate
from monoco.features.agent.apoptosis import ApoptosisManager
from monoco.features.memo.core import load_memos
from monoco.features.issue.core import list_issues, parse_issue
from monoco.daemon.services import SemaphoreManager

logger = logging.getLogger("monoco.daemon.handlers")


class AgentEventHandler(ABC):
    """Base class for agent event handlers."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        semaphore_manager: SemaphoreManager,
        apoptosis_manager: Optional[ApoptosisManager] = None,
    ):
        self.session_manager = session_manager
        self.semaphore_manager = semaphore_manager
        self.apoptosis_manager = apoptosis_manager
    
    @abstractmethod
    async def should_handle(self, event: AgentEvent) -> bool:
        """Check if this handler should process the event."""
        pass
    
    @abstractmethod
    async def handle(self, event: AgentEvent):
        """Process the event."""
        pass
    
    async def __call__(self, event: AgentEvent):
        """Make handler callable - checks conditions then handles."""
        try:
            if await self.should_handle(event):
                await self.handle(event)
        except Exception as e:
            logger.error(f"Handler error: {e}", exc_info=True)


class ArchitectHandler(AgentEventHandler):
    """
    Handles Memo accumulation events to spawn Architect agent.
    
    Trigger: MEMO_THRESHOLD event
    Condition: No existing Architect session running
    """
    
    MEMO_THRESHOLD = 5  # Default threshold
    
    async def should_handle(self, event: AgentEvent) -> bool:
        """Check if we should spawn an Architect."""
        if event.type != AgentEventType.MEMO_THRESHOLD:
            return False
        
        # Check if Architect already running
        existing = [
            s for s in self.session_manager.list_sessions()
            if s.model.role_name == "Architect" and s.model.status in ["running", "pending"]
        ]
        if existing:
            logger.debug("Architect already running, skipping")
            return False
        
        # Check semaphore
        if not self.semaphore_manager.can_acquire("Architect"):
            logger.warning("Cannot spawn Architect: concurrency limit reached")
            return False
        
        return True
    
    async def handle(self, event: AgentEvent):
        """Spawn Architect agent."""
        logger.info("Event trigger: Spawning Architect for memo processing")
        
        role = RoleTemplate(
            name="Architect",
            description="System Architect",
            trigger="memo.accumulation",
            goal="Process memo inbox and create issues.",
            system_prompt="You are the Architect. Process the Memo inbox.",
            engine="gemini"
        )
        
        session = self.session_manager.create_session(
            issue_id="architecture-review",
            role=role
        )
        
        # Acquire semaphore slot
        self.semaphore_manager.acquire(session.model.id, "Architect")
        
        try:
            session.start()
            logger.info(f"Architect session {session.model.id} started")
        except Exception as e:
            self.semaphore_manager.release(session.model.id)
            logger.error(f"Failed to start Architect session: {e}")
            raise


class EngineerHandler(AgentEventHandler):
    """
    Handles Issue stage change events to spawn Engineer agent.
    
    Trigger: ISSUE_STAGE_CHANGED event (to "doing")
    Condition: Issue status is "open", no existing Engineer session for this issue
    """
    
    async def should_handle(self, event: AgentEvent) -> bool:
        """Check if we should spawn an Engineer."""
        if event.type != AgentEventType.ISSUE_STAGE_CHANGED:
            return False
        
        payload = event.payload
        issue_id = payload.get("issue_id")
        new_stage = payload.get("new_stage")
        issue_status = payload.get("issue_status")
        
        # Only trigger when stage changes to "doing" and status is "open"
        if new_stage != "doing" or issue_status != "open":
            return False
        
        # Check if Engineer already running for this issue
        existing = [
            s for s in self.session_manager.list_sessions(issue_id=issue_id)
            if s.model.role_name == "Engineer" and s.model.status in ["running", "pending"]
        ]
        if existing:
            logger.debug(f"Engineer already running for {issue_id}, skipping")
            return False
        
        # Check semaphore (with cooldown)
        if not self.semaphore_manager.can_acquire("Engineer", issue_id=issue_id):
            logger.warning(f"Cannot spawn Engineer for {issue_id}: concurrency limit or cooldown")
            return False
        
        return True
    
    async def handle(self, event: AgentEvent):
        """Spawn Engineer agent."""
        payload = event.payload
        issue_id = payload.get("issue_id")
        issue_title = payload.get("issue_title", "Unknown")
        
        logger.info(f"Event trigger: Spawning Engineer for {issue_id}")
        
        role = RoleTemplate(
            name="Engineer",
            description="Software Engineer",
            trigger="issue.stage_changed",
            goal=f"Implement feature: {issue_title}",
            system_prompt="You are a Software Engineer. Read the issue and implement requirements.",
            engine="gemini"
        )
        
        session = self.session_manager.create_session(
            issue_id=issue_id,
            role=role
        )
        
        # Acquire semaphore slot
        self.semaphore_manager.acquire(session.model.id, "Engineer")
        
        try:
            session.start()
            logger.info(f"Engineer session {session.model.id} started for {issue_id}")
        except Exception as e:
            self.semaphore_manager.release(session.model.id)
            self.semaphore_manager.record_failure(issue_id, session.model.id)
            logger.error(f"Failed to start Engineer session for {issue_id}: {e}")
            raise


class CoronerHandler(AgentEventHandler):
    """
    Handles session failure events to perform autopsy.
    
    Trigger: SESSION_FAILED or SESSION_CRASHED events
    Condition: ApoptosisManager available
    """
    
    async def should_handle(self, event: AgentEvent) -> bool:
        """Check if we should perform autopsy."""
        if event.type not in [AgentEventType.SESSION_FAILED, AgentEventType.SESSION_CRASHED]:
            return False
        
        if not self.apoptosis_manager:
            logger.warning("No ApoptosisManager available, cannot perform autopsy")
            return False
        
        return True
    
    async def handle(self, event: AgentEvent):
        """Trigger apoptosis/autopsy for failed session."""
        payload = event.payload
        session_id = payload.get("session_id")
        issue_id = payload.get("issue_id")
        failure_reason = payload.get("reason", "Unknown")
        
        logger.info(f"Event trigger: Performing autopsy for failed session {session_id}")
        
        # Record failure for cooldown
        if issue_id:
            self.semaphore_manager.record_failure(issue_id, session_id)
        
        # Trigger apoptosis (which spawns Coroner agent)
        self.apoptosis_manager.trigger_apoptosis(
            session_id,
            failure_reason=f"Session {event.type.value}: {failure_reason}"
        )


class ReviewerHandler(AgentEventHandler):
    """
    Handles PR creation events to spawn Reviewer agent.
    
    Note: Reviewer is NOT auto-triggered by Engineer completion (FEAT-0155).
    It must be triggered by:
    - PR_CREATED event (from GitHub/GitLab webhook)
    - Manual command (monoco agent start --role reviewer)
    
    Trigger: PR_CREATED event
    Condition: No existing Reviewer session for this issue
    """
    
    async def should_handle(self, event: AgentEvent) -> bool:
        """Check if we should spawn a Reviewer."""
        if event.type != AgentEventType.PR_CREATED:
            return False
        
        payload = event.payload
        issue_id = payload.get("issue_id")
        
        # Check if Reviewer already running for this issue
        existing = [
            s for s in self.session_manager.list_sessions(issue_id=issue_id)
            if s.model.role_name == "Reviewer" and s.model.status in ["running", "pending"]
        ]
        if existing:
            logger.debug(f"Reviewer already running for {issue_id}, skipping")
            return False
        
        # Check semaphore
        if not self.semaphore_manager.can_acquire("Reviewer", issue_id=issue_id):
            logger.warning(f"Cannot spawn Reviewer for {issue_id}: concurrency limit reached")
            return False
        
        return True
    
    async def handle(self, event: AgentEvent):
        """Spawn Reviewer agent."""
        payload = event.payload
        issue_id = payload.get("issue_id")
        pr_url = payload.get("pr_url", "")
        
        logger.info(f"Event trigger: Spawning Reviewer for PR {pr_url}")
        
        role = RoleTemplate(
            name="Reviewer",
            description="Code Reviewer",
            trigger="pr.created",
            goal=f"Review code changes for {issue_id}",
            system_prompt="You are a Code Reviewer. Review the code changes thoroughly.",
            engine="gemini"
        )
        
        session = self.session_manager.create_session(
            issue_id=issue_id,
            role=role
        )
        
        # Acquire semaphore slot
        self.semaphore_manager.acquire(session.model.id, "Reviewer")
        
        try:
            session.start()
            logger.info(f"Reviewer session {session.model.id} started for {issue_id}")
        except Exception as e:
            self.semaphore_manager.release(session.model.id)
            logger.error(f"Failed to start Reviewer session for {issue_id}: {e}")
            raise


class EventHandlerRegistry:
    """
    Registry for managing event handler subscriptions.
    
    Provides convenient registration and lifecycle management.
    """
    
    def __init__(self):
        self._handlers: Dict[str, Any] = {}
    
    def register_architect(
        self,
        session_manager: SessionManager,
        semaphore_manager: SemaphoreManager,
    ) -> ArchitectHandler:
        """Register Architect handler for MEMO_THRESHOLD events."""
        handler = ArchitectHandler(session_manager, semaphore_manager)
        event_bus.subscribe(AgentEventType.MEMO_THRESHOLD, handler)
        self._handlers["architect"] = handler
        logger.info("Registered Architect handler")
        return handler
    
    def register_engineer(
        self,
        session_manager: SessionManager,
        semaphore_manager: SemaphoreManager,
    ) -> EngineerHandler:
        """Register Engineer handler for ISSUE_STAGE_CHANGED events."""
        handler = EngineerHandler(session_manager, semaphore_manager)
        event_bus.subscribe(AgentEventType.ISSUE_STAGE_CHANGED, handler)
        self._handlers["engineer"] = handler
        logger.info("Registered Engineer handler")
        return handler
    
    def register_coroner(
        self,
        session_manager: SessionManager,
        semaphore_manager: SemaphoreManager,
        apoptosis_manager: ApoptosisManager,
    ) -> CoronerHandler:
        """Register Coroner handler for SESSION_FAILED/CRASHED events."""
        handler = CoronerHandler(session_manager, semaphore_manager, apoptosis_manager)
        event_bus.subscribe(AgentEventType.SESSION_FAILED, handler)
        event_bus.subscribe(AgentEventType.SESSION_CRASHED, handler)
        self._handlers["coroner"] = handler
        logger.info("Registered Coroner handler")
        return handler
    
    def register_reviewer(
        self,
        session_manager: SessionManager,
        semaphore_manager: SemaphoreManager,
    ) -> ReviewerHandler:
        """Register Reviewer handler for PR_CREATED events."""
        handler = ReviewerHandler(session_manager, semaphore_manager)
        event_bus.subscribe(AgentEventType.PR_CREATED, handler)
        self._handlers["reviewer"] = handler
        logger.info("Registered Reviewer handler")
        return handler
    
    def unregister_all(self):
        """Unregister all handlers from event bus."""
        for name, handler in self._handlers.items():
            # Unsubscribe from all event types
            for event_type in AgentEventType:
                event_bus.unsubscribe(event_type, handler)
            logger.info(f"Unregistered {name} handler")
        self._handlers.clear()
    
    def get_handler(self, name: str) -> Optional[AgentEventHandler]:
        """Get a registered handler by name."""
        return self._handlers.get(name)
