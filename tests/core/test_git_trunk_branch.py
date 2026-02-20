"""Tests for trunk branch configuration (FEAT-0202)."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from monoco.core import git


class TestGetTrunkBranch:
    """Tests for get_trunk_branch function."""

    def test_returns_configured_trunk_when_exists(self, tmp_path):
        """Should return configured trunk branch if it exists."""
        with patch.object(git, 'branch_exists') as mock_exists:
            mock_exists.return_value = True
            
            result = git.get_trunk_branch(tmp_path, "develop")
            
            assert result == "develop"
            mock_exists.assert_called_with(tmp_path, "develop")

    def test_fallback_to_main_when_configured_missing(self, tmp_path):
        """Should fallback to 'main' if configured trunk doesn't exist but main does."""
        def side_effect(path, branch):
            return branch == "main"
        
        with patch.object(git, 'branch_exists', side_effect=side_effect):
            result = git.get_trunk_branch(tmp_path, "custom-trunk")
            
            assert result == "main"

    def test_fallback_to_master_when_main_missing(self, tmp_path):
        """Should fallback to 'master' if both configured and main don't exist."""
        def side_effect(path, branch):
            return branch == "master"
        
        with patch.object(git, 'branch_exists', side_effect=side_effect):
            result = git.get_trunk_branch(tmp_path, "custom-trunk")
            
            assert result == "master"

    def test_returns_configured_when_no_branches_exist(self, tmp_path):
        """Should return configured value even if no branches exist (caller handles)."""
        with patch.object(git, 'branch_exists', return_value=False):
            result = git.get_trunk_branch(tmp_path, "trunk")
            
            assert result == "trunk"

    def test_default_configured_value(self, tmp_path):
        """Should use 'main' as default configured value."""
        with patch.object(git, 'branch_exists', return_value=True) as mock_exists:
            result = git.get_trunk_branch(tmp_path)
            
            assert result == "main"
            mock_exists.assert_called_with(tmp_path, "main")

    def test_priority_order_configured_first(self, tmp_path):
        """Configured trunk should be checked first before fallbacks."""
        call_order = []
        
        def side_effect(path, branch):
            call_order.append(branch)
            return branch == "main"  # Only main exists
        
        with patch.object(git, 'branch_exists', side_effect=side_effect):
            result = git.get_trunk_branch(tmp_path, "custom")
            
            assert call_order[0] == "custom"
            assert call_order[1] == "main"
