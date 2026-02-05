"""
Tests for Issue Lifecycle Hooks System

Tests cover:
- Model definitions (IssueEvent, HookDecision, IssueHookResult)
- IssueHookDispatcher functionality
- AgentToolAdapter
- NamingACL mappings
- Integration helpers
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from monoco.features.issue.hooks import (
    IssueEvent,
    HookDecision,
    IssueHookResult,
    IssueHookContext,
    HookMetadata,
    NamingACL,
    IssueHookDispatcher,
    get_events_for_command,
    build_hook_context,
    execute_hooks,
    AgentToolAdapter,
    ParsedIssueCommand,
)


class TestIssueEvent:
    """Tests for IssueEvent enum."""
    
    def test_issue_lifecycle_events(self):
        """Test that all lifecycle events follow pre/post naming."""
        assert IssueEvent.PRE_CREATE.value == "pre-issue-create"
        assert IssueEvent.POST_CREATE.value == "post-issue-create"
        assert IssueEvent.PRE_START.value == "pre-issue-start"
        assert IssueEvent.POST_START.value == "post-issue-start"
        assert IssueEvent.PRE_SUBMIT.value == "pre-issue-submit"
        assert IssueEvent.POST_SUBMIT.value == "post-issue-submit"
        assert IssueEvent.PRE_CLOSE.value == "pre-issue-close"
        assert IssueEvent.POST_CLOSE.value == "post-issue-close"
    
    def test_all_events_are_canonical(self):
        """Test that all events follow canonical pre/post naming."""
        for event in IssueEvent:
            assert event.value.startswith(("pre-", "post-"))


class TestHookDecision:
    """Tests for HookDecision enum."""
    
    def test_decision_values(self):
        """Test decision values."""
        assert HookDecision.ALLOW.value == "allow"
        assert HookDecision.WARN.value == "warn"
        assert HookDecision.DENY.value == "deny"


class TestIssueHookResult:
    """Tests for IssueHookResult model."""
    
    def test_default_allow_result(self):
        """Test default ALLOW result creation."""
        result = IssueHookResult.allow("All good")
        
        assert result.decision == HookDecision.ALLOW
        assert result.message == "All good"
        assert result.suggestions == []
        assert result.diagnostics == []
    
    def test_warn_result(self):
        """Test WARN result creation."""
        suggestions = ["Check this", "Check that"]
        result = IssueHookResult.warn("Warning message", suggestions)
        
        assert result.decision == HookDecision.WARN
        assert result.message == "Warning message"
        assert result.suggestions == suggestions
    
    def test_deny_result(self):
        """Test DENY result creation."""
        suggestions = ["Fix this issue"]
        result = IssueHookResult.deny("Error occurred", suggestions)
        
        assert result.decision == HookDecision.DENY
        assert result.message == "Error occurred"
        assert result.suggestions == suggestions


class TestNamingACL:
    """Tests for NamingACL event mapping."""
    
    def test_claude_mapping(self):
        """Test Claude Code event mappings."""
        assert NamingACL.to_agent_event("pre-tool-use", "claude") == "PreToolUse"
        assert NamingACL.to_agent_event("post-tool-use", "claude") == "PostToolUse"
        assert NamingACL.to_agent_event("pre-session", "claude") == "SessionStart"
    
    def test_gemini_mapping(self):
        """Test Gemini CLI event mappings."""
        assert NamingACL.to_agent_event("pre-tool-use", "gemini") == "BeforeTool"
        assert NamingACL.to_agent_event("post-tool-use", "gemini") == "AfterTool"
        assert NamingACL.to_agent_event("pre-session", "gemini") == "SessionStart"
    
    def test_from_claude_event(self):
        """Test reverse mapping from Claude events."""
        assert NamingACL.from_agent_event("PreToolUse", "claude") == "pre-tool-use"
        assert NamingACL.from_agent_event("PostToolUse", "claude") == "post-tool-use"
        assert NamingACL.from_agent_event("SessionStart", "claude") == "pre-session"
    
    def test_is_canonical(self):
        """Test canonical naming detection."""
        assert NamingACL.is_canonical("pre-issue-start") == True
        assert NamingACL.is_canonical("post-issue-submit") == True
        assert NamingACL.is_canonical("PreToolUse") == False
        assert NamingACL.is_canonical("random-event") == False


class TestGetEventsForCommand:
    """Tests for command to event mapping."""
    
    def test_start_command_events(self):
        """Test events for start command."""
        pre, post = get_events_for_command("start")
        assert pre == IssueEvent.PRE_START
        assert post == IssueEvent.POST_START
    
    def test_submit_command_events(self):
        """Test events for submit command."""
        pre, post = get_events_for_command("submit")
        assert pre == IssueEvent.PRE_SUBMIT
        assert post == IssueEvent.POST_SUBMIT
    
    def test_close_command_events(self):
        """Test events for close command."""
        pre, post = get_events_for_command("close")
        assert pre == IssueEvent.PRE_CLOSE
        assert post == IssueEvent.POST_CLOSE
    
    def test_unknown_command(self):
        """Test unknown command returns None."""
        pre, post = get_events_for_command("unknown")
        assert pre is None
        assert post is None


class TestIssueHookContext:
    """Tests for IssueHookContext model."""
    
    def test_context_creation(self):
        """Test creating hook context."""
        context = IssueHookContext(
            event=IssueEvent.PRE_SUBMIT,
            issue_id="FEAT-123",
            trigger_source="cli",
        )
        
        assert context.event == IssueEvent.PRE_SUBMIT
        assert context.issue_id == "FEAT-123"
        assert context.trigger_source == "cli"
        assert isinstance(context.timestamp, datetime)
    
    def test_context_with_git_info(self):
        """Test context with git information."""
        context = IssueHookContext(
            event=IssueEvent.PRE_START,
            issue_id="FEAT-123",
            current_branch="feature/FEAT-123-test",
            default_branch="main",
            has_uncommitted_changes=True,
        )
        
        assert context.current_branch == "feature/FEAT-123-test"
        assert context.default_branch == "main"
        assert context.has_uncommitted_changes == True


class TestIssueHookDispatcher:
    """Tests for IssueHookDispatcher."""
    
    def test_dispatcher_creation(self, tmp_path):
        """Test creating a dispatcher."""
        dispatcher = IssueHookDispatcher(project_root=tmp_path)
        
        assert dispatcher.project_root == tmp_path
        assert dispatcher._user_hooks_dir == tmp_path / ".monoco" / "hooks" / "issue"
    
    def test_register_callable_hook(self, tmp_path):
        """Test registering a callable hook."""
        dispatcher = IssueHookDispatcher(project_root=tmp_path)
        
        def test_hook(context: IssueHookContext) -> IssueHookResult:
            return IssueHookResult.allow("Test passed")
        
        dispatcher.register_callable(
            name="test.hook",
            events=[IssueEvent.PRE_SUBMIT],
            fn=test_hook,
            priority=10,
        )
        
        hooks = dispatcher.get_hooks_for_event(IssueEvent.PRE_SUBMIT)
        assert len(hooks) == 1
        assert hooks[0].name == "test.hook"
        assert hooks[0].priority == 10
    
    def test_execute_hooks_allow(self, tmp_path):
        """Test executing hooks that return ALLOW."""
        dispatcher = IssueHookDispatcher(project_root=tmp_path)
        
        def allow_hook(context: IssueHookContext) -> IssueHookResult:
            return IssueHookResult.allow("Allowed")
        
        dispatcher.register_callable(
            name="allow.hook",
            events=[IssueEvent.PRE_START],
            fn=allow_hook,
        )
        
        context = IssueHookContext(
            event=IssueEvent.PRE_START,
            issue_id="FEAT-123",
        )
        
        result = dispatcher.execute(IssueEvent.PRE_START, context)
        
        assert result.decision == HookDecision.ALLOW
    
    def test_execute_hooks_deny(self, tmp_path):
        """Test executing hooks that return DENY."""
        dispatcher = IssueHookDispatcher(project_root=tmp_path)
        
        def deny_hook(context: IssueHookContext) -> IssueHookResult:
            return IssueHookResult.deny("Denied", ["Fix this"])
        
        dispatcher.register_callable(
            name="deny.hook",
            events=[IssueEvent.PRE_SUBMIT],
            fn=deny_hook,
        )
        
        context = IssueHookContext(
            event=IssueEvent.PRE_SUBMIT,
            issue_id="FEAT-123",
        )
        
        result = dispatcher.execute(IssueEvent.PRE_SUBMIT, context)
        
        assert result.decision == HookDecision.DENY
        assert "Fix this" in result.suggestions
    
    def test_execute_no_hooks(self, tmp_path):
        """Test execution with no_hooks flag."""
        dispatcher = IssueHookDispatcher(project_root=tmp_path)
        
        context = IssueHookContext(
            event=IssueEvent.PRE_START,
            issue_id="FEAT-123",
            no_hooks=True,
        )
        
        result = dispatcher.execute(IssueEvent.PRE_START, context)
        
        assert result.decision == HookDecision.ALLOW
        assert "skipped" in result.message.lower()
    
    def test_hook_priority_ordering(self, tmp_path):
        """Test hooks are executed in priority order."""
        dispatcher = IssueHookDispatcher(project_root=tmp_path)
        
        execution_order = []
        
        def high_priority_hook(context: IssueHookContext) -> IssueHookResult:
            execution_order.append("high")
            return IssueHookResult.allow()
        
        def low_priority_hook(context: IssueHookContext) -> IssueHookResult:
            execution_order.append("low")
            return IssueHookResult.allow()
        
        dispatcher.register_callable(
            name="low.hook",
            events=[IssueEvent.PRE_START],
            fn=low_priority_hook,
            priority=100,
        )
        
        dispatcher.register_callable(
            name="high.hook",
            events=[IssueEvent.PRE_START],
            fn=high_priority_hook,
            priority=10,
        )
        
        context = IssueHookContext(event=IssueEvent.PRE_START)
        dispatcher.execute(IssueEvent.PRE_START, context)
        
        assert execution_order == ["high", "low"]


class TestAgentToolAdapter:
    """Tests for AgentToolAdapter."""
    
    def test_parse_start_command(self, tmp_path):
        """Test parsing start command."""
        adapter = AgentToolAdapter(project_root=tmp_path)
        
        parsed = adapter.parse_command("monoco issue start FEAT-123 --branch")
        
        assert parsed is not None
        assert parsed.subcommand == "start"
        assert parsed.issue_id == "FEAT-123"
        assert parsed.args.get("branch") == True
    
    def test_parse_submit_command(self, tmp_path):
        """Test parsing submit command."""
        adapter = AgentToolAdapter(project_root=tmp_path)
        
        parsed = adapter.parse_command("monoco issue submit FEAT-123 --force")
        
        assert parsed is not None
        assert parsed.subcommand == "submit"
        assert parsed.issue_id == "FEAT-123"
        assert parsed.args.get("force") == True
    
    def test_parse_non_issue_command(self, tmp_path):
        """Test parsing non-issue command returns None."""
        adapter = AgentToolAdapter(project_root=tmp_path)
        
        parsed = adapter.parse_command("monoco memo add test")
        
        assert parsed is None
    
    def test_translate_event(self, tmp_path):
        """Test event translation."""
        adapter = AgentToolAdapter(project_root=tmp_path, agent_type="claude")
        
        # translate_event returns IssueEvent (mapped from Agent events)
        # but PreToolUse maps to pre-tool-use which is not in IssueEvent
        # It is in AgnosticAgentEvent, so the method returns None
        event = adapter.translate_event("PreToolUse")
        # PreToolUse maps to pre-tool-use which is AgnosticAgentEvent, not IssueEvent
        # So the method returns None for this case
        assert event is None
        
        # Test with an event that does map to IssueEvent
        # (e.g., through some other mechanism or future extension)
        # For now, we just verify the method handles the mapping correctly
    
    def test_translate_back_allow(self, tmp_path):
        """Test translating ALLOW result."""
        adapter = AgentToolAdapter(project_root=tmp_path)
        
        result = IssueHookResult.allow("Success")
        translated = adapter.translate_back(result)
        
        assert translated["decision"] == "allow"
        assert translated["allow"] == True
        assert translated["block"] == False
    
    def test_translate_back_deny(self, tmp_path):
        """Test translating DENY result."""
        adapter = AgentToolAdapter(project_root=tmp_path)
        
        result = IssueHookResult.deny("Failed", ["Fix this"])
        translated = adapter.translate_back(result)
        
        assert translated["decision"] == "deny"
        assert translated["allow"] == False
        assert translated["block"] == True
        assert "suggestions" in translated


class TestBuildHookContext:
    """Tests for build_hook_context helper."""
    
    def test_basic_context(self):
        """Test building basic context."""
        context = build_hook_context(
            event=IssueEvent.PRE_START,
            issue_id="FEAT-123",
            force=True,
        )
        
        assert context.event == IssueEvent.PRE_START
        assert context.issue_id == "FEAT-123"
        assert context.force == True
    
    def test_context_with_status_transition(self):
        """Test context with status transition."""
        context = build_hook_context(
            event=IssueEvent.PRE_SUBMIT,
            issue_id="FEAT-123",
            from_stage="doing",
            to_stage="review",
        )
        
        assert context.from_stage == "doing"
        assert context.to_stage == "review"


class TestIntegration:
    """Integration tests for the hooks system."""
    
    def test_full_hook_flow(self, tmp_path):
        """Test complete hook execution flow."""
        dispatcher = IssueHookDispatcher(project_root=tmp_path)
        
        # Register a hook that tracks execution
        execution_log = []
        
        def tracking_hook(context: IssueHookContext) -> IssueHookResult:
            execution_log.append({
                "event": context.event.value,
                "issue_id": context.issue_id,
            })
            return IssueHookResult.allow(f"Executed {context.event.value}")
        
        dispatcher.register_callable(
            name="tracking.hook",
            events=[IssueEvent.PRE_START, IssueEvent.POST_START],
            fn=tracking_hook,
        )
        
        # Execute pre-start
        pre_context = IssueHookContext(
            event=IssueEvent.PRE_START,
            issue_id="FEAT-123",
        )
        pre_result = dispatcher.execute(IssueEvent.PRE_START, pre_context)
        
        assert pre_result.decision == HookDecision.ALLOW
        assert execution_log[0]["event"] == "pre-issue-start"
        
        # Execute post-start
        post_context = IssueHookContext(
            event=IssueEvent.POST_START,
            issue_id="FEAT-123",
        )
        post_result = dispatcher.execute(IssueEvent.POST_START, post_context)
        
        assert post_result.decision == HookDecision.ALLOW
        assert execution_log[1]["event"] == "post-issue-start"
        assert execution_log[1]["event"] == "post-issue-start"
