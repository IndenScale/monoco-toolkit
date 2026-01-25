import typer
import time
from pathlib import Path
from typing import Optional
from monoco.core.output import print_output
from monoco.core.config import get_config
from monoco.features.scheduler import SessionManager, load_scheduler_config

app = typer.Typer(name="agent", help="Manage agent sessions")


@app.command()
def draft(
    desc: str = typer.Option(..., "--desc", "-d", help="Description of the task"),
    type: str = typer.Option(
        "feature", "--type", "-t", help="Issue type (feature/chore/fix)"
    ),
):
    """
    Draft a new issue based on a natural language description.
    This creates a temporary 'drafter' agent session.
    """
    from monoco.core.output import print_error

    settings = get_config()
    project_root = Path(settings.paths.root).resolve()

    # Load Roles
    roles = load_scheduler_config(project_root)
    # Use 'crafter' as the role for drafting (it handles new tasks)
    role_name = "crafter"
    selected_role = roles.get(role_name)

    if not selected_role:
        print_error(f"Role '{role_name}' not found.")
        raise typer.Exit(code=1)

    print_output(
        f"Drafting {type} from description: '{desc}'",
        title="Agent Drafter",
    )

    manager = SessionManager()
    # We use a placeholder ID as we don't know the ID yet.
    # The agent is expected to create the file, so the ID will be generated then.
    session = manager.create_session("NEW_TASK", selected_role)

    context = {"description": desc, "type": type}

    try:
        session.start(context=context)

        # Monitoring Loop
        while session.refresh_status() == "running":
            time.sleep(1)

        if session.model.status == "failed":
            print_error("Drafting failed.")
        else:
            print_output("Drafting completed.", title="Agent Drafter")

    except KeyboardInterrupt:
        print("\nStopping...")
        session.terminate()
        print_output("Drafting cancelled.")


@app.command()
def run(
    target: str = typer.Argument(
        ..., help="Issue ID (e.g. FEAT-101) or a Task Description in quotes."
    ),
    role: Optional[str] = typer.Option(
        None,
        help="Specific role to use (crafter/builder/auditor). Default: intelligent selection.",
    ),
    detach: bool = typer.Option(
        False, "--detach", "-d", help="Run in background (Daemon)"
    ),
    fail: bool = typer.Option(
        False, "--fail", help="Simulate a crash for testing Apoptosis."
    ),
):
    """
    Start an agent session.
    - If TARGET is an Issue ID: Work on that issue.
    - If TARGET is a text description: Create a new issue (Crafter).
    """
    settings = get_config()
    project_root = Path(settings.paths.root).resolve()

    # 1. Smart Intent Recognition
    import re

    is_id = re.match(r"^[a-zA-Z]+-\d+$", target)

    if is_id:
        issue_id = target.upper()
        role_name = role or "builder"
        description = None
    else:
        # Implicit Draft Mode via run command
        issue_id = "NEW_TASK"
        role_name = role or "crafter"
        description = target

    # 2. Load Roles
    roles = load_scheduler_config(project_root)
    selected_role = roles.get(role_name)

    if not selected_role:
        from monoco.core.output import print_error

        print_error(f"Role '{role_name}' not found. Available: {list(roles.keys())}")
        raise typer.Exit(code=1)

    print_output(
        f"Starting Agent Session for '{target}' as {role_name}...",
        title="Agent Scheduler",
    )

    # 3. Initialize Session
    manager = SessionManager()
    session = manager.create_session(issue_id, selected_role)

    if detach:
        print_output(
            "Background mode not fully implemented yet. Running in foreground."
        )

    try:
        # Pass description if it's a new task
        context = {"description": description} if description else None

        if fail:
            from monoco.core.output import rprint

            rprint("[bold yellow]DEBUG: Simulating immediate crash...[/bold yellow]")
            session.model.status = "failed"
        else:
            session.start(context=context)

        # Monitoring Loop
        while session.refresh_status() == "running":
            time.sleep(1)

        if session.model.status == "failed":
            from monoco.core.output import print_error

            print_error(
                f"Session {session.model.id} FAILED. Use 'monoco agent autopsy {session.model.id}' for analysis."
            )
        else:
            print_output(
                f"Session finished with status: {session.model.status}",
                title="Agent Scheduler",
            )

    except KeyboardInterrupt:
        print("\nStopping...")
        session.terminate()
        print_output("Session terminated.")


@app.command()
def kill(session_id: str):
    """
    Terminate a session.
    """
    manager = SessionManager()
    session = manager.get_session(session_id)
    if session:
        session.terminate()
        print_output(f"Session {session_id} terminated.")
    else:
        print_output(f"Session {session_id} not found.", style="red")


@app.command()
def autopsy(
    target: str = typer.Argument(..., help="Session ID or Issue ID to analyze."),
):
    """
    Execute Post-Mortem analysis on a failed session or target Issue.
    """
    from .reliability import ApoptosisManager

    manager = SessionManager()

    print_output(f"Initiating Autopsy for '{target}'...", title="Coroner")

    # Try to find session
    session = manager.get_session(target)
    if not session:
        # Fallback: Treat target as Issue ID and create a dummy failed session context
        import re

        if re.match(r"^[a-zA-Z]+-\d+$", target):
            print_output(f"Session not in memory. Analyzing Issue {target} directly.")
            # We create a transient session just to trigger the coroner
            from .defaults import DEFAULT_ROLES

            builder_role = next(r for r in DEFAULT_ROLES if r.name == "builder")
            session = manager.create_session(target.upper(), builder_role)
            session.model.status = "failed"
        else:
            print_output(
                f"Could not find session or valid Issue ID for '{target}'", style="red"
            )
            raise typer.Exit(code=1)

    apoptosis = ApoptosisManager(manager)
    apoptosis.trigger_apoptosis(session.model.id)


@app.command(name="list")
def list_sessions():
    """
    List active agent sessions.
    """
    manager = SessionManager()
    sessions = manager.list_sessions()

    output = []
    for s in sessions:
        output.append(
            {
                "id": s.model.id,
                "issue": s.model.issue_id,
                "role": s.model.role_name,
                "status": s.model.status,
                "branch": s.model.branch_name,
            }
        )

    print_output(
        output
        or "No active sessions found (Note: Persistence not implemented in CLI list yet).",
        title="Active Sessions",
    )


@app.command()
def logs(session_id: str):
    """
    Stream logs for a session.
    """
    print_output(f"Streaming logs for {session_id}...", title="Session Logs")
    # Placeholder
    print("[12:00:00] Session started")
    print("[12:00:01] Worker initialized")
