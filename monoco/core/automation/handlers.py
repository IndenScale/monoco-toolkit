"""
Event Handlers - Stateless, Independent Microservices (FEAT-0162).

This module implements independent event handlers for Agent collaboration.
Each handler is a self-contained, stateless microservice that:
- Listens to specific event types
- Applies its own filtering logic
- Triggers appropriate agent actions

Architecture: No Workflow class or orchestration. Workflow emerges from
the natural interaction of independent handlers.

Handlers:
- TaskFileHandler: Monitors tasks.md changes -> triggers Architect
- IssueStageHandler: Monitors Issue stage=doing -> triggers Engineer
- MemoThresholdHandler: Monitors Memo accumulation -> triggers Architect
- PRCreatedHandler: Monitors PR creation -> triggers Reviewer
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Set

from monoco.core.scheduler import (
    AgentEvent,
    AgentEventType,
    AgentScheduler,
    AgentTask,
    event_bus,
)
from monoco.core.router import ActionResult

logger = logging.getLogger(__name__)


# =============================================================================
# TaskFileHandler - Independent Microservice
# =============================================================================

class TaskFileHandler:
    """
    Independent handler for task file changes.
    
    Trigger: ISSUE_UPDATED event (from TaskWatcher)
    Condition: New tasks added to tasks.md
    Action: Spawn Architect agent to analyze and create Issue (stage=draft)
    
    Emergent Workflow: tasks.md → Architect → Issue (draft)
    
    This handler is stateless and self-contained. It directly subscribes
to the EventBus and manages its own lifecycle.
    
    Example:
        >>> handler = TaskFileHandler(scheduler)
        >>> handler.start()  # Subscribe to events
        >>> # ... handler runs independently ...
        >>> handler.stop()   # Unsubscribe
    """
    
    def __init__(
        self,
        scheduler: AgentScheduler,
        name: str = "TaskFileHandler",
    ):
        self.scheduler = scheduler
        self.name = name
        self._subscribed = False
        self._processed_tasks: Set[str] = set()
    
    def _should_handle(self, event: AgentEvent) -> bool:
        """
        Check if we should handle this event.
        
        Conditions:
        - Event is from TaskWatcher
        - New tasks were added (not just status changes)
        """
        source = event.payload.get("watcher_name", "")
        if "Task" not in source:
            return False
        
        task_changes = event.payload.get("task_changes", [])
        new_tasks = [c for c in task_changes if c.get("type") == "created"]
        
        if not new_tasks:
            logger.debug("No new tasks in event, skipping")
            return False
        
        return True
    
    async def _handle(self, event: AgentEvent) -> Optional[ActionResult]:
        """
        Handle the event by spawning Architect agent.
        
        The Architect will:
        1. Read the tasks.md file
        2. Analyze task requirements
        3. Create Issue tickets (stage=draft)
        """
        file_path = event.payload.get("path", "unknown")
        task_changes = event.payload.get("task_changes", [])
        new_tasks = [c for c in task_changes if c.get("type") == "created"]
        
        logger.info(f"TaskFileHandler: Spawning Architect for {len(new_tasks)} new tasks")
        
        task = AgentTask(
            task_id=f"architect-task-{event.timestamp.timestamp()}",
            role_name="Architect",
            issue_id="task-analysis",
            prompt=self._build_prompt(file_path, new_tasks),
            engine="gemini",
            timeout=600,
            metadata={
                "trigger": "task_file_changed",
                "file_path": file_path,
                "new_tasks": new_tasks,
            },
        )
        
        try:
            session_id = await self.scheduler.schedule(task)
            logger.info(f"Architect scheduled: session={session_id}")
            
            return ActionResult.success_result(
                output={
                    "session_id": session_id,
                    "role": "Architect",
                    "trigger": "task_file_changed",
                    "tasks_analyzed": len(new_tasks),
                },
                metadata={"file_path": file_path},
            )
        
        except Exception as e:
            logger.error(f"Failed to spawn Architect: {e}")
            return ActionResult.failure_result(
                error=f"Failed to schedule Architect: {e}",
                metadata={"file_path": file_path},
            )
    
    async def __call__(self, event: AgentEvent) -> Optional[ActionResult]:
        """Make handler callable - used as EventBus callback."""
        try:
            if self._should_handle(event):
                return await self._handle(event)
        except Exception as e:
            logger.error(f"Handler error in {self.name}: {e}", exc_info=True)
        return None
    
    def start(self) -> None:
        """Subscribe this handler to the EventBus."""
        if self._subscribed:
            return
        
        event_bus.subscribe(AgentEventType.ISSUE_UPDATED, self)
        self._subscribed = True
        logger.info(f"{self.name} started, subscribed to ISSUE_UPDATED")
    
    def stop(self) -> None:
        """Unsubscribe this handler from the EventBus."""
        if not self._subscribed:
            return
        
        event_bus.unsubscribe(AgentEventType.ISSUE_UPDATED, self)
        self._subscribed = False
        logger.info(f"{self.name} stopped")
    
    def _build_prompt(self, file_path: str, new_tasks: list) -> str:
        """Build the prompt for the Architect agent."""
        tasks_text = "\n".join([
            f"- {t.get('content', 'Unknown task')}"
            for t in new_tasks
        ])
        
        return f"""You are the Architect. New tasks have been added to {file_path}:

