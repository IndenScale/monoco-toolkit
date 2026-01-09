import os
import typer
from typing import Optional
from monoco.core.output import print_output

app = typer.Typer(
    name="monoco",
    help="Monoco Agent Native Toolkit",
    add_completion=False,
    no_args_is_help=True
)


@app.callback()
def main():
    """
    Monoco Toolkit - The sensory and motor system for Monoco Agents.
    """
    pass

from monoco.core.setup import init_cli
app.command(name="init")(init_cli)

@app.command()
def info():
    """
    Show toolkit information and current mode.
    """
    from pydantic import BaseModel
    from monoco.core.config import get_config
    
    settings = get_config()

    class Status(BaseModel):
        version: str
        mode: str
        root: str
        project: str

    mode = "Agent (JSON)" if os.getenv("AGENT_FLAG") == "true" else "Human (Rich)"
    
    status = Status(
        version="0.1.0",
        mode=mode,
        root=os.getcwd(),
        project=f"{settings.project.name} ({settings.project.key})"
    )
    
    print_output(status, title="Monoco Toolkit Status")
    
    if mode == "Human (Rich)":
        print_output(settings, title="Current Configuration")

# Register Feature Modules
# Register Feature Modules
from monoco.features.issue import commands as issue_cmd
from monoco.features.spike import commands as spike_cmd
from monoco.features.i18n import commands as i18n_cmd

app.add_typer(issue_cmd.app, name="issue", help="Manage development issues")
app.add_typer(spike_cmd.app, name="spike", help="Manage research spikes")
app.add_typer(i18n_cmd.app, name="i18n", help="Manage documentation i18n")

if __name__ == "__main__":
    app()
