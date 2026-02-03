"""
SpawnAgentAction - Action for spawning agent sessions.

Part of Layer 3 (Action Executor) in the event automation framework.
Uses AgentScheduler to spawn and manage agent sessions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from monoco.core.scheduler import AgentEvent, AgentEventType, AgentScheduler, AgentTask
from monoco.core.router import Action, ActionResult
from monoco.features.agent.models import RoleTemplate

logger = logging.getLogger(__name__)


class SpawnAgentAction(Action):
    """
    Action that spawns an agent session.
    
    This action creates and starts a new agent session based on the event.
    It supports different roles (Architect, Engineer, Reviewer, etc.)
    and integrates with the AgentScheduler for lifecycle management.
    
    Example:
        >>> action = SpawnAgentAction(
        ...     role="Engineer",
        ...     scheduler=scheduler,
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
        scheduler: AgentScheduler,
        config: Optional[Dict[str, Any]] = None,
        custom_role_template: Optional[Dict[str, str]] = None,
    ):
        super().__init__(config)
        self.role = role
        self.scheduler = scheduler
        self.custom_role_template = custom_role_template
        self._spawned_sessions: List[str] = []
    
    @property
    def name(self) -> str:
        return f"SpawnAgentAction({self.role})"
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """
        Check if we should spawn an agent.
        
        Conditions:
        - Scheduler has capacity for new tasks
        """
        # Check scheduler capacity
        stats = self.scheduler.get_stats()
        active_tasks = stats.get("active_tasks", 0)
        max_concurrent = stats.get("max_concurrent", 5)
        
        if active_tasks >= max_concurrent:
            logger.warning(f"Scheduler at capacity ({active_tasks}/{max_concurrent}), skipping")
            return False
        
        return True
    
    async def execute(self, event: AgentEvent) -> ActionResult:
        """Spawn an agent session."""
        issue_id = event.payload.get("issue_id", "unknown")
        issue_title = event.payload.get("issue_title", "Unknown")
        
        logger.info(f"Spawning {self.role} agent for {issue_id}")
        
        try:
            # Create AgentTask
            task = AgentTask(
                task_id=f"{self.role.lower()}-{issue_id}-{event.timestamp.timestamp()}",
                role_name=self.role,
                issue_id=issue_id,
                prompt=self._build_prompt(issue_id, issue_title),
                engine=self._get_engine(),
                timeout=self.config.get("timeout", 1800),
                metadata={
                    "trigger": event.type.value,
                    "issue_title": issue_title,
                },
            )
            
            # Schedule task
            session_id = await self.scheduler.schedule(task)
            
            # Track spawned session
            self._spawned_sessions.append(session_id)
            
            logger.info(f"{self.role} scheduled: session={session_id}")
            
            return ActionResult.success_result(
                output={
                    "session_id": session_id,
                    "issue_id": issue_id,
                    "role": self.role,
                },
                metadata={
                    "task_id": task.task_id,
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
    
    def _build_prompt(self, issue_id: str, issue_title: str) -> str:
        """Build the prompt for the agent."""
        template = self.ROLE_TEMPLATES.get(self.role, self.ROLE_TEMPLATES["Engineer"])
        
        return f"""You are a {template['description']}. 

Issue: {issue_id} - {issue_title}

Goal: {template['goal']}

{template['system_prompt']}
"""
    
    def _get_engine(self) -> str:
        """Get the engine for this role."""
        if self.custom_role_template:
            return self.custom_role_template.get("engine", "gemini")
        template = self.ROLE_TEMPLATES.get(self.role, self.ROLE_TEMPLATES["Engineer"])
        return template["engine"]
    
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
        scheduler: AgentScheduler,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            role="Architect",
            scheduler=scheduler,
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
        scheduler: AgentScheduler,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            role="Engineer",
            scheduler=scheduler,
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
        scheduler: AgentScheduler,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            role="Reviewer",
            scheduler=scheduler,
            config=config,
        )
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Only execute for PR_CREATED events."""
        if event.type != AgentEventType.PR_CREATED:
            return False
        return await super().can_execute(event)
