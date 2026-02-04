"""Tests for GitHookDispatcher."""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from monoco.features.hooks.dispatchers.git_dispatcher import GitHookDispatcher
from monoco.features.hooks.models import (
    GitEvent,
    HookMetadata,
    HookType,
    ParsedHook,
)


class TestGitHookDispatcherBasics:
    """Tests for basic GitHookDispatcher functionality."""

    def test_dispatcher_initialization(self):
        """Should initialize with correct type."""
        dispatcher = GitHookDispatcher()

        assert dispatcher.hook_type == HookType.GIT
        assert dispatcher.provider is None
        assert dispatcher.key == "git"

    def test_can_execute_git_hook(self):
        """Should be able to execute git hooks."""
        dispatcher = GitHookDispatcher()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.GIT

        assert dispatcher.can_execute(hook) is True

    def test_cannot_execute_non_git_hook(self):
        """Should not execute non-git hooks."""
        dispatcher = GitHookDispatcher()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.AGENT

        assert dispatcher.can_execute(hook) is False


class TestGitHookDispatcherInstall:
    """Tests for GitHookDispatcher.install method."""

    def test_install_fresh_hook(self, tmp_path):
        """Should install hook to .git/hooks/."""
        # Create git repo structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        dispatcher = GitHookDispatcher()

        script_path = tmp_path / "test-hook.sh"
        script_path.touch()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.event = "pre-commit"
        hook.metadata.matcher = None
        hook.script_path = script_path

        result = dispatcher.install(hook, tmp_path)

        assert result is True
        hook_path = hooks_dir / "pre-commit"
        assert hook_path.exists()

        content = hook_path.read_text()
        assert "MONOCO_HOOK_MARKER" in content
        assert "monoco hook run git pre-commit" in content
        assert os.access(hook_path, os.X_OK)

    def test_install_updates_existing_monoco_hook(self, tmp_path):
        """Should update existing Monoco-managed hook."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create existing Monoco hook
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("""#!/bin/sh
# MONOCO_HOOK_MARKER: old-hook
# Old content
exec monoco hook run git pre-commit "$@"
""")

        dispatcher = GitHookDispatcher()

        new_script = tmp_path / "new-hook.sh"
        new_script.touch()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.event = "pre-commit"
        hook.metadata.matcher = None
        hook.script_path = new_script

        result = dispatcher.install(hook, tmp_path)

        assert result is True
        content = hook_path.read_text()
        assert "new-hook" in content

    def test_install_with_matchers(self, tmp_path):
        """Should install hook with file matchers."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        dispatcher = GitHookDispatcher()

        lint_script = tmp_path / "lint.sh"
        lint_script.touch()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.event = "pre-commit"
        hook.metadata.matcher = ["*.py", "*.js"]
        hook.script_path = lint_script

        result = dispatcher.install(hook, tmp_path)

        assert result is True
        hook_path = hooks_dir / "pre-commit"
        content = hook_path.read_text()
        assert "*.py" in content
        assert "*.js" in content
        assert "STAGED_FILES" in content

    def test_install_merges_with_existing_hook(self, tmp_path):
        """Should merge with existing non-Monoco hook."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create existing non-Monoco hook
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("""#!/bin/sh
# Existing hook
echo "Running existing hook"
""")

        dispatcher = GitHookDispatcher()

        new_script = tmp_path / "new.sh"
        new_script.touch()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.event = "pre-commit"
        hook.metadata.matcher = None
        hook.script_path = new_script

        result = dispatcher.install(hook, tmp_path)

        assert result is True
        content = hook_path.read_text()
        assert "MONOCO_HOOK_MARKER: merged" in content
        assert "Running existing hook" in content
        assert "monoco hook run" in content

        # Check backup was created
        backup_path = hook_path.with_suffix(".monoco.backup")
        assert backup_path.exists()

    def test_install_fails_without_git_repo(self, tmp_path):
        """Should fail if not in a git repository."""
        dispatcher = GitHookDispatcher()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.event = "pre-commit"

        result = dispatcher.install(hook, tmp_path)

        assert result is False


class TestGitHookDispatcherUninstall:
    """Tests for GitHookDispatcher.uninstall method."""

    def test_uninstall_removes_hook(self, tmp_path):
        """Should remove installed hook."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create Monoco hook
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("""#!/bin/sh
# MONOCO_HOOK_MARKER: test-hook
exec monoco hook run git pre-commit "$@"
""")

        dispatcher = GitHookDispatcher()

        result = dispatcher.uninstall("pre-commit", tmp_path)

        assert result is True
        assert not hook_path.exists()

    def test_uninstall_restores_backup(self, tmp_path):
        """Should restore original hook from backup."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create backup
        hook_path = hooks_dir / "pre-commit"
        backup_path = hook_path.with_suffix(".monoco.backup")
        backup_path.write_text("""#!/bin/sh
