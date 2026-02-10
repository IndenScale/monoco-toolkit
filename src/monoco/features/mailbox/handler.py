"""
Mailbox Agent Handler - Handles mailbox events and triggers appropriate agents.

This module provides:
- MailboxAgentHandler: Main handler for mailbox events
- MessageRouter: Routes messages to appropriate agents based on content
- SessionManager: Manages conversation sessions
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from monoco.core.scheduler import (
    AgentEvent,
    AgentEventType,
    AgentScheduler,
    AgentTask,
    EventBus,
    EventHandler,
)
from monoco.features.agent.models import RoleTemplate
from monoco.features.mailbox.store import MailboxConfig, MailboxStore
from monoco.features.mailbox.watcher import MailboxFileEvent

logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """Context for a mailbox message."""

    message_id: str
    provider: str
    session_id: Optional[str]
    sender: Optional[str]
    content: str
    raw_content: str
    mentions: List[str]
    attachments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    file_path: Path
    received_at: datetime


@dataclass
class RoutingRule:
    """Rule for routing messages to agents."""

    name: str
    condition: str  # "command", "mention", "keyword", "regex", "always"
    pattern: str
    agent_role: str
    priority: int = 0
    enabled: bool = True


class MessageRouter:
    """
    Routes messages to appropriate agents based on content analysis.
    """

    def __init__(self):
        self.rules: List[RoutingRule] = []
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default routing rules."""
        # Command rules
        self.rules.append(
            RoutingRule(
                name="help_command",
                condition="command",
                pattern="/help",
                agent_role="helper",
                priority=100,
            )
        )
        self.rules.append(
            RoutingRule(
                name="issue_command",
                condition="command",
                pattern="/issue",
                agent_role="drafter",
                priority=100,
            )
        )
        self.rules.append(
            RoutingRule(
                name="task_command",
                condition="command",
                pattern="/task",
                agent_role="task_manager",
                priority=100,
            )
        )

        # Mention rules
        self.rules.append(
            RoutingRule(
                name="prime_mention",
                condition="mention",
                pattern="@Prime",
                agent_role="prime",
                priority=90,
            )
        )
        self.rules.append(
            RoutingRule(
                name="architect_mention",
                condition="mention",
                pattern="@Architect",
                agent_role="architect",
                priority=90,
            )
        )

        # Keyword rules
        self.rules.append(
            RoutingRule(
                name="bug_keyword",
                condition="keyword",
                pattern="bug|error|crash|fix",
                agent_role="debugger",
                priority=50,
            )
        )
        self.rules.append(
            RoutingRule(
                name="question_keyword",
                condition="keyword",
                pattern="how to|what is|why|help with",
                agent_role="helper",
                priority=50,
            )
        )

        # Fallback rule
        self.rules.append(
            RoutingRule(
                name="fallback",
                condition="always",
                pattern="",
                agent_role="prime",
                priority=10,
            )
        )

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def route_message(self, context: MessageContext) -> Tuple[str, Dict[str, Any]]:
        """
        Route a message to an agent role.

        Args:
            context: Message context

        Returns:
            Tuple of (agent_role, routing_metadata)
        """
        content_lower = context.content.lower()

        for rule in self.rules:
            if not rule.enabled:
                continue

            matched = False
            metadata = {"rule": rule.name, "matched_pattern": rule.pattern}

            if rule.condition == "command":
                # Check if content starts with command pattern
                if content_lower.startswith(rule.pattern.lower()):
                    matched = True
                    metadata["command"] = rule.pattern

            elif rule.condition == "mention":
                # Check for mentions in content or metadata
                if rule.pattern.lower() in content_lower:
                    matched = True
                elif any(
                    mention.lower() == rule.pattern.lower()
                    for mention in context.mentions
                ):
                    matched = True

            elif rule.condition == "keyword":
                # Check for keywords in content
                if re.search(rf"\b{rule.pattern}\b", content_lower, re.IGNORECASE):
                    matched = True

            elif rule.condition == "regex":
                # Use regex pattern
                if re.search(rule.pattern, context.content, re.IGNORECASE):
                    matched = True

            elif rule.condition == "always":
                # Always match (fallback)
                matched = True

            if matched:
                logger.info(
                    f"Message {context.message_id} routed to {rule.agent_role} "
                    f"by rule {rule.name}"
                )
                return rule.agent_role, metadata

        # Should never reach here due to fallback rule
        return "prime", {"rule": "fallback", "reason": "no rule matched"}


