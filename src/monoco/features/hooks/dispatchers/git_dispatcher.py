"""
Git Hooks Dispatcher for Universal Hooks system.

Manages installation, execution, and uninstallation of Git hooks
to the `.git/hooks/` directory with non-destructive installation
and Glob matcher support for staged files.
"""

import fnmatch
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ..manager import HookDispatcher
from ..models import GitEvent, HookType, ParsedHook


class GitHookDispatcher(HookDispatcher):
    """
    Dispatcher for Git lifecycle hooks.

    Responsible for:
    - Installing hook proxy scripts to `.git/hooks/`
    - Executing hooks with staged file filtering
    - Non-destructive installation (coexisting with Husky/pre-commit)
    - Uninstalling and restoring original hooks

    Supported events:
    - pre-commit
    - prepare-commit-msg
    - commit-msg
    - post-merge
    - pre-push
    - post-checkout
    - pre-rebase
    """

    # Marker used to identify Monoco-managed hooks
    HOOK_MARKER = "MONOCO_HOOK_MARKER"
    BACKUP_SUFFIX = ".monoco.backup"

    def __init__(self):
        """Initialize the Git hook dispatcher."""
        super().__init__(HookType.GIT, provider=None)
        self._git_dir: Optional[Path] = None
        self._hooks_dir: Optional[Path] = None

    def _ensure_git_repo(self, project_root: Path) -> bool:
        """
        Check if project_root is a git repository and set up paths.

        Args:
            project_root: The project root directory

        Returns:
            True if valid git repository, False otherwise
        """
        git_dir = project_root / ".git"
        if not git_dir.exists():
            return False

        self._git_dir = git_dir
        self._hooks_dir = git_dir / "hooks"
        self._hooks_dir.mkdir(exist_ok=True)
        return True

    def can_execute(self, hook: ParsedHook) -> bool:
        """
        Check if this dispatcher can execute the given hook.

        Args:
            hook: The parsed hook to check

        Returns:
            True if this is a git hook
        """
        return hook.metadata.type == HookType.GIT

    def execute(self, hook: ParsedHook, context: Optional[dict] = None) -> bool:
        """
        Execute a git hook script.

        Args:
            hook: The parsed hook to execute
            context: Optional execution context with 'event' and 'git_root'

        Returns:
            True if execution succeeded
        """
        if not hook.script_path.exists():
            return False

        # Check if we need to filter by staged files
        if hook.metadata.matcher and context:
            git_root = context.get("git_root")
            if git_root and not self._should_trigger_for_staged_files(
                git_root, hook.metadata.matcher
            ):
                # No matching staged files, skip silently
                return True

        # Execute the hook script
        try:
            env = os.environ.copy()
            if context:
                env["MONOCO_HOOK_EVENT"] = context.get("event", "")
                env["MONOCO_HOOK_TYPE"] = "git"

            result = subprocess.run(
                [str(hook.script_path)],
                cwd=hook.script_path.parent,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return result.returncode == 0
        except Exception:
            return False

    def _should_trigger_for_staged_files(
        self, git_root: Path, matchers: list[str]
    ) -> bool:
        """
        Check if any staged files match the given glob patterns.

        Args:
            git_root: Path to the git repository root
            matchers: List of glob patterns to match

        Returns:
            True if any staged file matches any pattern
        """
        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return True  # If we can't get staged files, allow execution

            staged_files = result.stdout.strip().split("\n")
            staged_files = [f for f in staged_files if f]

            if not staged_files:
                return False  # No staged files, don't trigger

            # Check if any staged file matches any pattern
            for file_path in staged_files:
                for pattern in matchers:
                    if fnmatch.fnmatch(file_path, pattern):
                        return True
                    # Also try matching against just the filename
                    if fnmatch.fnmatch(Path(file_path).name, pattern):
                        return True

            return False

        except Exception:
            # If anything goes wrong, allow execution
            return True

    def install(
        self,
        hook: ParsedHook,
        project_root: Path,
        hook_id: Optional[str] = None,
    ) -> bool:
        """
        Install a hook proxy script to `.git/hooks/`.

        The proxy script calls `monoco hook run git <event>` to execute
the actual hook logic.

        Args:
            hook: The parsed hook to install
            project_root: The project root directory
            hook_id: Optional unique identifier for this hook

        Returns:
            True if installation succeeded
        """
        if not self._ensure_git_repo(project_root):
            return False

        event = hook.metadata.event
        if not event:
            return False

        hook_path = self._hooks_dir / event
        hook_id = hook_id or hook.script_path.stem

        # Generate proxy script content
        proxy_content = self._generate_proxy_script(event, hook_id, hook.metadata.matcher)

        if hook_path.exists():
            # Check if it's already managed by us
            existing_content = hook_path.read_text(encoding="utf-8")
            if self.HOOK_MARKER in existing_content:
                # Already our hook, update it
                hook_path.write_text(proxy_content, encoding="utf-8")
                os.chmod(hook_path, 0o755)
                return True
            else:
                # Existing hook not managed by us - backup and merge
                return self._install_merged(hook_path, proxy_content, event, hook_id)
        else:
            # Fresh install
            hook_path.write_text(proxy_content, encoding="utf-8")
            os.chmod(hook_path, 0o755)
            return True

    def _generate_proxy_script(
        self,
        event: str,
        hook_id: str,
        matchers: Optional[list[str]] = None,
    ) -> str:
        """
        Generate a proxy script for a git hook.

        Args:
            event: The git hook event (e.g., "pre-commit")
            hook_id: Unique identifier for this hook
            matchers: Optional list of glob patterns for file filtering

        Returns:
            The proxy script content
        """
        # Build staged files check if matchers are provided
        staged_check = ""
        if matchers:
            patterns_str = " ".join(f'"{m}"' for m in matchers)
            staged_check = f"""
# Check if staged files match patterns
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

MATCHED=false
PATTERNS="{patterns_str}"
for file in $STAGED_FILES; do
    for pattern in $PATTERNS; do
        case "$file" in
            $pattern | */$pattern)
                MATCHED=true
                break 2
                ;;
        esac
    done
done

if [ "$MATCHED" = "false" ]; then
    exit 0
fi
"""

        return f"""#!/bin/sh
# {self.HOOK_MARKER}: {hook_id}
# Auto-generated by Monoco. Do not edit manually.

{staged_check}
# Execute Monoco hook
exec uv run python3 -m monoco hook run git {event} "$@"
"""

    def _install_merged(
        self,
        hook_path: Path,
        proxy_content: str,
        event: str,
        hook_id: str,
    ) -> bool:
        """
        Install by merging with an existing hook.

        Creates a backup of the original and appends our proxy.

        Args:
            hook_path: Path to the existing hook
            proxy_content: Our proxy script content
            event: The git hook event
            hook_id: Unique identifier for this hook

        Returns:
            True if installation succeeded
        """
        try:
            # Backup original hook
            backup_path = hook_path.with_suffix(self.BACKUP_SUFFIX)
            shutil.copy2(hook_path, backup_path)

            # Read original content
            original_content = hook_path.read_text(encoding="utf-8")

            # Create merged content - original runs first, then our proxy
            # Extract just the execution part from our proxy (without shebang)
            proxy_lines = proxy_content.split("\n")
            exec_lines = []
            in_staged_check = False
            for line in proxy_lines:
                if line.startswith("#!/"):
                    continue
                if "exec monoco hook run" in line:
                    # Replace exec with direct call to allow continuation
                    line = line.replace("exec ", "")
                exec_lines.append(line)

            merged_content = f"""#!/bin/sh
# {self.HOOK_MARKER}: merged
# Original hook preserved by Monoco

# Run original hook
ORIGINAL_EXIT=$?

# Run Monoco hook
{chr(10).join(exec_lines)}
MONOCO_EXIT=$?

# Return non-zero if either failed
if [ $ORIGINAL_EXIT -ne 0 ]; then
    exit $ORIGINAL_EXIT
fi
exit $MONOCO_EXIT
"""

            # Insert original content before "Run original hook" comment
            marker = "# Run original hook"
            if marker in merged_content:
                parts = merged_content.split(marker)
                merged_content = parts[0] + original_content + "\n" + marker + parts[1]

            hook_path.write_text(merged_content, encoding="utf-8")
            os.chmod(hook_path, 0o755)
            return True

        except Exception:
            return False

    def uninstall(
        self,
        event: str,
        project_root: Path,
        hook_id: Optional[str] = None,
    ) -> bool:
        """
        Uninstall a hook from `.git/hooks/`.

        Restores the original hook if it was backed up.

        Args:
            event: The git hook event (e.g., "pre-commit")
            project_root: The project root directory
            hook_id: Optional hook identifier (for selective uninstall)

        Returns:
            True if uninstallation succeeded
        """
        if not self._ensure_git_repo(project_root):
            return False

        hook_path = self._hooks_dir / event
        if not hook_path.exists():
            return True  # Already uninstalled

        try:
            content = hook_path.read_text(encoding="utf-8")

            # Check if it's our marker
            if self.HOOK_MARKER not in content:
                # Not our hook, skip
                return True

            # Check for backup
            backup_path = hook_path.with_suffix(self.BACKUP_SUFFIX)
            if backup_path.exists():
                # Restore original
                shutil.move(backup_path, hook_path)
                return True
            else:
                # No backup, just remove
                hook_path.unlink()
                return True

        except Exception:
            return False

    def list_installed(self, project_root: Path) -> list[dict]:
        """
        List all Git hooks installed by Monoco.

        Args:
            project_root: The project root directory

        Returns:
            List of installed hook information
        """
        if not self._ensure_git_repo(project_root):
            return []

        installed = []

        for event in GitEvent:
            hook_path = self._hooks_dir / event.value
            if hook_path.exists():
                try:
                    content = hook_path.read_text(encoding="utf-8")
                    if self.HOOK_MARKER in content:
                        # Extract hook ID from marker
                        hook_id = None
                        for line in content.split("\n"):
                            if self.HOOK_MARKER in line:
                                parts = line.split(":")
                                if len(parts) >= 2:
                                    hook_id = parts[1].strip()
                                break

                        installed.append({
                            "event": event.value,
                            "hook_id": hook_id,
                            "path": str(hook_path),
                            "is_merged": "merged" in content,
                        })
                except Exception:
                    pass

        return installed

    def sync(
        self,
        hooks: list[ParsedHook],
        project_root: Path,
    ) -> dict[str, bool]:
        """
        Synchronize all git hooks with the repository.

        Installs new hooks, updates existing ones, and removes
        hooks that are no longer in the list.

        Args:
            hooks: List of parsed hooks to install
            project_root: The project root directory

        Returns:
            Dictionary mapping hook events to success status
        """
        results = {}

        if not self._ensure_git_repo(project_root):
            return results

        # Get current installed hooks
        current = self.list_installed(project_root)
        current_events = {h["event"] for h in current}

        # Install/update hooks
        new_events = set()
        for hook in hooks:
            if hook.metadata.type != HookType.GIT:
                continue

            event = hook.metadata.event
            new_events.add(event)
            results[event] = self.install(hook, project_root)

        # Remove hooks that are no longer needed
        for old_event in current_events - new_events:
            results[old_event] = self.uninstall(old_event, project_root)

        return results