{tasks_text}

Your task:
1. Analyze these tasks for clarity and completeness
2. If they represent feature requests or bugs, create appropriate Issue tickets
3. Set the Issue stage to 'draft' for review
4. Use `monoco issue create` command to create issues

Focus on understanding the intent and creating well-structured issues."""


# =============================================================================
# IssueStageHandler - Independent Microservice
# =============================================================================

class IssueStageHandler:
    """
    Independent handler for Issue stage changes.
    
    Trigger: ISSUE_STAGE_CHANGED event
    Condition: Stage changed to 'doing' AND status is 'open'
    Action: Spawn Engineer agent to implement the Issue
    
    Emergent Workflow: Issue (doing) → Engineer → PR
    
    This handler is stateless and self-contained.
    
    Example:
        >>> handler = IssueStageHandler(scheduler)
        >>> handler.start()
        >>> # ... handler runs independently ...
        >>> handler.stop()
    """
    
    def __init__(
        self,
        scheduler: AgentScheduler,
        name: str = "IssueStageHandler",
    ):
        self.scheduler = scheduler
        self.name = name
        self._subscribed = False
        self._processed_issues: Set[str] = set()
    
    def _should_handle(self, event: AgentEvent) -> bool:
        """
        Check if we should handle this stage change.
        
        Conditions:
        - New stage is 'doing'
        - Issue status is 'open'
        - Not already processed
        """
        new_stage = event.payload.get("new_stage")
        issue_status = event.payload.get("issue_status")
        issue_id = event.payload.get("issue_id")
        
        if new_stage != "doing":
            logger.debug(f"Stage is '{new_stage}', not 'doing', skipping")
            return False
        
        if issue_status != "open":
            logger.debug(f"Issue status is '{issue_status}', not 'open', skipping")
            return False
        
        if issue_id in self._processed_issues:
            logger.debug(f"Issue {issue_id} already processed, skipping")
            return False
        
        return True
    
    async def _handle(self, event: AgentEvent) -> Optional[ActionResult]:
        """
        Handle the event by spawning Engineer agent.
        
        The Engineer will:
        1. Read the Issue file
        2. Understand requirements
        3. Implement the feature/fix
        4. Create a PR when done
        """
        issue_id = event.payload.get("issue_id", "unknown")
        issue_title = event.payload.get("issue_title", "Unknown")
        file_path = event.payload.get("path", "")
        
        logger.info(f"IssueStageHandler: Spawning Engineer for {issue_id}")
        
        self._processed_issues.add(issue_id)
        
        task = AgentTask(
            task_id=f"engineer-{issue_id}-{event.timestamp.timestamp()}",
            role_name="Engineer",
            issue_id=issue_id,
            prompt=self._build_prompt(issue_id, issue_title, file_path),
            engine="gemini",
            timeout=1800,
            metadata={
                "trigger": "issue_stage_doing",
                "issue_id": issue_id,
                "issue_title": issue_title,
                "file_path": file_path,
            },
        )
        
        try:
            session_id = await self.scheduler.schedule(task)
            logger.info(f"Engineer scheduled: session={session_id}")
            
            return ActionResult.success_result(
                output={
                    "session_id": session_id,
                    "role": "Engineer",
                    "trigger": "issue_stage_doing",
                    "issue_id": issue_id,
                },
                metadata={"issue_id": issue_id},
            )
        
        except Exception as e:
            logger.error(f"Failed to spawn Engineer for {issue_id}: {e}")
            return ActionResult.failure_result(
                error=f"Failed to schedule Engineer: {e}",
                metadata={"issue_id": issue_id},
            )
    
    async def __call__(self, event: AgentEvent) -> Optional[ActionResult]:
        """Make handler callable - used as EventBus callback."""
        try:
            if self._should_handle(event):
                return await self._handle(event)
        except Exception as e:
            logger.error(f"Handler error in {self.name}: {e}", exc_info=True)
        return None
    
    def start(self) -> None:
        """Subscribe this handler to the EventBus."""
        if self._subscribed:
            return
        
        event_bus.subscribe(AgentEventType.ISSUE_STAGE_CHANGED, self)
        self._subscribed = True
        logger.info(f"{self.name} started, subscribed to ISSUE_STAGE_CHANGED")
    
    def stop(self) -> None:
        """Unsubscribe this handler from the EventBus."""
        if not self._subscribed:
            return
        
        event_bus.unsubscribe(AgentEventType.ISSUE_STAGE_CHANGED, self)
        self._subscribed = False
        logger.info(f"{self.name} stopped")
    
    def _build_prompt(self, issue_id: str, issue_title: str, file_path: str) -> str:
        """Build the prompt for the Engineer agent."""
        return f"""You are a Software Engineer. You have been assigned to implement:

