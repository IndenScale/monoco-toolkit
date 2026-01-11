import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict

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
    # git add accepts multiple files, but if list is too long, it might fail on command line limit.
    # For now, simplistic.
    # If "." in files, careful.
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

def search_commits_by_message(path: Path, grep_pattern: str) -> List[Dict[str, str]]:
    """
    Search commits where message matches grep_pattern.
    Returns list of {hash, subject, files: []}
    """
    # Format: %H|%s (Hash|Subject)
    # --name-only lists files after metadata
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
                "files": []
            }
        elif line.strip():
            if current_commit:
                current_commit["files"].append(line.strip())
                
    if current_commit:
        commits.append(current_commit)
        
    return commits

def get_commit_stats(path: Path, commit_hash: str) -> Dict[str, int]:
    """Get simple stats for a commit"""
    cmd = ["show", "--shortstat", "--format=", commit_hash]
    code, stdout, _ = _run_git(cmd, path)
    # Output: " 1 file changed, 2 insertions(+), 1 deletion(-)"
    # Parse simplisticly
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