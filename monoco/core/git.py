from typing import List, Tuple, Optional, Dict, Callable, Awaitable
import asyncio
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("monoco.core.git")


def _run_git(args: List[str], cwd: Path) -> Tuple[int, str, str]:
    """Run a raw git command."""
    try:
        result = subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "Git executable not found"


def is_git_repo(path: Path) -> bool:
    code, _, _ = _run_git(["rev-parse", "--is-inside-work-tree"], path)
    return code == 0


def get_git_status(path: Path, subpath: Optional[str] = None) -> List[str]:
    """
    Get list of modified files.
    If subpath is provided, only check that path.
    """
    cmd = ["status", "--porcelain"]
    if subpath:
        cmd.append(subpath)

    code, stdout, _ = _run_git(cmd, path)
    if code != 0:
        raise RuntimeError("Failed to check git status")

    lines = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Porcelain format: XY PATH
        if len(line) > 3:
            path_str = line[3:]
            if path_str.startswith('"') and path_str.endswith('"'):
                path_str = path_str[1:-1]
            lines.append(path_str)
    return lines


def git_add(path: Path, files: List[str]) -> None:
    if not files:
        return
    code, _, stderr = _run_git(["add"] + files, path)
    if code != 0:
        raise RuntimeError(f"Git add failed: {stderr}")


def git_commit(path: Path, message: str) -> str:
    code, stdout, stderr = _run_git(["commit", "-m", message], path)
    if code != 0:
        raise RuntimeError(f"Git commit failed: {stderr}")

    code, hash_out, _ = _run_git(["rev-parse", "HEAD"], path)
    return hash_out.strip()


def search_commits_by_message(path: Path, grep_pattern: str) -> List[Dict[str, str]]:
    cmd = ["log", f"--grep={grep_pattern}", "--name-only", "--format=COMMIT:%H|%s"]
    code, stdout, stderr = _run_git(cmd, path)
    if code != 0:
        raise RuntimeError(f"Git log failed: {stderr}")

    commits = []
    current_commit = None

    for line in stdout.splitlines():
        if line.startswith("COMMIT:"):
            if current_commit:
                commits.append(current_commit)

            parts = line[7:].split("|", 1)
            current_commit = {
                "hash": parts[0],
                "subject": parts[1] if len(parts) > 1 else "",
                "files": [],
            }
        elif line.strip():
            if current_commit:
                current_commit["files"].append(line.strip())

    if current_commit:
        commits.append(current_commit)

    return commits


def get_commit_stats(path: Path, commit_hash: str) -> Dict[str, int]:
    cmd = ["show", "--shortstat", "--format=", commit_hash]
    code, stdout, _ = _run_git(cmd, path)
    stats = {"files": 0, "insertions": 0, "deletions": 0}
    if code == 0 and stdout.strip():
        parts = stdout.strip().split(",")
        for p in parts:
            p = p.strip()
            if "file" in p:
                stats["files"] = int(p.split()[0])
            elif "insertion" in p:
                stats["insertions"] = int(p.split()[0])
            elif "deletion" in p:
                stats["deletions"] = int(p.split()[0])
    return stats


# --- Branch & Worktree Extensions ---


def get_current_branch(path: Path) -> str:
    code, stdout, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], path)
    if code != 0:
        return ""
    return stdout.strip()


def branch_exists(path: Path, branch_name: str) -> bool:
    code, _, _ = _run_git(["rev-parse", "--verify", branch_name], path)
    return code == 0


def create_branch(path: Path, branch_name: str, checkout: bool = False):
    cmd = ["checkout", "-b", branch_name] if checkout else ["branch", branch_name]
    code, _, stderr = _run_git(cmd, path)
    if code != 0:
        raise RuntimeError(f"Failed to create branch {branch_name}: {stderr}")


def checkout_branch(path: Path, branch_name: str):
    code, _, stderr = _run_git(["checkout", branch_name], path)
    if code != 0:
        raise RuntimeError(f"Failed to checkout {branch_name}: {stderr}")


