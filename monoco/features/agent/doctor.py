import typer
from monoco.core.output import print_output, print_error
from monoco.core.agent.state import AgentStateManager

app = typer.Typer()

@app.command()
def doctor(
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh of agent state")
):
    """
    Diagnose Agent Environment and refresh state.
    """
    manager = AgentStateManager()
    try:
        if force:
            print("Force refreshing agent state...")
            state = manager.refresh()
        else:
            state = manager.get_or_refresh()
            
        print_output(state, title="Agent Diagnosis Report")
        
        # Simple summary
        available = [k for k, v in state.providers.items() if v.available]
        print(f"\n✅ Available Agents: {', '.join(available) if available else 'None'}")
        
    except Exception as e:
        print_error(f"Doctor failed: {e}")
        raise typer.Exit(1)
