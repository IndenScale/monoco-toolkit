import typer
import time
from pathlib import Path
from typing import Optional
from monoco.core.output import print_output, print_error
from monoco.core.config import get_config
from monoco.features.agent import SessionManager, load_scheduler_config

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
    from monoco.features.agent.config import RoleLoader

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
    target: str = typer.Argument(
        ..., help="Issue ID (e.g. FEAT-101) or a Task Description in quotes."
    ),
    role: str = typer.Option(
        "Default", "--role", "-r", help="Specific role to use."
    ),
    detach: bool = typer.Option(
        False, "--detach", "-d", help="Run in background (Daemon)"
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Override the default engine/provider for this session."
    ),
):
    """
    Start an agent session.

    Logic is completely role-agnostic.
    - Loads the specified ROLE configuration.
    - Starts a session for TARGET.
    """
    settings = get_config()
    project_root = Path(settings.paths.root).resolve()

    # 1. Identify Target
    import re
    is_id = re.match(r"^[a-zA-Z]+-\d+$", target)
    
    if is_id:
        issue_id = target.upper()
        description = None
    else:
        # Treat as description for a new task
        issue_id = "NEW_TASK"
        description = target

    # 2. Load Roles
    roles = load_scheduler_config(project_root)
    selected_role = roles.get(role)

    if not selected_role:
        print_error(f"Role '{role}' not found. Available: {list(roles.keys())}")
        raise typer.Exit(code=1)

    # Override engine if provider is specified
    if provider:
        # We modify the instance in memory for this session only
        print_output(f"Overriding provider: {selected_role.engine} -> {provider}")
        selected_role.engine = provider

    print_output(
        f"Starting Agent Session for '{target}' as {role} (via {selected_role.engine})...",
        title="Agent Framework",
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
        session.start(context=context)

        # Monitoring Loop
        while session.refresh_status() == "running":
            time.sleep(1)

        if session.model.status == "failed":
            print_error(
                f"Session {session.model.id} FAILED. Review logs for details."
            )
        else:
            print_output(
                f"Session finished with status: {session.model.status}",
                title="Agent Framework",
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
