import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

def _run_git(args: List[str], cwd: Path) -> Tuple[int, str, str]:
    """Run a raw git command."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
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
        # XY are two chars, then space.
        # But if we used just split(), it handles spaces.
        # Wait, simple split on whitespace? Path might have spaces.
        # Standard porcelain v1: "XY Path"
        # Untracked: "?? Path"
        # We can slice from 3.
        if len(line) > 3:
            path_str = line[3:]
            # If renamed, "R  New -> Old" (Wait, "R" is recursive?)
            # No, renames in --porcelain are "R  ORIG_PATH -> NEW_PATH"
            # But let's assume simple add/mod for issues.
            # Usually we don't do renames in this logic yet.
            # Handle quotes? "?? \"path with spaces\""
            if path_str.startswith('"') and path_str.endswith('"'):
                path_str = path_str[1:-1]
                # TODO: unescape
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
    
    # Return commit hash
    code, hash_out, _ = _run_git(["rev-parse", "HEAD"], path)
    return hash_out.strip()