Issue: {issue_id} - {issue_title}
File: {file_path}

Your task:
1. Read and understand the Issue requirements
2. Follow the Git workflow:
   - Use `monoco issue start {issue_id} --branch` to create feature branch
   - Implement the requirements
   - Run tests to ensure quality
   - Use `monoco issue sync-files` to track changes
   - Submit PR when done
3. Follow coding standards and best practices
4. Ensure all tests pass

Start by reading the Issue file to understand the full requirements."""


# =============================================================================
# MemoThresholdHandler - Independent Microservice
# =============================================================================

class MemoThresholdHandler:
    """
    Independent handler for Memo threshold events.
    
    Trigger: MEMO_THRESHOLD event
    Condition: Pending memo count exceeds threshold
    Action: Spawn Architect agent to analyze and create Issues
    
    Emergent Workflow: Memos (threshold) → Architect → Issues
    
    This handler is stateless and self-contained.
    
    Example:
        >>> handler = MemoThresholdHandler(scheduler, threshold=5)
        >>> handler.start()
        >>> # ... handler runs independently ...
        >>> handler.stop()
    """
    
    DEFAULT_THRESHOLD = 5
    
    def __init__(
        self,
        scheduler: AgentScheduler,
        threshold: int = DEFAULT_THRESHOLD,
        name: str = "MemoThresholdHandler",
    ):
        self.scheduler = scheduler
        self.name = name
        self.threshold = threshold
        self._subscribed = False
        self._last_processed_count = 0
    
    def _should_handle(self, event: AgentEvent) -> bool:
        """
        Check if we should handle this memo threshold event.
        
        Conditions:
        - Event is MEMO_THRESHOLD
        - Threshold was just crossed (not already above)
        """
        pending_count = event.payload.get("pending_count", 0)
        
        if pending_count < self.threshold:
            logger.debug(f"Pending count {pending_count} below threshold {self.threshold}")
            return False
        
        if pending_count <= self._last_processed_count:
            logger.debug(f"Already processed {self._last_processed_count} memos, skipping")
            return False
        
        return True
    
    async def _handle(self, event: AgentEvent) -> Optional[ActionResult]:
        """
        Handle the event by spawning Architect agent.
        
        The Architect will:
        1. Read the Memos/inbox.md file
        2. Analyze accumulated ideas
        3. Create appropriate Issue tickets
        4. Clear or organize processed memos
        """
        file_path = event.payload.get("path", "Memos/inbox.md")
        pending_count = event.payload.get("pending_count", 0)
        
        logger.info(f"MemoThresholdHandler: Spawning Architect for {pending_count} memos")
        
        self._last_processed_count = pending_count
        
        task = AgentTask(
            task_id=f"architect-memo-{event.timestamp.timestamp()}",
            role_name="Architect",
            issue_id="memo-analysis",
            prompt=self._build_prompt(file_path, pending_count),
            engine="gemini",
            timeout=900,
            metadata={
                "trigger": "memo_threshold",
                "file_path": file_path,
                "pending_count": pending_count,
                "threshold": self.threshold,
            },
        )
        
        try:
            session_id = await self.scheduler.schedule(task)
            logger.info(f"Architect scheduled: session={session_id}")
            
            return ActionResult.success_result(
                output={
                    "session_id": session_id,
                    "role": "Architect",
                    "trigger": "memo_threshold",
                    "pending_count": pending_count,
                },
                metadata={"file_path": file_path},
            )
        
        except Exception as e:
            logger.error(f"Failed to spawn Architect: {e}")
            return ActionResult.failure_result(
                error=f"Failed to schedule Architect: {e}",
                metadata={"file_path": file_path},
            )
    
    async def __call__(self, event: AgentEvent) -> Optional[ActionResult]:
        """Make handler callable - used as EventBus callback."""
        try:
            if self._should_handle(event):
                return await self._handle(event)
        except Exception as e:
            logger.error(f"Handler error in {self.name}: {e}", exc_info=True)
        return None
    
    def start(self) -> None:
        """Subscribe this handler to the EventBus."""
        if self._subscribed:
            return
        
        event_bus.subscribe(AgentEventType.MEMO_THRESHOLD, self)
        self._subscribed = True
        logger.info(f"{self.name} started, subscribed to MEMO_THRESHOLD")
    
    def stop(self) -> None:
        """Unsubscribe this handler from the EventBus."""
        if not self._subscribed:
            return
        
        event_bus.unsubscribe(AgentEventType.MEMO_THRESHOLD, self)
        self._subscribed = False
        logger.info(f"{self.name} stopped")
    
    def _build_prompt(self, file_path: str, pending_count: int) -> str:
        """Build the prompt for the Architect agent."""
        return f"""You are the Architect. {pending_count} memos have accumulated in {file_path}.

