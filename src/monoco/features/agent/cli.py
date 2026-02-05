import typer
import time
import asyncio
from pathlib import Path
from typing import Optional
from monoco.core.output import print_output, print_error
from monoco.core.config import get_config
from monoco.features.agent import load_scheduler_config
from monoco.core.scheduler import AgentTask, LocalProcessScheduler

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

    integrations = get_all_integrations(enabled_only=False)

    output = []
    for key, integration in integrations.items():
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
        issue_id = issue.upper()
        description = full_prompt or None
    else:
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
    
    is_available = False
    if integration:
        health = integration.check_health()
        is_available = health.available
        if not is_available and provider:
            print_error(f"Requested provider '{target_engine}' is not available.")
            print_error(f"Error: {health.error}")
            raise typer.Exit(code=1)
            
    # Auto-fallback if default provider is unavailable
    if not is_available:
        print_output(f"⚠️  Provider '{target_engine}' is not available. Searching for fallback...", style="yellow")
        
        all_integrations = get_all_integrations(enabled_only=True)
        fallback_found = None
        priority = ["cursor", "claude", "gemini", "qwen", "kimi"]
        
        for key in priority:
            if key in all_integrations:
                if all_integrations[key].check_health().available:
                    fallback_found = key
                    break
        
        if fallback_found:
             print_output(f"🔄 Falling back to available provider: [bold green]{fallback_found}[/bold green]")
             selected_role.engine = fallback_found
        else:
             if "agent" in all_integrations:
                 print_output("🔄 Falling back to Generic Agent (No CLI execution).", style="yellow")
                 selected_role.engine = "agent"
             else:
                 print_error("❌ No available agent providers found on this system.")
                 print_error("Please install Cursor, Claude Code, or Gemini CLI.")
                 raise typer.Exit(code=1)
    elif provider:
        print_output(f"Overriding provider: {selected_role.engine} -> {provider}")
        selected_role.engine = provider

    display_target = issue if issue else (full_prompt[:50] + "..." if len(full_prompt) > 50 else full_prompt)
    print_output(
        f"Starting Agent Session for '{display_target}' as {role} (via {selected_role.engine})...",
        title="Agent Framework",
    )

    # 4. Initialize AgentScheduler and schedule task
    scheduler = LocalProcessScheduler(
        max_concurrent=5,
        project_root=project_root,
    )

    task = AgentTask(
        task_id=f"cli-{issue_id}-{int(time.time())}",
        role_name=selected_role.name,
        issue_id=issue_id,
        prompt=description or "Execute task",
        engine=selected_role.engine,
        timeout=selected_role.timeout or 900,
        metadata={
            "role_description": selected_role.description,
            "role_goal": selected_role.goal,
        },
    )

    try:
        # Run async scheduler in sync context
        asyncio.run(scheduler.start())
        session_id = asyncio.run(scheduler.schedule(task))
        
        print_output(f"Session {session_id} started.")

        if detach:
            print_output(
                 f"Session {session_id} running in background (detached)."
            )
            return

        # Monitoring Loop - poll for task status
        while True:
            status = scheduler.get_task_status(session_id)
            if status in ["completed", "failed", "crashed"]:
                break
            time.sleep(1)

        final_status = scheduler.get_task_status(session_id)
        if final_status == "failed":
            print_error(
                f"Session {session_id} FAILED. Review logs for details."
            )
        else:
            print_output(
                f"Session finished with status: {final_status}",
                title="Agent Framework",
            )

    except KeyboardInterrupt:
        print("\nStopping...")
        asyncio.run(scheduler.cancel_task(session_id))
        print_output("Session terminated.")
    finally:
        asyncio.run(scheduler.stop())


@session_app.command(name="kill")
def kill_session(session_id: str):
    """
    Terminate a specific session.
    
    Note: Uses AgentScheduler to cancel the task.
    """
    settings = get_config()
    project_root = Path(settings.paths.root).resolve()
    
    scheduler = LocalProcessScheduler(
        max_concurrent=5,
        project_root=project_root,
    )
    
    try:
        asyncio.run(scheduler.start())
        asyncio.run(scheduler.cancel_task(session_id))
        print_output(f"Session {session_id} terminated.")
    except Exception as e:
        print_error(f"Failed to terminate session: {e}")
    finally:
        asyncio.run(scheduler.stop())


@session_app.command(name="list")
def list_sessions():
    """
    List active agent sessions.
    
    Note: Shows tasks from AgentScheduler.
    """
    settings = get_config()
    project_root = Path(settings.paths.root).resolve()
    
    scheduler = LocalProcessScheduler(
        max_concurrent=5,
        project_root=project_root,
    )
    
    try:
        asyncio.run(scheduler.start())
        stats = scheduler.get_stats()
        
        output = {
            "scheduler_status": "running" if stats.get("running") else "stopped",
            "active_tasks": stats.get("active_tasks", 0),
            "completed_tasks": stats.get("completed_tasks", 0),
            "failed_tasks": stats.get("failed_tasks", 0),
        }

        print_output(output, title="Agent Scheduler Status")
    finally:
        asyncio.run(scheduler.stop())


@session_app.command(name="logs")
def session_logs(session_id: str):
    """
    Stream logs for a session.
    
    Note: Logs are stored in .monoco/sessions/{session_id}.log
    """
    settings = get_config()
    project_root = Path(settings.paths.root).resolve()
    log_path = project_root / ".monoco" / "sessions" / f"{session_id}.log"
    
    print_output(f"Streaming logs for {session_id}...", title="Session Logs")
    
    if log_path.exists():
        print(log_path.read_text())
    else:
        print(f"[12:00:00] Session {session_id} started")
        print("[12:00:01] Worker initialized")
        print("(Log file not found - showing placeholder)")
