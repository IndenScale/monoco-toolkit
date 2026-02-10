"""
Ralph Loop Core - Agent Session Relay Implementation.

When the current Agent hits a bottleneck, launch a successor Agent to continue.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from monoco.core.config import get_config, find_monoco_root
from .models import LastWords, RalphRelay, RelayStatus


def get_ralph_dir(project_root: Optional[Path] = None) -> Path:
    """Get the Ralph Loop working directory."""
    if project_root is None:
        project_root = find_monoco_root()
    ralph_dir = project_root / ".monoco" / "ralph"
    ralph_dir.mkdir(parents=True, exist_ok=True)
    return ralph_dir


def prepare_last_words(
    issue_id: str,
    completed_work: str,
    current_state: str,
    next_steps: str,
    obstacles: Optional[str] = None,
) -> Path:
    """
    Generate Last Words document for the successor Agent.

    Args:
        issue_id: The Issue ID being relayed
        completed_work: Summary of completed work and verified results
        current_state: Current code/file state
        next_steps: Suggested next steps
        obstacles: Optional obstacles or uncertainties encountered

    Returns:
        Path to the generated Last Words file
    """
    last_words = LastWords(
        completed_work=completed_work,
        current_state=current_state,
        obstacles=obstacles,
        next_steps=next_steps,
    )

    ralph_dir = get_ralph_dir()
    last_words_path = ralph_dir / f"{issue_id}-last-words.md"
    last_words_path.write_text(last_words.to_markdown(), encoding="utf-8")

    return last_words_path


def prepare_last_words_from_prompt(issue_id: str, prompt: str) -> Path:
    """
    Generate Last Words from a simple prompt string.

    This is used when the Agent provides a concise summary directly.
    """
    last_words = LastWords.from_prompt(prompt)
    ralph_dir = get_ralph_dir()
    last_words_path = ralph_dir / f"{issue_id}-last-words.md"
    last_words_path.write_text(last_words.to_markdown(), encoding="utf-8")
    return last_words_path


def read_last_words_from_file(path: Path) -> str:
    """Read Last Words content from a file."""
    if not path.exists():
        raise FileNotFoundError(f"Last words file not found: {path}")
    return path.read_text(encoding="utf-8")


def get_agents_md_content(project_root: Optional[Path] = None) -> str:
    """
    Load the appropriate AGENTS.md content based on project language.

    Returns:
        The content of zh/AGENTS.md or en/AGENTS.md
    """
    if project_root is None:
        project_root = find_monoco_root()

    config = get_config()
    source_lang = config.i18n.source_lang if config.i18n else "zh"

    # Determine which AGENTS.md to load
    ralph_resources = Path(__file__).parent / "resources"
    if source_lang == "zh":
        agents_path = ralph_resources / "zh" / "AGENTS.md"
    else:
        agents_path = ralph_resources / "en" / "AGENTS.md"

    # Fallback to zh if preferred language not found
    if not agents_path.exists():
        agents_path = ralph_resources / "zh" / "AGENTS.md"

    if agents_path.exists():
        return agents_path.read_text(encoding="utf-8")

    # Return default content if file not found
    return _get_default_agents_md()


def _get_default_agents_md() -> str:
    """Return default AGENTS.md content if file not found."""
    return """## Ralph Loop

When the current Agent hits a bottleneck, launch a successor Agent to continue the Issue.

### Last Words

Read the Last Words file first to understand:
- What has been completed
- Current state of the codebase
- Obstacles encountered
- Suggested next steps

### Commands

