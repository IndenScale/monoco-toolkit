"""
Tests for last-word module.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from monoco.features.last_word import (
    Entry,
    TargetKey,
    EntryMeta,
    OperationType,
    LastWordSchema,
    ValidationResult,
    LastWordConfig,
    KnowledgeBaseConfig,
    init_session,
    plan,
    process_session_end,
    get_buffer,
    clear_buffer,
    validate_entries,
    apply_entry_to_markdown,
    get_last_word_dir,
    ensure_directories,
    load_config,
    save_config,
)


class TestModels:
    """Test data models."""
    
    def test_target_key_creation(self):
        key = TargetKey(path="~/.config/agents/USER.md", heading="Test", level=2)
        assert key.heading == "Test"
        assert key.level == 2
        # Home directory should be expanded
        assert not key.path.startswith("~")
    
    def test_target_key_hashable(self):
        key1 = TargetKey(path="/path/to/file.md", heading="Test", level=2)
        key2 = TargetKey(path="/path/to/file.md", heading="Test", level=2)
        key3 = TargetKey(path="/path/to/file.md", heading="Other", level=2)
        
        assert key1 == key2
        assert key1 != key3
        assert hash(key1) == hash(key2)
    
    def test_entry_creation(self):
        entry = Entry(
            key=TargetKey(path="USER.md", heading="Test", level=2),
            operation=OperationType.UPDATE,
            content="Test content",
        )
        assert entry.operation == OperationType.UPDATE
        assert entry.content == "Test content"
        assert entry.meta.confidence == 0.9  # default
    
    def test_entry_auto_operation(self):
        # null content defaults to no-op
        entry1 = Entry(key=TargetKey(path="USER.md", heading="Test", level=2))
        assert entry1.operation == OperationType.NO_OP
        
        # empty string defaults to clear
        entry2 = Entry(
            key=TargetKey(path="USER.md", heading="Test", level=2),
            content="",
        )
        assert entry2.operation == OperationType.CLEAR
    
    def test_entry_yaml_roundtrip(self):
        entry = Entry(
            key=TargetKey(path="USER.md", heading="Test Section", level=2),
            operation=OperationType.UPDATE,
            content="Test content",
            meta=EntryMeta(confidence=0.95, reason="Test reason"),
        )
        
        yaml_dict = entry.to_yaml_dict()
        restored = Entry.from_yaml_dict(yaml_dict)
        
        assert restored.key.heading == entry.key.heading
        assert restored.operation == entry.operation
        assert restored.content == entry.content
        assert restored.meta.confidence == entry.meta.confidence
    
    def test_schema_yaml_roundtrip(self):
        schema = LastWordSchema(
            version="1.0.0",
            source="test_session",
            entries=[
                Entry(
                    key=TargetKey(path="USER.md", heading="Interests", level=2),
                    operation=OperationType.UPDATE,
                    content="- AI\n- ML",
                ),
            ],
        )
        
        yaml_str = schema.to_yaml()
        restored = LastWordSchema.from_yaml(yaml_str)
        
        assert restored.version == schema.version
        assert restored.source == schema.source
        assert len(restored.entries) == 1
        assert restored.entries[0].key.heading == "Interests"


class TestValidation:
    """Test entry validation."""
    
    def test_valid_entries(self):
        entries = [
            Entry(key=TargetKey(path="A.md", heading="H1", level=2)),
            Entry(key=TargetKey(path="A.md", heading="H2", level=2)),
            Entry(key=TargetKey(path="B.md", heading="H1", level=2)),
        ]
        result = validate_entries(entries)
        assert result.valid
        assert not result.has_errors
    
    def test_duplicate_heading_same_file(self):
        entries = [
            Entry(key=TargetKey(path="A.md", heading="Same", level=2)),
            Entry(key=TargetKey(path="A.md", heading="Same", level=2)),
        ]
        result = validate_entries(entries)
        assert not result.valid
        assert result.has_errors
        assert len(result.errors) == 1
        assert "Duplicate" in result.errors[0].error
    
    def test_same_heading_different_files(self):
        entries = [
            Entry(key=TargetKey(path="A.md", heading="Same", level=2)),
            Entry(key=TargetKey(path="B.md", heading="Same", level=2)),
        ]
        result = validate_entries(entries)
        assert result.valid  # Should be valid - different files
    
    def test_same_heading_different_levels(self):
        entries = [
            Entry(key=TargetKey(path="A.md", heading="Same", level=1)),
            Entry(key=TargetKey(path="A.md", heading="Same", level=2)),
        ]
        result = validate_entries(entries)
        assert result.valid  # Should be valid - different levels


class TestSessionBuffer:
    """Test session buffer operations."""
    
    def setup_method(self):
        clear_buffer()
    
    def teardown_method(self):
        clear_buffer()
    
    def test_init_session(self):
        session_id = init_session()
        assert session_id is not None
        assert session_id.startswith("session_")
    
    def test_plan_adds_to_buffer(self):
        init_session()
        entry = plan(path="USER.md", heading="Test", content="Content")
        
        buffer = get_buffer()
        assert len(buffer) == 1
        assert buffer[0].key.heading == "Test"
    
    def test_plan_auto_detects_operation(self):
        init_session()
        
        entry_update = plan(path="USER.md", heading="Update", content="Content")
        assert entry_update.operation == OperationType.UPDATE
        
        entry_clear = plan(path="USER.md", heading="Clear", content="")
        assert entry_clear.operation == OperationType.CLEAR
        
        entry_noop = plan(path="USER.md", heading="NoOp", content=None)
        assert entry_noop.operation == OperationType.NO_OP
    
    def test_clear_buffer(self):
        init_session()
        plan(path="USER.md", heading="Test", content="Content")
        
        assert len(get_buffer()) == 1
        clear_buffer()
        assert len(get_buffer()) == 0


class TestMarkdownApply:
    """Test applying entries to markdown."""
    
    def test_no_op(self):
        entry = Entry(
            key=TargetKey(path="USER.md", heading="Test", level=2),
            operation=OperationType.NO_OP,
        )
        content = "# Heading\n\nContent"
        result = apply_entry_to_markdown(entry, content)
        assert result == content
    
    def test_update_existing_section(self):
        entry = Entry(
            key=TargetKey(path="USER.md", heading="Section", level=2),
            operation=OperationType.UPDATE,
            content="New content",
        )
        content = "# Doc\n\n## Section\n\nOld content\n\n## Other\n\nMore"
        result = apply_entry_to_markdown(entry, content)
        
        assert "New content" in result
        assert "Old content" not in result
        assert "## Other" in result
    
    def test_update_append_new_section(self):
        entry = Entry(
            key=TargetKey(path="USER.md", heading="New Section", level=2),
            operation=OperationType.UPDATE,
            content="New content",
        )
        content = "# Doc\n\n## Existing\n\nContent"
        result = apply_entry_to_markdown(entry, content)
        
        assert "## New Section" in result
        assert "New content" in result
    
    def test_clear_section(self):
        entry = Entry(
            key=TargetKey(path="USER.md", heading="Section", level=2),
            operation=OperationType.CLEAR,
            content="",
        )
        content = "# Doc\n\n## Section\n\nContent to clear\n\n## Other"
        result = apply_entry_to_markdown(entry, content)
        
        assert "## Section" in result
        assert "Content to clear" not in result
    
    def test_delete_section(self):
        entry = Entry(
            key=TargetKey(path="USER.md", heading="Section", level=2),
            operation=OperationType.DELETE,
            content=None,
        )
        content = "# Doc\n\n## Section\n\nContent\n\n## Other\n\nMore"
        result = apply_entry_to_markdown(entry, content)
        
        assert "## Section" not in result
        assert "## Other" in result


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        config = LastWordConfig()
        
        assert config.global_agents.name == "global_agents"
        assert config.soul.name == "soul"
        assert config.user.name == "user"
        assert "global_agents" in config.session_bootstrap
    
    def test_get_knowledge_base(self):
        config = LastWordConfig()
        
        kb = config.get_knowledge_base("user")
        assert kb is not None
        assert kb.name == "user"
        
        kb_missing = config.get_knowledge_base("nonexistent")
        assert kb_missing is None


class TestIntegration:
    """Integration tests with filesystem."""
    
    def test_ensure_directories(self, tmp_path):
        with patch('monoco.features.last_word.core.get_last_word_dir') as mock_dir:
            mock_dir.return_value = tmp_path / "last-word"
            
            ensure_directories()
            
            assert (tmp_path / "last-word").exists()
            assert (tmp_path / "last-word" / "staging").exists()
    
    def test_process_session_end_empty(self):
        init_session()
        result = process_session_end()
        
        assert result["status"] == "empty"
    
    def test_process_session_end_with_entries(self, tmp_path):
        with patch('monoco.features.last_word.core.get_last_word_dir') as mock_dir:
            mock_dir.return_value = tmp_path / "last-word"
            
            init_session("test_session")
            plan(path="/test/USER.md", heading="Interests", content="- AI")
            
            result = process_session_end()
            
            assert result["status"] == "success"
            assert len(result["written"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