def delete_branch(path: Path, branch_name: str, force: bool = False):
    flag = "-D" if force else "-d"
    code, _, stderr = _run_git(["branch", flag, branch_name], path)
    if code != 0:
        raise RuntimeError(f"Failed to delete branch {branch_name}: {stderr}")


def get_merge_base(path: Path, ref1: str, ref2: str) -> str:
    code, stdout, stderr = _run_git(["merge-base", ref1, ref2], path)
    if code != 0:
        raise RuntimeError(f"Failed to find merge base: {stderr}")
    return stdout.strip()


def git_checkout_files(path: Path, ref: str, files: List[str]):
    if not files:
        return
    code, _, stderr = _run_git(["checkout", ref, "--"] + files, path)
    if code != 0:
        raise RuntimeError(f"Failed to checkout files from {ref}: {stderr}")


def has_diff(path: Path, ref1: str, ref2: str, files: List[str]) -> bool:
    """Check if there are differences between two refs for specific files."""
    if not files:
        return False
    code, stdout, _ = _run_git(["diff", "--name-only", ref1, ref2, "--"] + files, path)
    return code == 0 and bool(stdout.strip())


def get_worktrees(path: Path) -> List[Tuple[str, str, str]]:
    """Returns list of (path, head, branch)"""
    code, stdout, stderr = _run_git(["worktree", "list", "--porcelain"], path)
    if code != 0:
        raise RuntimeError(f"Failed to list worktrees: {stderr}")

    trees = []
    current = {}
    for line in stdout.splitlines():
        if line.startswith("worktree "):
            if current:
                trees.append(
                    (
                        current.get("worktree"),
                        current.get("HEAD"),
                        current.get("branch"),
                    )
                )
            current = {"worktree": line[9:].strip()}
        elif line.startswith("HEAD "):
            current["HEAD"] = line[5:].strip()
        elif line.startswith("branch "):
            current["branch"] = line[7:].strip()

    if current:
        trees.append(
            (current.get("worktree"), current.get("HEAD"), current.get("branch"))
        )
    return trees


def worktree_add(path: Path, branch_name: str, worktree_path: Path):
    # If branch doesn't exist, -b will create it.
    # Logic: git worktree add [-b <new_branch>] <path> <commit-ish>

    # We assume if branch_exists, use it. If not, create it.
    cmd = ["worktree", "add"]
    if not branch_exists(path, branch_name):
        cmd.extend(["-b", branch_name])

    cmd.extend([str(worktree_path), branch_name])

    code, _, stderr = _run_git(cmd, path)
    if code != 0:
        raise RuntimeError(f"Failed to create worktree: {stderr}")


def worktree_remove(path: Path, worktree_path: Path, force: bool = False):
    cmd = ["worktree", "remove"]
    if force:
        cmd.append("--force")
    cmd.append(str(worktree_path))

    code, _, stderr = _run_git(cmd, path)
    if code != 0:
        raise RuntimeError(f"Failed to remove worktree: {stderr}")


class GitMonitor:
    """
    Polls the Git repository for HEAD changes and triggers updates.
    """

    def __init__(
        self,
        path: Path,
        on_head_change: Callable[[str], Awaitable[None]],
        poll_interval: float = 2.0,
    ):
        self.path = path
        self.on_head_change = on_head_change
        self.poll_interval = poll_interval
        self.last_head_hash: Optional[str] = None
        self.is_running = False

    async def get_head_hash(self) -> Optional[str]:
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "HEAD",
                cwd=self.path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode().strip()
            return None
        except Exception as e:
            logger.error(f"Git polling error: {e}")
            return None

    async def start(self):
        self.is_running = True
        logger.info(f"Git Monitor started for {self.path}.")

        self.last_head_hash = await self.get_head_hash()

        while self.is_running:
            await asyncio.sleep(self.poll_interval)
            current_hash = await self.get_head_hash()

            if current_hash and current_hash != self.last_head_hash:
                logger.info(
                    f"Git HEAD changed: {self.last_head_hash} -> {current_hash}"
                )
                self.last_head_hash = current_hash
                await self.on_head_change(current_hash)

    def stop(self):
        self.is_running = False
        logger.info(f"Git Monitor stopping for {self.path}...")
