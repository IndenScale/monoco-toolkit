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
        # Perform health check
        health = integration.check_health()
        status_icon = "✅" if health.available else "❌"
        
        output.append(
            {
                "key": key,
                "name": integration.name,
                "status": status_icon,
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
    prompt: Optional[list[str]] = typer.Argument(None, help="Instructions for the agent (e.g. 'Fix the bug')."),
    issue: Optional[str] = typer.Option(
        None, "--issue", "-i", help="Link to a specific Issue ID (e.g. FEAT-101)."
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

    Usage:
      monoco agent run "Check memos"
      monoco agent run -i FEAT-101 "Implement feature"
    """
    settings = get_config()
    project_root = Path(settings.paths.root).resolve()
    
    # 1. Resolve Inputs
    full_prompt = " ".join(prompt) if prompt else ""
    
    if issue:
        # User explicitly linked an issue
        issue_id = issue.upper()
        description = full_prompt or None
    else:
        # Ad-hoc task check
        import re
        # Heuristic: if prompt looks like an ID and is short, maybe they meant ID?
        # But explicit is better. Let's assume everything in prompt is instructions.
        issue_id = "NEW_TASK"
        description = full_prompt

    if not description and not issue:
        print_error("Please provide either a PROMPT or an --issue ID.")
        raise typer.Exit(code=1)

    # 2. Load Roles
    roles = load_scheduler_config(project_root)
    selected_role = roles.get(role)

    if not selected_role:
        print_error(f"Role '{role}' not found. Available: {list(roles.keys())}")
        raise typer.Exit(code=1)

    # 3. Provider Override & Fallback Logic
    target_engine = provider or selected_role.engine
    from monoco.core.integrations import get_integration, get_all_integrations
    
    integration = get_integration(target_engine)
    
    # If integration is found, check health
    is_available = False
    if integration:
        health = integration.check_health()
        is_available = health.available
        if not is_available and provider:
            # If user explicitly requested this provider, fail hard
            print_error(f"Requested provider '{target_engine}' is not available.")
            print_error(f"Error: {health.error}")
            raise typer.Exit(code=1)
            
    # Auto-fallback if default provider is unavailable
    if not is_available:
        print_output(f"⚠️  Provider '{target_engine}' is not available. Searching for fallback...", style="yellow")
        
        all_integrations = get_all_integrations(enabled_only=True)
        fallback_found = None
        
        # Priority list for fallback
        priority = ["cursor", "claude", "gemini", "qwen", "kimi"]
        
        # Try priority matches first
        for key in priority:
            if key in all_integrations:
                if all_integrations[key].check_health().available:
                    fallback_found = key
                    break
        
        # Determine strict fallback
        if fallback_found:
             print_output(f"🔄 Falling back to available provider: [bold green]{fallback_found}[/bold green]")
             selected_role.engine = fallback_found
        else:
             # If NO CLI tools available, maybe generic agent?
             if "agent" in all_integrations:
                 print_output("🔄 Falling back to Generic Agent (No CLI execution).", style="yellow")
                 selected_role.engine = "agent"
             else:
                 print_error("❌ No available agent providers found on this system.")
                 print_error("Please install Cursor, Claude Code, or Gemini CLI.")
                 raise typer.Exit(code=1)
    elif provider:
        # If available and user overrode it
        print_output(f"Overriding provider: {selected_role.engine} -> {provider}")
        selected_role.engine = provider

    display_target = issue if issue else (full_prompt[:50] + "..." if len(full_prompt) > 50 else full_prompt)
    print_output(
        f"Starting Agent Session for '{display_target}' as {role} (via {selected_role.engine})...",
        title="Agent Framework",
    )

    # 4. Initialize Session
    manager = SessionManager()
    session = manager.create_session(issue_id, selected_role)


    try:
        # Pass description if it's a new task
        context = {"description": description} if description else None
        session.start(context=context)

        if detach:
            print_output(
                 f"Session {session.model.id} started in background (detached)."
            )
            return

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
