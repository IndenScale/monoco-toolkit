import typer
import time
from typing import Optional
from monoco.core.output import print_output
from monoco.core.config import get_config
from monoco.features.scheduler import SessionManager, load_scheduler_config

app = typer.Typer(name="agent", help="Manage agent sessions")


@app.command()
def run(
    issue_id: str = typer.Argument(..., help="The Issue ID to work on"),
    role: Optional[str] = typer.Option(
        None, help="Specific role to use (crafter/builder/auditor)"
    ),
    detach: bool = typer.Option(
        False, "--detach", "-d", help="Run in background (Daemon)"
    ),
):
    """
    Start an agent session for a given Issue.
    """
    settings = get_config()
    project_root = settings.project_root_path

    # Load Roles
    roles = load_scheduler_config(project_root)

    # Determine Role
    # TODO: Intelligence to pick role based on issue state or tags?
    # For now, default to 'crafter' if not specified
    role_name = role or "crafter"
    selected_role = roles.get(role_name)

    if not selected_role:
        print_output(
            {"error": f"Role '{role_name}' not found. Available: {list(roles.keys())}"},
            style="red",
        )
        raise typer.Exit(code=1)

    print_output(
        f"Starting Agent Session for {issue_id} as {role_name}...",
        title="Agent Scheduler",
    )

    # Initialize Session
    manager = SessionManager()
    session = manager.create_session(issue_id, selected_role)

    if detach:
        print_output(
            "Background mode not fully implemented yet. Running in foreground."
        )
        # In future: send command to daemon

    try:
        session.start()

        # Simulation Loop
        # In a real implementation, this would connect to the LLM backend
        print("Agent is thinking...")
        time.sleep(1)
        print("Agent is exploring context...")
        time.sleep(1)
        print(f"Agent running default tools: {selected_role.tools}")

        # Keep alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
        session.terminate()
        print_output("Session terminated.")


@app.command(name="list")
def list_sessions():
    """
    List active agent sessions.
    """
    # NOTE: In a real implementation, this needs to query the Daemon or a persistent Store.
    # Since SessionManager is currently in-memory only per process, this will report empty
    # if run from a separate process.
    # For MVP demonstration, we just show the concept.

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


@app.command()
def kill(session_id: str):
    """
    Terminate a session.
    """
    print_output(f"Killing session {session_id}...", title="Kill Session")
    # Placeholder
    print("Signal sent.")
