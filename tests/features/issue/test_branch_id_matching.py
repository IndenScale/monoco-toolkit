"""
Tests for strict branch-to-issue ID matching (FIX-0013, FIX-0014).

Ensures that `sync_issue_files()` only matches branches with exact ID,
preventing substring collisions like FEAT-1 matching FEAT-123-login.

Branch format: <ID>-<slug> (e.g., FEAT-0123-login-page)
"""

import pytest
from monoco.features.issue.core import _extract_issue_id_from_branch


class TestExtractIssueIdFromBranch:
    """Test branch name to issue ID extraction (new flat format)."""

    @pytest.mark.parametrize("branch,expected", [
        # New flat format: ID-slug
        ("FEAT-0123-login-page", "FEAT-0123"),
        ("FEAT-0123", "FEAT-0123"),
        ("FEAT-0001", "FEAT-0001"),

        # Different types
        ("FIX-0001-critical", "FIX-0001"),
        ("CHORE-0099", "CHORE-0099"),
        ("EPIC-0001", "EPIC-0001"),

        # Edge case: non-standard digit counts
        ("FEAT-123-login", "FEAT-123"),  # 3 digits
        ("FEAT-1-short", "FEAT-1"),  # single digit
        ("FEAT-123456-long-slug", "FEAT-123456"),  # 6 digits

        # Case insensitive input
        ("feat-0123", "FEAT-0123"),
        ("Feat-0123-Test", "FEAT-0123"),
    ])
    def test_valid_branch_formats(self, branch, expected):
        """Branch names in flat format extract correctly."""
        result = _extract_issue_id_from_branch(branch)
        assert result == expected

    @pytest.mark.parametrize("branch", [
        # Non-issue branches
        "main",
        "master",
        "develop",
        "dev",
        "release/v1.0",
        "hotfix/urgent",

        # Old format (no longer supported)
        "feat/feat-0123-login",
        "feat/feat-0123",
        "fix/fix-0001",

        # Invalid formats
        "something-else",  # no valid prefix
        "123",  # no prefix
        "feat",  # no number
    ])
    def test_invalid_branch_formats(self, branch):
        """Non-conforming branch names return None."""
        result = _extract_issue_id_from_branch(branch)
        assert result is None


class TestStrictIdMatching:
    """Test that IDs match strictly, not by substring (security test)."""

    def _match_logic(self, branch: str, issue_id: str) -> bool:
        """Simulate the matching logic in sync_issue_files."""
        branch_id = _extract_issue_id_from_branch(branch)
        return branch_id is not None and branch_id.upper() == issue_id.upper()

    @pytest.mark.parametrize("branch,issue_id,should_match", [
        # Exact matches (should succeed)
        ("FEAT-0001-login", "FEAT-0001", True),
        ("FEAT-0123", "FEAT-0123", True),

        # CRITICAL: Substring matches must fail
        # FEAT-1 should NOT match FEAT-123-*
        ("FEAT-123-login-page", "FEAT-1", False),
        ("FEAT-123", "FEAT-1", False),
        ("FEAT-0123", "FEAT-01", False),  # Different ID

        # FEAT-0123 should NOT match FEAT-01234-*
        ("FEAT-01234-extra", "FEAT-0123", False),

        # Different prefixes should not match
        ("FEAT-0001", "FIX-0001", False),
        ("FIX-0001", "FEAT-0001", False),

        # Non-issue branches should not match any ID
        ("main", "FEAT-0001", False),
        ("develop", "EPIC-0001", False),
    ])
    def test_id_matching_security(self, branch, issue_id, should_match):
        """Verify strict ID matching prevents cross-branch contamination."""
        result = self._match_logic(branch, issue_id)

        if should_match:
            assert result is True, \
                f"Expected {issue_id} to match branch '{branch}'"
        else:
            assert result is False, \
                f"SECURITY: {issue_id} should NOT match branch '{branch}' - " \
                f"this could cause cross-branch file contamination!"


class TestRegressionFIX0013:
    """Regression tests for FIX-0013: Substring matching vulnerability."""

    def test_feat_1_does_not_match_feat_123(self):
        """
        Original bug: FEAT-1 would match FEAT-123-login via substring.
        After fix: Must not match.
        """
        branch = "FEAT-123-login-page"
        issue_id = "FEAT-1"

        branch_id = _extract_issue_id_from_branch(branch)
        match = branch_id is not None and branch_id.upper() == issue_id.upper()

        assert branch_id == "FEAT-123"  # Extracts correct ID
        assert match is False, \
            "CRITICAL: FEAT-1 must not match FEAT-123-* branches"

    def test_feat_123_only_matches_exact_id(self):
        """FEAT-123 should only match branches with ID=123, not 1234 or 0123."""
        cases = [
            ("FEAT-123-login", "FEAT-123", True),   # Exact match
            ("FEAT-0123", "FEAT-0123", True),       # Different format, but exact string match
            ("FEAT-1234-extra", "FEAT-123", False), # Different ID (1234 != 123)
            ("FEAT-01234", "FEAT-0123", False),     # Different ID (01234 != 0123)
        ]

        for branch, issue_id, should_match in cases:
            branch_id = _extract_issue_id_from_branch(branch)
            match = branch_id == issue_id

            if should_match:
                assert match is True, f"Expected {issue_id} to match {branch}, got {branch_id}"
            else:
                assert match is False, f"{issue_id} should not match {branch}, got {branch_id}"
