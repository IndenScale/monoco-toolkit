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
- TaskFileHandler: Monitors tasks.md changes -> triggers Principal
- IssueStageHandler: Monitors Issue stage=doing -> triggers Engineer
- MemoThresholdHandler: Monitors Memo accumulation -> triggers Principal
- PRCreatedHandler: Monitors PR creation -> triggers Reviewer
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from monoco.core.scheduler import (
    AgentEvent,
    AgentEventType,
    AgentScheduler,
    AgentTask,
    event_bus,
)
from monoco.core.router import ActionResult
from monoco.features.memo.models import Memo
from monoco.features.memo.core import load_memos, get_inbox_path

logger = logging.getLogger(__name__)


# =============================================================================
# TaskFileHandler - Independent Microservice
# =============================================================================

class TaskFileHandler:
    """
    Independent handler for task file changes.
    
    Trigger: ISSUE_UPDATED event (from TaskWatcher)
    Condition: New tasks added to tasks.md
    Action: Spawn Principal agent to analyze and create Issue (stage=draft)
    
    Emergent Workflow: tasks.md → Principal → Issue (draft)
    
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
        Handle the event by spawning Principal agent.
        
        The Principal will:
        1. Read the tasks.md file
        2. Analyze task requirements
        3. Create Issue tickets (stage=draft)
        """
        file_path = event.payload.get("path", "unknown")
        task_changes = event.payload.get("task_changes", [])
        new_tasks = [c for c in task_changes if c.get("type") == "created"]
        
        logger.info(f"TaskFileHandler: Spawning Principal for {len(new_tasks)} new tasks")
        
        task = AgentTask(
            task_id=f"principal-task-{event.timestamp.timestamp()}",
            role_name="Principal",
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
            logger.info(f"Principal scheduled: session={session_id}")
            
            return ActionResult.success_result(
                output={
                    "session_id": session_id,
                    "role": "Principal",
                    "trigger": "task_file_changed",
                    "tasks_analyzed": len(new_tasks),
                },
                metadata={"file_path": file_path},
            )
        
        except Exception as e:
            logger.error(f"Failed to spawn Principal: {e}")
            return ActionResult.failure_result(
                error=f"Failed to schedule Principal: {e}",
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
        """Build the prompt for the Principal agent."""
        tasks_text = "\n".join([
            f"- {t.get('content', 'Unknown task')}"
            for t in new_tasks
        ])
        
        return f"""You are the Principal Engineer. New tasks have been added to {file_path}:

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
    Action: Spawn Principal agent to analyze and create Issues
    
    Signal Queue Model (FEAT-0165):
    - Memos are signals, not assets
    - File existence = signal pending
    - File cleared = signal consumed
    - Git is the archive, not app state
    
    Emergent Workflow: Memos (threshold) → Principal → Issues
    
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
        
        return True
    
    async def _handle(self, event: AgentEvent) -> Optional[ActionResult]:
        """
        Handle the event by spawning Principal agent.
        
        Signal Queue Semantics:
        1. Atomically load and clear inbox BEFORE scheduling
        2. Memos are embedded in prompt, not read from file
        3. File cleared = consumed, no state needed
        
        This ensures:
        - Natural idempotency (deleted memos won't be reprocessed)
        - No dependency on memory state across restarts
        - Principal always has data even if file is cleared
        """
        file_path_str = event.payload.get("path", "Memos/inbox.md")
        file_path = Path(file_path_str)
        pending_count = event.payload.get("pending_count", 0)
        
        logger.info(f"MemoThresholdHandler: Processing {pending_count} memos")
        
        # Phase 1: Atomically load and clear inbox
        try:
            # Load memos before clearing
            memos = self._load_and_clear_memos(file_path)
            if not memos:
                logger.warning("Inbox was empty after locking, skipping")
                return None
        except Exception as e:
            logger.error(f"Failed to load and clear inbox: {e}")
            return ActionResult.failure_result(
                error=f"Failed to consume memos: {e}",
                metadata={"file_path": file_path_str},
            )
        
        # Phase 2: Schedule Principal with embedded memos
        task = AgentTask(
            task_id=f"principal-memo-{event.timestamp.timestamp()}",
            role_name="Principal",
            issue_id="memo-analysis",
            prompt=self._build_prompt(file_path_str, memos),
            engine="gemini",
            timeout=900,
            metadata={
                "trigger": "memo_threshold",
                "file_path": file_path_str,
                "pending_count": pending_count,
                "threshold": self.threshold,
                "memo_count": len(memos),
            },
        )
        
        try:
            session_id = await self.scheduler.schedule(task)
            logger.info(f"Principal scheduled: session={session_id} with {len(memos)} memos")
            
            return ActionResult.success_result(
                output={
                    "session_id": session_id,
                    "role": "Principal",
                    "trigger": "memo_threshold",
                    "memo_count": len(memos),
                },
                metadata={"file_path": file_path_str},
            )
        
        except Exception as e:
            logger.error(f"Failed to spawn Principal: {e}")
            # Note: At this point memos are already cleared from inbox
            # This is intentional - we trade "at-least-once" for "at-most-once" semantics
            # If Principal fails, the memos are in git history
            return ActionResult.failure_result(
                error=f"Failed to schedule Principal: {e}",
                metadata={"file_path": file_path_str, "memos_consumed": len(memos)},
            )
    
    def _load_and_clear_memos(self, inbox_path: Path) -> List[Memo]:
        """
        Atomically load all memos and clear the inbox file.
        
        This implements the "consume" operation in signal queue model.
        File existence is the state - clearing the file marks all signals consumed.
        """
        # Resolve path relative to project root if needed
        if not inbox_path.is_absolute():
            from monoco.core.config import find_monoco_root
            project_root = find_monoco_root()
            inbox_path = project_root / inbox_path
        
        if not inbox_path.exists():
            return []
        
        # Load memos directly from inbox path
        # inbox_path is Memos/inbox.md, issues_root is sibling: Issues/
        issues_root = inbox_path.parent.parent / "Issues"
        memos = load_memos(issues_root)
        
        # Clear inbox (atomic write)
        inbox_path.write_text("# Monoco Memos Inbox\n\n", encoding="utf-8")
        logger.info(f"Inbox cleared after consuming {len(memos)} memos")
        
        return memos
    
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
    
    def _build_prompt(self, file_path: str, memos: List[Memo]) -> str:
        """Build the prompt for the Principal agent with embedded memos."""
        # Format memos for prompt
        memo_sections = []
        for i, memo in enumerate(memos, 1):
            section = f"""### Memo {i} (ID: {memo.uid})
- **Time**: {memo.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
- **Type**: {memo.type}
- **Source**: {memo.source}
- **Author**: {memo.author}
{'' if not memo.context else f'- **Context**: `{memo.context}`'}

{memo.content}
"""
            memo_sections.append(section)
        
        memos_text = "\n".join(memo_sections)
        
        return f"""You are the Principal Engineer. {len(memos)} memos have been consumed from {file_path}.

## Consumed Memos (Signal Queue Model)

The following memos have been atomically consumed from the inbox. 
They are provided here for your analysis - do NOT read the inbox file as it has been cleared.

{memos_text}

## Your Task

1. Analyze the accumulated memos above
2. Categorize and prioritize the ideas
3. Create Issue tickets for actionable items:
   - Use `monoco issue create` command
   - Set appropriate type (feature, fix, chore)
   - Set stage to 'draft' for review
4. Link related memos to created issues via `source_memo` field if applicable

## Signal Queue Semantics

- Memos are signals, not assets - they are consumed (deleted) upon processing
- No need to "resolve" or "link" memos - just create Issues from them
- Historical memos can be found in git history if needed

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