Your task:
1. Read and analyze the accumulated memos
2. Categorize and prioritize the ideas
3. Create Issue tickets for actionable items:
   - Use `monoco issue create` command
   - Set appropriate type (feature, fix, chore)
   - Set stage to 'draft' for review
4. Organize or clear processed memos

Focus on turning raw ideas into structured, actionable work items."""


# =============================================================================
# PRCreatedHandler - Independent Microservice
# =============================================================================

class PRCreatedHandler:
    """
    Independent handler for PR creation events.
    
    Trigger: PR_CREATED event
    Condition: New PR created for an Issue
    Action: Spawn Reviewer agent to review the PR
    
    Emergent Workflow: PR → Reviewer → 审查报告
    
    This handler is stateless and self-contained.
    
    Example:
        >>> handler = PRCreatedHandler(scheduler)
        >>> handler.start()
        >>> # ... handler runs independently ...
        >>> handler.stop()
    """
    
    def __init__(
        self,
        scheduler: AgentScheduler,
        name: str = "PRCreatedHandler",
    ):
        self.scheduler = scheduler
        self.name = name
        self._subscribed = False
        self._processed_prs: Set[str] = set()
    
    def _should_handle(self, event: AgentEvent) -> bool:
        """
        Check if we should handle this PR creation event.
        
        Conditions:
        - Event is PR_CREATED
        - Has valid PR URL or ID
        - Not already processed
        """
        pr_url = event.payload.get("pr_url", "")
        pr_id = event.payload.get("pr_id", "")
        
        pr_identifier = pr_id or pr_url
        if not pr_identifier:
            logger.debug("No PR identifier in event, skipping")
            return False
        
        if pr_identifier in self._processed_prs:
            logger.debug(f"PR {pr_identifier} already processed, skipping")
            return False
        
        return True
    
    async def _handle(self, event: AgentEvent) -> Optional[ActionResult]:
        """
        Handle the event by spawning Reviewer agent.
        
        The Reviewer will:
        1. Fetch the PR details
        2. Review code changes
        3. Generate a review report
        4. Output findings to file/Memos
        """
        pr_url = event.payload.get("pr_url", "")
        pr_id = event.payload.get("pr_id", "")
        issue_id = event.payload.get("issue_id", "")
        branch = event.payload.get("branch", "")
        
        pr_identifier = pr_id or pr_url or f"{issue_id}-pr"
        
        logger.info(f"PRCreatedHandler: Spawning Reviewer for PR {pr_identifier}")
        
        self._processed_prs.add(pr_identifier)
        
        task = AgentTask(
            task_id=f"reviewer-{pr_identifier}-{event.timestamp.timestamp()}",
            role_name="Reviewer",
            issue_id=issue_id or "review",
            prompt=self._build_prompt(pr_url, pr_id, issue_id, branch),
            engine="gemini",
            timeout=900,
            metadata={
                "trigger": "pr_created",
                "pr_url": pr_url,
                "pr_id": pr_id,
                "issue_id": issue_id,
                "branch": branch,
            },
        )
        
        try:
            session_id = await self.scheduler.schedule(task)
            logger.info(f"Reviewer scheduled: session={session_id}")
            
            return ActionResult.success_result(
                output={
                    "session_id": session_id,
                    "role": "Reviewer",
                    "trigger": "pr_created",
                    "pr_identifier": pr_identifier,
                },
                metadata={"pr_identifier": pr_identifier},
            )
        
        except Exception as e:
            logger.error(f"Failed to spawn Reviewer: {e}")
            return ActionResult.failure_result(
                error=f"Failed to schedule Reviewer: {e}",
                metadata={"pr_identifier": pr_identifier},
            )
    
    async def __call__(self, event: AgentEvent) -> Optional[ActionResult]:
        """Make handler callable - used as EventBus callback."""
        try:
            if self._should_handle(event):
                return await self._handle(event)
        except Exception as e:
            logger.error(f"Handler error in {self.name}: {e}", exc_info=True)
        return None
    
    def start(self) -> None:
        """Subscribe this handler to the EventBus."""
        if self._subscribed:
            return
        
        event_bus.subscribe(AgentEventType.PR_CREATED, self)
        self._subscribed = True
        logger.info(f"{self.name} started, subscribed to PR_CREATED")
    
    def stop(self) -> None:
        """Unsubscribe this handler from the EventBus."""
        if not self._subscribed:
            return
        
        event_bus.unsubscribe(AgentEventType.PR_CREATED, self)
        self._subscribed = False
        logger.info(f"{self.name} stopped")
    
    def _build_prompt(
        self,
        pr_url: str,
        pr_id: str,
        issue_id: str,
        branch: str,
    ) -> str:
        """Build the prompt for the Reviewer agent."""
        pr_info = f"""
