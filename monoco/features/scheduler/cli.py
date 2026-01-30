import typer
import time
from pathlib import Path
from typing import Optional
from monoco.core.output import print_output
from monoco.core.config import get_config
from monoco.features.scheduler import SessionManager, load_scheduler_config

app = typer.Typer(name="agent", help="Manage agent sessions and roles")
session_app = typer.Typer(name="session", help="Manage active agent sessions")
role_app = typer.Typer(name="role", help="Manage agent roles (CRUD)")
provider_app = typer.Typer(name="provider", help="Manage agent providers (Engines)")

app.add_typer(session_app, name="session")
app.add_typer(role_app, name="role")
app.add_typer(provider_app, name="provider")


@role_app.command(name="list")
def list_roles():
    """
    List available agent roles and their sources.
    """
    from monoco.features.scheduler.config import RoleLoader

    settings = get_config()
    project_root = Path(settings.paths.root).resolve()

    loader = RoleLoader(project_root)
    roles = loader.load_all()

    output = []
    for name, role in roles.items():
        output.append(
            {
                "role": name,
                "engine": role.engine,
                "source": loader.sources.get(name, "unknown"),
                "description": role.description,
            }
        )

    print_output(output, title="Agent Roles")


@provider_app.command(name="list")
def list_providers():
    """
    List available agent providers and their status.
    """
    from monoco.core.integrations import get_all_integrations

    settings = get_config()
    # Ideally we'd pass project-specific integrations here if they existed in config objects
    integrations = get_all_integrations(enabled_only=False)

    output = []
    for key, integration in integrations.items():
        output.append(
            {
                "key": key,
                "name": integration.name,
                "binary": integration.bin_name or "-",
                "enabled": integration.enabled,
                "rules": integration.system_prompt_file,
            }
        )

    print_output(output, title="Agent Providers")


@provider_app.command(name="check")
def check_providers():
    """
    Run health checks on available providers.
    """
    from monoco.core.integrations import get_all_integrations

    integrations = get_all_integrations(enabled_only=True)

    output = []
    for key, integration in integrations.items():
        health = integration.check_health()
        output.append(
            {
                "provider": integration.name,
                "available": "✅" if health.available else "❌",
                "latency": f"{health.latency_ms}ms" if health.latency_ms else "-",
                "error": health.error or "-",
            }
        )

    print_output(output, title="Provider Health Check")


@app.command()
def run(
    target: Optional[str] = typer.Argument(
        None, help="Issue ID (e.g. FEAT-101) or a Task Description in quotes."
    ),
    role: Optional[str] = typer.Option(
        None,
        help="Specific role to use (Planner/Builder/Reviewer). Default: intelligent selection.",
    ),
    type: str = typer.Option(
        "feature", "--type", "-t", help="Issue type for new tasks (feature/chore/fix)."
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

    If TARGET is an Issue ID, it starts a session for that issue.
    If TARGET is a description, it starts a 'Planner' session to draft a new issue.
    """
    from monoco.core.output import print_error

    # Normal run mode - target is required
    if not target:
        from monoco.core.output import print_error

        print_error("TARGET (Issue ID or Task Description) is required.")
        raise typer.Exit(code=1)
        raise typer.Exit(code=1)

    # 1. Smart Intent Recognition
    import re

    is_id = re.match(r"^[a-zA-Z]+-\d+$", target)

    if is_id:
        issue_id = target.upper()
        role_name = role or "Builder"
        description = None
    else:
        # Implicit Draft Mode via run command (target is description)
        issue_id = "NEW_TASK"
        role_name = role or "Planner"
        description = target

    # 2. Load Roles
    roles = load_scheduler_config(project_root)
    selected_role = roles.get(role_name)

    if not selected_role:
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
            print_error(
                f"Session {session.model.id} FAILED. Use 'monoco agent session autopsy {session.model.id}' for analysis."
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


@session_app.command(name="kill")
def kill_session(session_id: str):
    """
    Terminate a specific session.
    """
    manager = SessionManager()
    session = manager.get_session(session_id)
    if session:
        session.terminate()
        print_output(f"Session {session_id} terminated.")
    else:
        print_output(f"Session {session_id} not found.", style="red")


@session_app.command(name="autopsy")
def autopsy_command(target: str):
    """Execute Post-Mortem analysis on a failed session or target Issue."""
    _run_autopsy(target)


def _run_autopsy(target: str):
    """Execute Post-Mortem analysis on a failed session or target Issue."""
    from .reliability import ApoptosisManager
    from monoco.core.output import print_error

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
            settings = get_config()
            project_root = Path(settings.paths.root).resolve()
            roles = load_scheduler_config(project_root)
            builder_role = roles.get("Builder")

            if not builder_role:
                print_error("Builder role not found.")
                raise typer.Exit(code=1)

            session = manager.create_session(target.upper(), builder_role)
            session.model.status = "failed"
        else:
            print_error(f"Could not find session or valid Issue ID for '{target}'")
            raise typer.Exit(code=1)

    apoptosis = ApoptosisManager(manager)
    apoptosis.trigger_apoptosis(session.model.id)


def _run_draft(desc: str, type: str, detach: bool):
    """Draft a new issue based on a natural language description."""
    from monoco.core.output import print_error

    settings = get_config()
    project_root = Path(settings.paths.root).resolve()

    # Load Roles
    roles = load_scheduler_config(project_root)
    # Use 'Planner' as the role for drafting (it handles new tasks)
    role_name = "Planner"
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


@session_app.command(name="list")
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


@session_app.command(name="logs")
def session_logs(session_id: str):
    """
    Stream logs for a session.
    """
    print_output(f"Streaming logs for {session_id}...", title="Session Logs")
    # Placeholder
    print("[12:00:00] Session started")
    print("[12:00:01] Worker initialized")