class SessionManager:
    """
    Manages conversation sessions for mailbox messages.
    """

    def __init__(self, session_ttl: int = 3600):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_ttl = session_ttl  # seconds
        self._lock = asyncio.Lock()

    async def get_or_create_session(
        self, session_id: str, provider: str
    ) -> Dict[str, Any]:
        """
        Get or create a session.

        Args:
            session_id: Session identifier
            provider: Message provider

        Returns:
            Session data
        """
        async with self._lock:
            # Clean up expired sessions
            self._cleanup_sessions()

            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "id": session_id,
                    "provider": provider,
                    "created_at": datetime.now(),
                    "last_activity": datetime.now(),
                    "message_count": 0,
                    "agent_tasks": [],
                    "context": {},
                }

            session = self.sessions[session_id]
            session["last_activity"] = datetime.now()
            session["message_count"] += 1

            return session

    async def update_session_context(
        self, session_id: str, context_updates: Dict[str, Any]
    ) -> None:
        """
        Update session context.

        Args:
            session_id: Session identifier
            context_updates: Context updates to merge
        """
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session["context"].update(context_updates)
                session["last_activity"] = datetime.now()

    async def add_agent_task(self, session_id: str, task_id: str) -> None:
        """
        Add an agent task to session.

        Args:
            session_id: Session identifier
            task_id: Agent task identifier
        """
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if task_id not in session["agent_tasks"]:
                    session["agent_tasks"].append(task_id)
                session["last_activity"] = datetime.now()

    def _cleanup_sessions(self) -> None:
        """Clean up expired sessions."""
        now = datetime.now()
        expired = []

        for session_id, session in self.sessions.items():
            last_activity = session["last_activity"]
            if (now - last_activity).total_seconds() > self.session_ttl:
                expired.append(session_id)

        for session_id in expired:
            del self.sessions[session_id]
            logger.debug(f"Cleaned up expired session: {session_id}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": sum(
                1
                for s in self.sessions.values()
                if (datetime.now() - s["last_activity"]).total_seconds()
                < self.session_ttl
            ),
        }


