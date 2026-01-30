"""Tests for LoggingHook."""

import pytest
import logging
from datetime import datetime, timedelta
from pathlib import Path

from monoco.core.hooks.builtin.logging_hook import LoggingHook
from monoco.core.hooks.context import HookContext, IssueInfo
from monoco.core.hooks.base import HookStatus


class TestLoggingHook:
    """Tests for LoggingHook."""

    def test_hook_initialization_defaults(self):
        hook = LoggingHook()
        
        assert hook.name == "logging"
        assert hook.log_level == logging.INFO
        assert hook.log_start is True
        assert hook.log_end is True

    def test_hook_initialization_with_config(self):
        config = {
            "log_level": "DEBUG",
            "log_start": False,
            "log_end": False,
        }
        hook = LoggingHook(config=config)
        
        assert hook.log_level == logging.DEBUG
        assert hook.log_start is False
        assert hook.log_end is False

    def test_parse_log_level(self):
        hook = LoggingHook()
        
        assert hook._parse_log_level("DEBUG") == logging.DEBUG
        assert hook._parse_log_level("INFO") == logging.INFO
        assert hook._parse_log_level("WARNING") == logging.WARNING
        assert hook._parse_log_level("ERROR") == logging.ERROR
        assert hook._parse_log_level("CRITICAL") == logging.CRITICAL
        assert hook._parse_log_level("UNKNOWN") == logging.INFO  # Default fallback

    def test_on_session_start_disabled(self):
        hook = LoggingHook(config={"log_start": False})
        context = HookContext(
            session_id="test",
            role_name="reviewer",
            session_status="running",
            created_at=None,
        )
        
        result = hook.on_session_start(context)
        
        assert result.status == HookStatus.SKIPPED
        assert "disabled" in result.message

    def test_on_session_start_success(self):
        hook = LoggingHook()
        context = HookContext(
            session_id="test-123",
            role_name="reviewer",
            session_status="running",
            created_at=None,
        )
        
        result = hook.on_session_start(context)
        
        assert result.status == HookStatus.SUCCESS
        assert "test-123" in result.message

    def test_on_session_start_with_issue(self):
        hook = LoggingHook()
        issue = IssueInfo(id="FEAT-0120", status="open")
        context = HookContext(
            session_id="test-123",
            role_name="reviewer",
            session_status="running",
            created_at=None,
            issue=issue,
        )
        
        result = hook.on_session_start(context)
        
        # Hook should succeed, and the log message should contain issue info
        assert result.status == HookStatus.SUCCESS
        assert "test-123" in result.message

    def test_on_session_end_disabled(self):
        hook = LoggingHook(config={"log_end": False})
        context = HookContext(
            session_id="test",
            role_name="reviewer",
            session_status="terminated",
            created_at=datetime.now(),
        )
        
        result = hook.on_session_end(context)
        
        assert result.status == HookStatus.SKIPPED
        assert "disabled" in result.message

    def test_on_session_end_success(self):
        hook = LoggingHook()
        created_at = datetime.now() - timedelta(seconds=5)
        context = HookContext(
            session_id="test-123",
            role_name="reviewer",
            session_status="terminated",
            created_at=created_at,
        )
        
        result = hook.on_session_end(context)
        
        assert result.status == HookStatus.SUCCESS
        assert "test-123" in result.message
        assert "duration" in result.message.lower()

    def test_on_session_end_with_issue(self):
        hook = LoggingHook()
        issue = IssueInfo(id="FEAT-0120", status="closed")
        created_at = datetime.now() - timedelta(minutes=1)
        context = HookContext(
            session_id="test-123",
            role_name="reviewer",
            session_status="terminated",
            created_at=created_at,
            issue=issue,
        )
        
        result = hook.on_session_end(context)
        
        # Hook should succeed, and the log message should contain issue info
        assert result.status == HookStatus.SUCCESS
        assert "test-123" in result.message