# Original hook
echo "Original"
""")

        # Create merged hook
        hook_path.write_text("""#!/bin/sh
# MONOCO_HOOK_MARKER: merged
# Original hook
echo "Original"
# Run Monoco hook
monoco hook run git pre-commit "$@"
""")

        dispatcher = GitHookDispatcher()

        result = dispatcher.uninstall("pre-commit", tmp_path)

        assert result is True
        content = hook_path.read_text()
        assert "MONOCO_HOOK_MARKER" not in content
        assert "Original" in content
        assert not backup_path.exists()

    def test_uninstall_nonexistent_hook(self, tmp_path):
        """Should succeed if hook doesn't exist."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        dispatcher = GitHookDispatcher()

        result = dispatcher.uninstall("pre-commit", tmp_path)

        assert result is True

    def test_uninstall_skips_non_monoco_hook(self, tmp_path):
        """Should not uninstall non-Monoco hooks."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create non-Monoco hook
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("""#!/bin/sh
# Custom hook
echo "Custom"
""")

        dispatcher = GitHookDispatcher()

        result = dispatcher.uninstall("pre-commit", tmp_path)

        assert result is True
        assert hook_path.exists()


class TestGitHookDispatcherListInstalled:
    """Tests for GitHookDispatcher.list_installed method."""

    def test_list_installed_hooks(self, tmp_path):
        """Should list all installed Monoco hooks."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create Monoco hooks
        (hooks_dir / "pre-commit").write_text("""#!/bin/sh
# MONOCO_HOOK_MARKER: hook-1
exec monoco hook run git pre-commit "$@"
""")
        (hooks_dir / "pre-push").write_text("""#!/bin/sh
# MONOCO_HOOK_MARKER: hook-2
exec monoco hook run git pre-push "$@"
""")
        # Create non-Monoco hook
        (hooks_dir / "post-commit").write_text("""#!/bin/sh
echo "Custom"
""")

        dispatcher = GitHookDispatcher()

        installed = dispatcher.list_installed(tmp_path)

        assert len(installed) == 2
        events = {h["event"] for h in installed}
        assert "pre-commit" in events
        assert "pre-push" in events

    def test_list_installed_empty(self, tmp_path):
        """Should return empty list when no hooks installed."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        dispatcher = GitHookDispatcher()

        installed = dispatcher.list_installed(tmp_path)

        assert installed == []

    def test_list_installed_not_git_repo(self, tmp_path):
        """Should return empty list when not in git repo."""
        dispatcher = GitHookDispatcher()

        installed = dispatcher.list_installed(tmp_path)

        assert installed == []


class TestGitHookDispatcherSync:
    """Tests for GitHookDispatcher.sync method."""

    def test_sync_installs_new_hooks(self, tmp_path):
        """Should install new hooks."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        dispatcher = GitHookDispatcher()

        script1 = tmp_path / "hook1.sh"
        script1.touch()
        hook1 = Mock(spec=ParsedHook)
        hook1.metadata = Mock(spec=HookMetadata)
        hook1.metadata.type = HookType.GIT
        hook1.metadata.event = "pre-commit"
        hook1.metadata.matcher = None
        hook1.script_path = script1

        script2 = tmp_path / "hook2.sh"
        script2.touch()
        hook2 = Mock(spec=ParsedHook)
        hook2.metadata = Mock(spec=HookMetadata)
        hook2.metadata.type = HookType.GIT
        hook2.metadata.event = "pre-push"
        hook2.metadata.matcher = None
        hook2.script_path = script2

        results = dispatcher.sync([hook1, hook2], tmp_path)

        assert len(results) == 2
        assert results["pre-commit"] is True
        assert results["pre-push"] is True
        assert (hooks_dir / "pre-commit").exists()
        assert (hooks_dir / "pre-push").exists()

    def test_sync_removes_orphaned_hooks(self, tmp_path):
        """Should remove hooks no longer in list."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create existing Monoco hook
        (hooks_dir / "post-merge").write_text("""#!/bin/sh