class MailboxAgentHandler:
    """
    Handles mailbox events and triggers appropriate agents.

    This handler:
    1. Listens for MAILBOX_INBOUND_RECEIVED events
    2. Parses message files and extracts context
    3. Routes messages to appropriate agents
    4. Manages conversation sessions
    5. Triggers agent execution
    """

    def __init__(
        self,
        event_bus: EventBus,
        agent_scheduler: AgentScheduler,
        mailbox_root: Optional[Path] = None,
        debounce_window: int = 30,
    ):
        """
        Initialize the mailbox agent handler.

        Args:
            event_bus: Event bus for subscribing to events
            agent_scheduler: Agent scheduler for triggering agents
            mailbox_root: Root path for mailbox (default: ~/.monoco/mailbox)
            debounce_window: Debounce window in seconds for message aggregation
        """
        self.event_bus = event_bus
        self.agent_scheduler = agent_scheduler
        self.mailbox_root = mailbox_root
        self.debounce_window = debounce_window

        self.router = MessageRouter()
        self.session_manager = SessionManager()

        # Message aggregation buffers
        self._message_buffers: Dict[str, List[MessageContext]] = {}
        self._buffer_locks: Dict[str, asyncio.Lock] = {}
        self._processing_tasks: Set[asyncio.Task] = set()

        # Subscribe to mailbox events
        self.event_bus.subscribe(
            AgentEventType.MAILBOX_INBOUND_RECEIVED, self.handle_inbound
        )
        self.event_bus.subscribe(
            AgentEventType.MAILBOX_AGENT_TRIGGER, self.handle_trigger
        )

    async def __call__(self, event: AgentEvent) -> None:
        """
        Handle events - required by EventHandler protocol.

        This method routes events to the appropriate handler based on event type.

        Args:
            event: The agent event to handle
        """
        if event.event_type == AgentEventType.MAILBOX_INBOUND_RECEIVED:
            await self.handle_inbound(event)
        elif event.event_type == AgentEventType.MAILBOX_AGENT_TRIGGER:
            await self.handle_trigger(event)
        else:
            logger.warning(f"Unhandled event type: {event.event_type}")

    async def handle_inbound(self, event: AgentEvent) -> None:
        """
        Handle inbound mailbox message event.

        Args:
            event: Mailbox inbound event
        """
        try:
            # Extract file path from event
            file_path = Path(event.payload.get("path"))
            if not file_path.exists():
                logger.warning(f"Message file not found: {file_path}")
                return

            # Parse message file
            context = await self._parse_message_file(file_path)
            if not context:
                return

            logger.info(
                f"Received inbound message: {context.message_id} "
                f"from {context.sender or 'unknown'}"
            )

            # Add to debounce buffer
            await self._buffer_message(context)

        except Exception as e:
            logger.exception(f"Failed to handle inbound event: {e}")

    async def handle_trigger(self, event: AgentEvent) -> None:
        """
        Handle manual agent trigger event.

        Args:
            event: Agent trigger event
        """
        try:
            message_id = event.payload.get("message_id")
            if not message_id:
                logger.warning("No message_id in trigger event")
                return

            # Find and process the message
            await self._process_single_message(message_id)

        except Exception as e:
            logger.exception(f"Failed to handle trigger event: {e}")

    async def _parse_message_file(self, file_path: Path) -> Optional[MessageContext]:
        """
        Parse a mailbox message file.

        Args:
            file_path: Path to message file

        Returns:
            MessageContext if successful, None otherwise
        """
        try:
            from monoco.features.mailbox.store import MailboxStore

            # Create store to parse the file
            store = MailboxStore.__new__(MailboxStore)
            frontmatter, body = store._parse_frontmatter(file_path.read_text())

            if not frontmatter:
                logger.warning(f"Failed to parse frontmatter from {file_path}")
                return None

            # Extract message info
            message_id = frontmatter.get("id", "")
            provider = frontmatter.get("provider", "unknown")
            session = frontmatter.get("session", {})
            session_id = session.get("id")
            participants = frontmatter.get("participants", {})
            sender = participants.get("sender", {}).get("name")

            # Extract content
            content = body.strip()
            if not content and "content" in frontmatter:
                content_obj = frontmatter.get("content", {})
                content = content_obj.get("text") or content_obj.get("markdown") or ""

            # Extract mentions
            mentions = frontmatter.get("mentions", [])
            if not mentions and "@" in content:
                # Extract @mentions from content
                mentions = re.findall(r"@\w+", content)

            # Extract attachments
            artifacts = frontmatter.get("artifacts", [])

            return MessageContext(
                message_id=message_id,
                provider=provider,
                session_id=session_id,
                sender=sender,
                content=content,
                raw_content=body,
                mentions=mentions,
                attachments=artifacts,
                metadata=frontmatter,
                file_path=file_path,
                received_at=datetime.now(),
            )

        except Exception as e:
            logger.exception(f"Failed to parse message file {file_path}: {e}")
            return None

    async def _buffer_message(self, context: MessageContext) -> None:
        """
        Buffer a message for debouncing.

        Args:
            context: Message context
        """
        buffer_key = context.session_id or context.message_id

        # Ensure lock exists for this buffer
        if buffer_key not in self._buffer_locks:
            self._buffer_locks[buffer_key] = asyncio.Lock()
            self._message_buffers[buffer_key] = []

        async with self._buffer_locks[buffer_key]:
            self._message_buffers[buffer_key].append(context)

            # Schedule processing if this is the first message in buffer
            if len(self._message_buffers[buffer_key]) == 1:
                # Schedule delayed processing
                task = asyncio.create_task(self._process_buffered_messages(buffer_key))
                self._processing_tasks.add(task)
                task.add_done_callback(self._processing_tasks.discard)

    async def _process_buffered_messages(self, buffer_key: str) -> None:
        """
        Process buffered messages after debounce window.

        Args:
            buffer_key: Buffer identifier
        """
        # Wait for debounce window
        await asyncio.sleep(self.debounce_window)

        async with self._buffer_locks.get(buffer_key, asyncio.Lock()):
            if buffer_key not in self._message_buffers:
                return

            messages = self._message_buffers.pop(buffer_key, [])
            if buffer_key in self._buffer_locks:
                del self._buffer_locks[buffer_key]

            if not messages:
                return

            # Process all buffered messages
            await self._process_messages(messages)

    async def _process_single_message(self, message_id: str) -> None:
        """
        Process a single message immediately.

        Args:
            message_id: Message identifier
        """
        # Find the message file
        if not self.mailbox_root:
            logger.error("Mailbox root not configured")
            return

        # Search for message file
        for provider_dir in (self.mailbox_root / "inbound").iterdir():
            if not provider_dir.is_dir():
                continue

            for file_path in provider_dir.glob("*.md"):
                context = await self._parse_message_file(file_path)
                if context and context.message_id == message_id:
                    await self._process_messages([context])
                    return

        logger.warning(f"Message not found: {message_id}")

    async def _process_messages(self, messages: List[MessageContext]) -> None:
        """
        Process a batch of messages.

        Args:
            messages: List of message contexts
        """
        if not messages:
            return

        # Use the first message for session context
        first_message = messages[0]
        session_id = first_message.session_id or f"single_{first_message.message_id}"

        try:
            # Get or create session
            session = await self.session_manager.get_or_create_session(
                session_id, first_message.provider
            )

            # Combine message contents
            combined_content = "\n\n".join(
                [f"{msg.sender or 'User'}: {msg.content}" for msg in messages]
            )

            # Create combined context
            combined_context = MessageContext(
                message_id=f"batch_{first_message.message_id}",
                provider=first_message.provider,
                session_id=session_id,
                sender=first_message.sender,
                content=combined_content,
                raw_content=combined_content,
                mentions=list(
                    set(mention for msg in messages for mention in msg.mentions)
                ),
                attachments=[
                    attachment for msg in messages for attachment in msg.attachments
                ],
                metadata={
                    "batch_size": len(messages),
                    "message_ids": [msg.message_id for msg in messages],
                    "senders": [msg.sender for msg in messages],
                },
                file_path=first_message.file_path,
                received_at=datetime.now(),
            )

            # Route message to agent
            agent_role, routing_metadata = self.router.route_message(combined_context)

            # Update session context
            await self.session_manager.update_session_context(
                session_id,
                {
                    "last_message": combined_content,
                    "last_agent_role": agent_role,
                    "routing_metadata": routing_metadata,
                },
            )

            # Trigger agent
            await self._trigger_agent(agent_role, combined_context, session_id)

            logger.info(
                f"Processed {len(messages)} messages in session {session_id}, "
                f"routed to {agent_role}"
            )

        except Exception as e:
            logger.exception(f"Failed to process messages: {e}")

    async def _trigger_agent(
        self, agent_role: str, context: MessageContext, session_id: str
    ) -> Optional[str]:
        """
        Trigger an agent to process the message.

        Args:
            agent_role: Agent role name
            context: Message context
            session_id: Session identifier

        Returns:
            Agent task ID if triggered, None otherwise
        """
        try:
            # Build agent prompt from message context
            prompt = self._build_agent_prompt(agent_role, context)

            # Create agent task
            task = AgentTask(
                task_id=f"mailbox_{context.message_id}",
                role_name=agent_role,
                prompt=prompt,
                issue_id="",  # Mailbox tasks don't have issue IDs
                metadata={
                    "message_id": context.message_id,
                    "provider": context.provider,
                    "session_id": session_id,
                    "sender": context.sender,
                    "content": context.content,
                    "mentions": context.mentions,
                    "attachments": context.attachments,
                    "metadata": context.metadata,
                    "file_path": str(context.file_path),
                },
                timeout=300,  # 5 minutes timeout
            )

            # Schedule agent
            task_id = await self.agent_scheduler.schedule(task)

            # Update session with task info
            await self.session_manager.add_agent_task(session_id, task_id)

            logger.info(
                f"Triggered agent {agent_role} for message {context.message_id}, "
                f"task_id: {task_id}"
            )

            # Publish agent triggered event
            await self.event_bus.publish(
                AgentEventType.MAILBOX_AGENT_TRIGGER,
                {
                    "task_id": task_id,
                    "agent_role": agent_role,
                    "message_id": context.message_id,
                    "session_id": session_id,
                },
                source="mailbox_handler",
            )

            return task_id

        except Exception as e:
            logger.exception(f"Failed to trigger agent {agent_role}: {e}")
            return None

    def _build_agent_prompt(self, agent_role: str, context: MessageContext) -> str:
        """
        Build agent prompt from message context.

        Args:
            agent_role: Agent role name
            context: Message context

        Returns:
            Formatted prompt string
        """
        # Base prompt template
        base_prompt = f"""You are the {agent_role} agent in the Monoco system.

Message Context:
- From: {context.sender or "Unknown"}
- Provider: {context.provider}
- Session: {context.session_id or "Single message"}
- Mentions: {", ".join(context.mentions) if context.mentions else "None"}

Message Content:
{context.content}

Attachments: {len(context.attachments)} files attached

Instructions:
1. Analyze the message and determine the appropriate action
2. If this is a command, execute it
3. If this is a question, provide a helpful answer
4. If this requires creating an issue or task, do so
5. Keep responses concise and actionable

Remember: You are operating within the Monoco system. Use available tools and commands.
"""

        # Role-specific additions
        if agent_role == "prime":
            base_prompt += "\n\nAs the Prime Agent, you are responsible for overall coordination. Delegate to specialized agents when appropriate."
        elif agent_role == "drafter":
            base_prompt += "\n\nAs the Drafter Agent, focus on creating well-structured issues. Use 'monoco issue create' command."
        elif agent_role == "helper":
            base_prompt += "\n\nAs the Helper Agent, provide clear explanations and guidance. Be patient and thorough."
        elif agent_role == "debugger":
            base_prompt += "\n\nAs the Debugger Agent, analyze problems systematically. Look for root causes and suggest fixes."

        return base_prompt

    async def shutdown(self) -> None:
        """Shutdown the handler and cleanup resources."""
        # Cancel all processing tasks
        for task in self._processing_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)

        # Clear buffers
        self._message_buffers.clear()
        self._buffer_locks.clear()
        self._processing_tasks.clear()

        logger.info("MailboxAgentHandler shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "buffered_messages": sum(
                len(buf) for buf in self._message_buffers.values()
            ),
            "active_buffers": len(self._message_buffers),
            "processing_tasks": len(self._processing_tasks),
            "session_stats": self.session_manager.get_session_stats(),
        }