PR URL: {pr_url or 'N/A'}
PR ID: {pr_id or 'N/A'}
Issue: {issue_id or 'N/A'}
Branch: {branch or 'N/A'}
"""
        
        return f"""You are a Code Reviewer. A new PR has been created:

{pr_info}

Your task:
1. Fetch and review the PR changes
2. Check against the original Issue requirements
3. Review for:
   - Code quality and best practices
   - Test coverage
   - Documentation
   - Security considerations
4. Generate a review report:
   - Use `monoco memo add` to record findings
   - Include specific file/line references
   - Provide actionable feedback

Focus on thorough, constructive review that improves code quality."""


# =============================================================================
# Convenience Functions
# =============================================================================

def start_all_handlers(scheduler: AgentScheduler, memo_threshold: int = 5) -> list:
    """
    Start all event handlers.
    
    This is a convenience function - handlers remain independent
    and do not form a Workflow or orchestration layer.
    
    Args:
        scheduler: The AgentScheduler for spawning agents
        memo_threshold: Threshold for memo handler
        
    Returns:
        List of started handler instances
    """
    handlers = [
        TaskFileHandler(scheduler),
        IssueStageHandler(scheduler),
        MemoThresholdHandler(scheduler, threshold=memo_threshold),
        PRCreatedHandler(scheduler),
    ]
    
    for handler in handlers:
        handler.start()
    
    logger.info(f"Started {len(handlers)} independent handlers")
    return handlers


def stop_all_handlers(handlers: list) -> None:
    """
    Stop all event handlers.
    
    Args:
        handlers: List of handler instances to stop
    """
    for handler in handlers:
        handler.stop()
    
    logger.info(f"Stopped {len(handlers)} handlers")