# MONOCO_HOOK_MARKER: old-hook
exec monoco hook run git post-merge "$@"
""")

        dispatcher = GitHookDispatcher()

        script = tmp_path / "hook.sh"
        script.touch()
        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.GIT
        hook.metadata.event = "pre-commit"
        hook.metadata.matcher = None
        hook.script_path = script

        results = dispatcher.sync([hook], tmp_path)

        # post-merge should be removed
        assert not (hooks_dir / "post-merge").exists()
        assert "post-merge" in results

    def test_sync_skips_non_git_hooks(self, tmp_path):
        """Should skip non-git hooks in sync."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        dispatcher = GitHookDispatcher()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.AGENT  # Not GIT
        hook.metadata.event = "before-tool"

        results = dispatcher.sync([hook], tmp_path)

        assert results == {}


class TestGitHookDispatcherExecute:
    """Tests for GitHookDispatcher.execute method."""

    def test_execute_hook_success(self, tmp_path):
        """Should execute hook script successfully."""
        dispatcher = GitHookDispatcher()

        # Create executable script
        script = tmp_path / "test.sh"
        script.write_text("#!/bin/bash\necho 'Hello'")
        script.chmod(0o755)

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.GIT
        hook.metadata.matcher = None
        hook.script_path = script

        result = dispatcher.execute(hook)

        assert result is True

    def test_execute_hook_failure(self, tmp_path):
        """Should return False when hook fails."""
        dispatcher = GitHookDispatcher()

        # Create failing script
        script = tmp_path / "test.sh"
        script.write_text("#!/bin/bash\nexit 1")
        script.chmod(0o755)

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.GIT
        hook.metadata.matcher = None
        hook.script_path = script

        result = dispatcher.execute(hook)

        assert result is False

    def test_execute_missing_script(self, tmp_path):
        """Should return False when script doesn't exist."""
        dispatcher = GitHookDispatcher()

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.GIT
        hook.metadata.matcher = None
        hook.script_path = tmp_path / "nonexistent.sh"

        result = dispatcher.execute(hook)

        assert result is False

    @patch("subprocess.run")
    def test_execute_with_staged_files_check(self, mock_run, tmp_path):
        """Should check staged files when matchers provided."""
        dispatcher = GitHookDispatcher()

        # Mock git command to return staged files
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file.py\nfile.js\n",
            stderr=""
        )

        script = tmp_path / "test.sh"
        script.write_text("#!/bin/bash\necho 'Hello'")
        script.chmod(0o755)

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.GIT
        hook.metadata.matcher = ["*.py"]
        hook.script_path = script

        context = {"git_root": str(tmp_path)}
        result = dispatcher.execute(hook, context)

        assert result is True
        # subprocess.run is called twice: once for git diff, once for hook execution
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_execute_skips_when_no_matching_files(self, mock_run, tmp_path):
        """Should skip execution when no files match."""
        dispatcher = GitHookDispatcher()

        # Mock git command to return no matching staged files
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file.txt\n",  # No .py files
            stderr=""
        )

        script = tmp_path / "test.sh"
        script.write_text("#!/bin/bash\necho 'Hello'")
        script.chmod(0o755)

        hook = Mock(spec=ParsedHook)
        hook.metadata = Mock(spec=HookMetadata)
        hook.metadata.type = HookType.GIT
        hook.metadata.matcher = ["*.py"]
        hook.script_path = script

        context = {"git_root": str(tmp_path)}
        result = dispatcher.execute(hook, context)

        # Should return True (silently skipped)
        assert result is True


