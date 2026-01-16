
import typer
from typing import Optional, Annotated
from pathlib import Path
from monoco.core.output import print_output, print_error, AgentOutput, OutputManager
from monoco.core.agent.adapters import get_agent_client
from monoco.core.agent.state import AgentStateManager
from monoco.core.agent.action import ActionRegistry, ActionContext
from monoco.core.config import get_config
import asyncio
import re
import json as j

app = typer.Typer()

@app.command(name="run")
def run_command(
    prompt_or_task: str = typer.Argument(..., help="Prompt string OR execution task name (e.g. 'refine-issue')"),
    target: Optional[str] = typer.Argument(None, help="Target file argument for the task"),
    provider: Optional[str] = typer.Option(None, "--using", "-u", help="Override agent provider"),
    instruction: Optional[str] = typer.Option(None, "--instruction", "-i", help="Additional instruction for the agent"),
    json: AgentOutput = False,
):
    """
    Execute a prompt or a named task using an Agent CLI.
    """
    # 0. Setup
    settings = get_config()
    state_manager = AgentStateManager()
    registry = ActionRegistry(Path(settings.paths.root))
    
    # 1. Check if it's a named task
    action = registry.get(prompt_or_task)
    
    final_prompt = prompt_or_task
    context_files = []
    
    # Determine Provider Priority: CLI > Action Def > Config > Default
    prov_name = provider 
    
    if action:
        # It IS an action
        if not OutputManager.is_agent_mode():
            print(f"Running action: {action.name}")
        
        # Simple template substitution
        final_prompt = action.template
        
        if "{{file}}" in final_prompt:
             if not target:
                 print_error("This task requires a target file argument.")
                 raise typer.Exit(1)
             
             target_path = Path(target).resolve()
             if not target_path.exists():
                 print_error(f"Target file not found: {target}")
                 raise typer.Exit(1)
                 
             final_prompt = final_prompt.replace("{{file}}", target_path.read_text())
             # Also add to context files? Ideally the prompt has it.
             # Let's add it to context files list to be safe if prompt didn't embed it fully
             context_files.append(target_path)
             
        if not prov_name:
            prov_name = action.provider

    # 2. Append Instruction if provided
    if instruction:
        final_prompt = f"{final_prompt}\n\n[USER INSTRUCTION]\n{instruction}"

    # 2. Provider Resolution Fallback
    prov_name = prov_name or settings.agent.framework or "gemini"

    # 3. State Check
    state = state_manager.load()
    if not state or state.is_stale:
        if not OutputManager.is_agent_mode():
            print("Agent state stale or missing, refreshing...")
        state = state_manager.refresh()
    
    if prov_name not in state.providers:
         print_error(f"Provider '{prov_name}' unknown.")
         raise typer.Exit(1)
         
    if not state.providers[prov_name].available:
         print_error(f"Provider '{prov_name}' is not available. Run 'monoco doctor' to diagnose.")
         raise typer.Exit(1)

    # 4. Execute
    try:
        client = get_agent_client(prov_name)
        result = asyncio.run(client.execute(final_prompt, context_files=context_files))
        
        if OutputManager.is_agent_mode():
            OutputManager.print({"result": result, "provider": prov_name})
        else:
            print(result)
        
    except Exception as e:
        print_error(f"Execution failed: {e}")
        raise typer.Exit(1)

@app.command()
def list(
    json: AgentOutput = False,
    context: Optional[str] = typer.Option(None, "--context", help="Context for filtering (JSON string)")
):
    """List available actions."""
    settings = get_config()
    registry = ActionRegistry(Path(settings.paths.root))
    
    action_context = None
    if context:
        try:
            ctx_data = j.loads(context)
            action_context = ActionContext(**ctx_data)
        except Exception as e:
            print_error(f"Invalid context JSON: {e}")

    actions = registry.list_available(action_context)
    # OutputManager handles list of Pydantic models automatically for both JSON and Table
    print_output(actions, title="Available Actions")

@app.command()
def status(
    json: AgentOutput = False,
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh of agent state")
):
    """View status of Agent Providers."""
    state_manager = AgentStateManager()
    state = state_manager.get_or_refresh(force=force)
    
    if OutputManager.is_agent_mode():
        # Convert datetime to ISO string for JSON serialization
        data = state.dict()
        data["last_checked"] = data["last_checked"].isoformat()
        OutputManager.print(data)
    else:
        # Standard output using existing print_output or custom formatting
        from monoco.core.output import Table
        from rich import print as rprint
        
        table = Table(title=f"Agent Status (Last Checked: {state.last_checked.strftime('%Y-%m-%d %H:%M:%S')})")
        table.add_column("Provider")
        table.add_column("Available")
        table.add_column("Path")
        table.add_column("Error")
        
        for name, p_state in state.providers.items():
            table.add_row(
                name,
                "✅" if p_state.available else "❌",
                p_state.path or "-",
                p_state.error or "-"
            )
        rprint(table)

@app.command()
def doctor(
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh of agent state")
):
    """
    Diagnose Agent Environment and refresh state.
    """
    from monoco.features.agent.doctor import doctor as doc_impl
    doc_impl(force)