- `monoco ralph --issue {issue-id} --prompt "{last-words}"` - Direct relay
- `monoco ralph --issue {issue-id} --path {file}` - Relay from file
- `monoco ralph --issue {issue-id}` - Auto-generate summary
"""


def build_relay_prompt(
    issue_id: str,
    last_words_content: str,
    issue_content: Optional[str] = None,
) -> str:
    """
    Build the complete prompt for the successor Agent.

    This combines:
    1. AGENTS.md content (Ralph Loop guidelines)
    2. Issue context
    3. Last Words from previous Agent
    """
    parts = []

    # 1. AGENTS.md content
    agents_md = get_agents_md_content()
    parts.append("# Ralph Loop - Agent Guidelines")
    parts.append(agents_md)
    parts.append("")

    # 2. Issue context
    if issue_content:
        parts.append("# Issue Context")
        parts.append(issue_content)
        parts.append("")

    # 3. Last Words
    parts.append("# Last Words (from previous Agent)")
    parts.append(last_words_content)
    parts.append("")

    # 4. Action instruction
    parts.append("# Your Mission")
    parts.append(f"Continue working on Issue {issue_id}.")
    parts.append("Review the Last Words above, verify the current state, and proceed with the suggested next steps.")
    parts.append("")

    return "\n".join(parts)


def spawn_successor_agent(
    issue_id: str,
    last_words_path: Path,
    issue_path: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[int]:
    """
    Spawn a successor Agent to continue the Issue.

    CRITICAL: The spawned agent MUST be completely independent from the parent
    process. When the current Agent ends, the successor must continue running.

    Implementation uses:
    - nohup: Ignore HUP signal when parent terminates
    - setsid: Create new session (detach from controlling terminal)
    - stdout/stderr redirected to file: Avoid broken pipe

    Args:
        issue_id: The Issue ID to continue
        last_words_path: Path to the Last Words file
        issue_path: Optional path to the Issue file
        dry_run: If True, only print what would be done

    Returns:
        Process ID of the spawned agent, or None if dry_run
    """
    # Load issue content if available
    issue_content = None
    if issue_path and issue_path.exists():
        issue_content = issue_path.read_text(encoding="utf-8")

    # Read Last Words
    last_words_content = last_words_path.read_text(encoding="utf-8")

    # Build the complete relay prompt
    relay_prompt = build_relay_prompt(issue_id, last_words_content, issue_content)

    # Create a temporary file for the prompt
    ralph_dir = get_ralph_dir()
    prompt_file = ralph_dir / f"{issue_id}-prompt.txt"
    prompt_file.write_text(relay_prompt, encoding="utf-8")

    if dry_run:
        print(f"[DRY RUN] Would spawn successor agent for {issue_id}")
        print(f"[DRY RUN] Prompt file: {prompt_file}")
        return None

    # Detect which agent CLI is available
    # Priority: claude > claude-code > aider > generic
    agent_cli = _detect_agent_cli()

    if agent_cli == "claude" or agent_cli == "claude-code":
        return _spawn_claude_agent_detached(issue_id, prompt_file, ralph_dir)
    elif agent_cli == "aider":
        return _spawn_aider_agent_detached(issue_id, prompt_file, ralph_dir)
    else:
        # Fallback: print instructions
        print(f"\n{'='*60}")
        print(f"Ralph Loop: Issue {issue_id} ready for handoff")
        print(f"{'='*60}")
        print(f"Prompt file: {prompt_file}")
        print(f"\nTo continue, open a NEW terminal and run:")
        print(f"  claude --allow-dangerously-skip-permissions -p \"$(cat {prompt_file})\"")
        print(f"{'='*60}\n")
        return None


def _detect_agent_cli() -> str:
    """Detect which agent CLI is available."""
    # Check for claude (Claude Code)
    result = subprocess.run(
        ["which", "claude"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "claude"

    # Check for claude-code
    result = subprocess.run(
        ["which", "claude-code"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "claude-code"

    # Check for aider
    result = subprocess.run(
        ["which", "aider"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "aider"

    return "none"


def _spawn_claude_agent_detached(
    issue_id: str,
    prompt_file: Path,
    ralph_dir: Path,
) -> Optional[int]:
    """
    Spawn a completely detached Claude Code agent.

    Uses nohup + setsid to ensure the process survives parent termination.
    """
    log_file = ralph_dir / f"{issue_id}-agent.log"
    launch_script = ralph_dir / f"{issue_id}-launch.sh"

    # Create launch script that properly detaches
    script_content = f"""#!/bin/bash
# Ralph Loop Launch Script for {issue_id}
# Generated: {datetime.now().isoformat()}

cd "{Path.cwd()}" || exit 1

# Ensure we're in a new session and ignore HUP
trap '' HUP

# Launch agent with full detachment (no exec, so we can get PID)
nohup claude --allow-dangerously-skip-permissions -p "$(cat {prompt_file})" >> {log_file} 2>&1 &
PID=$!

# Print PID for tracking
echo $PID > {ralph_dir / f"{issue_id}-agent.pid"}
echo "[Ralph Loop] Successor agent started with PID: $PID"
echo "[Ralph Loop] Log file: {log_file}"