class TestGitHookDispatcherStagedFiles:
    """Tests for staged files filtering."""

    @patch("subprocess.run")
    def test_should_trigger_for_matching_files(self, mock_run, tmp_path):
        """Should return True when staged files match pattern."""
        dispatcher = GitHookDispatcher()

        mock_run.return_value = Mock(
            returncode=0,
            stdout="src/main.py\ntests/test.py\n",
            stderr=""
        )

        result = dispatcher._should_trigger_for_staged_files(
            tmp_path, ["*.py"]
        )

        assert result is True

    @patch("subprocess.run")
    def test_should_not_trigger_for_non_matching_files(self, mock_run, tmp_path):
        """Should return False when no staged files match."""
        dispatcher = GitHookDispatcher()

        mock_run.return_value = Mock(
            returncode=0,
            stdout="README.md\nLICENSE\n",
            stderr=""
        )

        result = dispatcher._should_trigger_for_staged_files(
            tmp_path, ["*.py"]
        )

        assert result is False

    @patch("subprocess.run")
    def test_should_trigger_when_git_fails(self, mock_run, tmp_path):
        """Should return True when git command fails (fail-safe)."""
        dispatcher = GitHookDispatcher()

        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="error"
        )

        result = dispatcher._should_trigger_for_staged_files(
            tmp_path, ["*.py"]
        )

        assert result is True

    @patch("subprocess.run")
    def test_should_not_trigger_when_no_staged_files(self, mock_run, tmp_path):
        """Should return False when no staged files."""
        dispatcher = GitHookDispatcher()

        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = dispatcher._should_trigger_for_staged_files(
            tmp_path, ["*.py"]
        )

        assert result is False

    @patch("subprocess.run")
    def test_matches_filename_only(self, mock_run, tmp_path):
        """Should match against filename only, not just full path."""
        dispatcher = GitHookDispatcher()

        mock_run.return_value = Mock(
            returncode=0,
            stdout="path/to/file.py\n",
            stderr=""
        )

        result = dispatcher._should_trigger_for_staged_files(
            tmp_path, ["file.py"]
        )

        assert result is True


class TestGitHookDispatcherProxyScript:
    """Tests for proxy script generation."""

    def test_generate_basic_proxy_script(self):
        """Should generate basic proxy script."""
        dispatcher = GitHookDispatcher()

        content = dispatcher._generate_proxy_script("pre-commit", "my-hook", None)

        assert "#!/bin/sh" in content
        assert "MONOCO_HOOK_MARKER: my-hook" in content
        assert "monoco hook run git pre-commit" in content

    def test_generate_proxy_with_matchers(self):
        """Should generate proxy with staged file check."""
        dispatcher = GitHookDispatcher()

        content = dispatcher._generate_proxy_script(
            "pre-commit", "my-hook", ["*.py", "*.js"]
        )

        assert "STAGED_FILES" in content
        assert "*.py" in content
        assert "*.js" in content
        assert "MATCHED" in content

    def test_proxy_script_exits_cleanly_when_no_match(self):
        """Proxy should exit 0 when no files match."""
        dispatcher = GitHookDispatcher()

        content = dispatcher._generate_proxy_script(
            "pre-commit", "my-hook", ["*.py"]
        )

        # Should have exit 0 when no match
        assert "exit 0" in content
