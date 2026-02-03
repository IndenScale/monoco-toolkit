"""
SpawnAgentAction - Action for spawning agent sessions.

Part of Layer 3 (Action Executor) in the event automation framework.
Uses AgentScheduler to spawn and manage agent sessions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from monoco.core.scheduler import AgentEvent, AgentEventType, AgentScheduler
from monoco.core.router import Action, ActionResult
from monoco.features.agent.manager import SessionManager
from monoco.features.agent.models import RoleTemplate

logger = logging.getLogger(__name__)


class SpawnAgentAction(Action):
    """
    Action that spawns an agent session.
    
    This action creates and starts a new agent session based on the event.
    It supports different roles (Architect, Engineer, Reviewer, etc.)
    and integrates with the SessionManager for lifecycle management.
    
    Example:
        >>> action = SpawnAgentAction(
        ...     role="Engineer",
        ...     session_manager=session_manager,
        ... )
        >>> result = await action(event)
    """
    
    ROLE_TEMPLATES = {
        "Architect": {
            "description": "System Architect",
            "trigger": "memo.accumulation",
            "goal": "Process memo inbox and create issues.",
            "system_prompt": "You are the Architect. Process the Memo inbox.",
            "engine": "gemini",
        },
        "Engineer": {
            "description": "Software Engineer",
            "trigger": "issue.stage_changed",
            "goal": "Implement feature requirements.",
            "system_prompt": "You are a Software Engineer. Read the issue and implement requirements.",
            "engine": "gemini",
        },
        "Reviewer": {
            "description": "Code Reviewer",
            "trigger": "pr.created",
            "goal": "Review code changes thoroughly.",
            "system_prompt": "You are a Code Reviewer. Review the code changes thoroughly.",
            "engine": "gemini",
        },
        "Coroner": {
            "description": "Session Autopsy",
            "trigger": "session.failed",
            "goal": "Analyze failed session and create incident report.",
            "system_prompt": "You are the Coroner. Analyze the failed session.",
            "engine": "gemini",
        },
    }
    
    def __init__(
        self,
        role: str,
        session_manager: SessionManager,
        config: Optional[Dict[str, Any]] = None,
        custom_role_template: Optional[Dict[str, str]] = None,
    ):
        super().__init__(config)
        self.role = role
        self.session_manager = session_manager
        self.custom_role_template = custom_role_template
        self._spawned_sessions: List[str] = []
    
    @property
    def name(self) -> str:
        return f"SpawnAgentAction({self.role})"
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """
        Check if we should spawn an agent.
        
        Conditions:
        - No existing session with same role for this issue
        - Semaphore allows new session
        """
        issue_id = event.payload.get("issue_id", "unknown")
        
        # Check if agent already running for this issue
        existing = [
            s for s in self.session_manager.list_sessions(issue_id=issue_id)
            if s.model.role_name == self.role and s.model.status in ["running", "pending"]
        ]
        if existing:
            logger.debug(f"{self.role} already running for {issue_id}, skipping")
            return False
        
        return True
    
    async def execute(self, event: AgentEvent) -> ActionResult:
        """Spawn an agent session."""
        issue_id = event.payload.get("issue_id", "unknown")
        issue_title = event.payload.get("issue_title", "Unknown")
        
        logger.info(f"Spawning {self.role} agent for {issue_id}")
        
        try:
            # Get role template
            role = self._create_role_template(issue_title)
            
            # Create session
            session = self.session_manager.create_session(
                issue_id=issue_id,
                role=role,
            )
            
            # Track spawned session
            self._spawned_sessions.append(session.model.id)
            
            # Start session
            session.start()
            
            logger.info(f"{self.role} session {session.model.id} started for {issue_id}")
            
            return ActionResult.success_result(
                output={
                    "session_id": session.model.id,
                    "issue_id": issue_id,
                    "role": self.role,
                },
                metadata={
                    "session_status": session.model.status,
                },
            )
        
        except Exception as e:
            logger.error(f"Failed to spawn {self.role} for {issue_id}: {e}")
            return ActionResult.failure_result(
                error=str(e),
                metadata={
                    "issue_id": issue_id,
                    "role": self.role,
                },
            )
    
    def _create_role_template(self, issue_title: str) -> RoleTemplate:
        """Create a RoleTemplate for this action."""
        if self.custom_role_template:
            template = self.custom_role_template
        else:
            template = self.ROLE_TEMPLATES.get(self.role, self.ROLE_TEMPLATES["Engineer"])
        
        return RoleTemplate(
            name=self.role,
            description=template["description"],
            trigger=template["trigger"],
            goal=template["goal"].replace("feature requirements", f"feature: {issue_title}"),
            system_prompt=template["system_prompt"],
            engine=template["engine"],
        )
    
    def get_spawned_sessions(self) -> List[str]:
        """Get list of session IDs spawned by this action."""
        return self._spawned_sessions.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get action statistics."""
        stats = super().get_stats()
        stats.update({
            "role": self.role,
            "spawned_sessions": len(self._spawned_sessions),
        })
        return stats


class SpawnArchitectAction(SpawnAgentAction):
    """Convenience action for spawning Architect agents."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            role="Architect",
            session_manager=session_manager,
            config=config,
        )
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Only execute for MEMO_THRESHOLD events."""
        if event.type != AgentEventType.MEMO_THRESHOLD:
            return False
        return await super().can_execute(event)


class SpawnEngineerAction(SpawnAgentAction):
    """Convenience action for spawning Engineer agents."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            role="Engineer",
            session_manager=session_manager,
            config=config,
        )
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Only execute for ISSUE_STAGE_CHANGED to 'doing' events."""
        if event.type != AgentEventType.ISSUE_STAGE_CHANGED:
            return False
        
        new_stage = event.payload.get("new_stage")
        issue_status = event.payload.get("issue_status")
        
        if new_stage != "doing" or issue_status != "open":
            return False
        
        return await super().can_execute(event)


class SpawnReviewerAction(SpawnAgentAction):
    """Convenience action for spawning Reviewer agents."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            role="Reviewer",
            session_manager=session_manager,
            config=config,
        )
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Only execute for PR_CREATED events."""
        if event.type != AgentEventType.PR_CREATED:
            return False
        return await super().can_execute(event)