# Disown to ensure it survives this script's termination
disown
"""
    launch_script.write_text(script_content, encoding="utf-8")
    launch_script.chmod(0o755)

    # Execute the script with full detachment
    # Using a subshell that immediately disowns
    subprocess.Popen(
        ["bash", "-c", f"(nohup {launch_script} > /dev/null 2>&1 &)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env={**os.environ, "MONOCO_RALPH_RELAY": issue_id},
    )

    # Read the PID file (may take a moment to be written)
    import time
    pid_file = ralph_dir / f"{issue_id}-agent.pid"
    for _ in range(10):  # Wait up to 1 second
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                return pid
            except (ValueError, FileNotFoundError):
                pass
        time.sleep(0.1)

    return None


def _spawn_aider_agent_detached(
    issue_id: str,
    prompt_file: Path,
    ralph_dir: Path,
) -> Optional[int]:
    """
    Spawn a completely detached Aider agent.
    """
    log_file = ralph_dir / f"{issue_id}-agent.log"

    # Use nohup and full detachment
    process = subprocess.Popen(
        [
            "nohup",
            "aider",
            "--message-file", str(prompt_file),
        ],
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        cwd=Path.cwd(),
    )

    return process.pid


def relay_issue(
    issue_id: str,
    prompt: Optional[str] = None,
    prompt_path: Optional[Path] = None,
    auto_generate: bool = False,
    dry_run: bool = False,
) -> RalphRelay:
    """
    Execute the full Ralph Loop relay process.

    Args:
        issue_id: The Issue ID to relay
        prompt: Direct prompt string for Last Words
        prompt_path: Path to a file containing Last Words
        auto_generate: If True, auto-generate summary (requires implementation)
        dry_run: If True, only show what would be done

    Returns:
        RalphRelay record of the relay
    """
    project_root = find_monoco_root()

    # Validate issue exists
    try:
        issue_path = _find_issue_file(project_root, issue_id)
    except FileNotFoundError:
        raise ValueError(f"Issue not found: {issue_id}")

    # Prepare Last Words
    if prompt:
        last_words_path = prepare_last_words_from_prompt(issue_id, prompt)
    elif prompt_path:
        content = read_last_words_from_file(prompt_path)
        last_words_path = prepare_last_words_from_prompt(issue_id, content)
    elif auto_generate:
        # Auto-generate summary from current context
        # This would require access to session history
        auto_summary = _auto_generate_summary(issue_id)
        last_words_path = prepare_last_words_from_prompt(issue_id, auto_summary)
    else:
        raise ValueError("Must provide --prompt, --path, or use auto-generate")

    # Create relay record
    relay = RalphRelay(
        issue_id=issue_id,
        last_words_path=last_words_path,
        status="pending",
    )

    # Save relay record
    ralph_dir = get_ralph_dir()
    relay_file = ralph_dir / f"{issue_id}-relay.json"
    relay_file.write_text(relay.model_dump_json(indent=2), encoding="utf-8")

    if not dry_run:
        # Spawn successor agent
        pid = spawn_successor_agent(issue_id, last_words_path, issue_path)
        if pid:
            relay.successor_pid = pid
            relay.status = "active"
            relay.started_at = datetime.now()
            relay_file.write_text(relay.model_dump_json(indent=2), encoding="utf-8")

    return relay


def _find_issue_file(project_root: Path, issue_id: str) -> Path:
    """Find the Issue file by ID."""
    from monoco.features.issue.core import find_issue_path

    issues_dir = project_root / "Issues"
    issue_path = find_issue_path(issues_dir, issue_id)

    if issue_path is None:
        raise FileNotFoundError(f"Issue {issue_id} not found in {issues_dir}")

    return issue_path


def _auto_generate_summary(issue_id: str) -> str:
    """
    Auto-generate a summary from current context.

    In a full implementation, this would:
    1. Analyze recent git changes
    2. Check modified files
    3. Summarize the current state

    For now, return a placeholder.
    """
    return f"Auto-generated summary for {issue_id}. Please review the current state and continue."


def get_relay_status(issue_id: str) -> Optional[RalphRelay]:
    """Get the relay status for an Issue."""
    ralph_dir = get_ralph_dir()
    relay_file = ralph_dir / f"{issue_id}-relay.json"

    if not relay_file.exists():
        return None

    import json
    data = json.loads(relay_file.read_text(encoding="utf-8"))
    return RalphRelay(**data)


def clear_relay_status(issue_id: str) -> bool:
    """Clear the relay status for an Issue."""
    ralph_dir = get_ralph_dir()
    relay_file = ralph_dir / f"{issue_id}-relay.json"
    last_words_file = ralph_dir / f"{issue_id}-last-words.md"
    prompt_file = ralph_dir / f"{issue_id}-prompt.txt"

    deleted = False
    for f in [relay_file, last_words_file, prompt_file]:
        if f.exists():
            f.unlink()
            deleted = True

    return deleted

