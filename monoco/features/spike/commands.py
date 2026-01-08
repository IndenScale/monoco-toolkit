import typer
from typing import List
from pydantic import BaseModel
from monoco.core.output import print_output, AgentOutput

app = typer.Typer()

class SpikeReference(BaseModel):
    id: str
    url: str
    summary: str

@app.command("list")
def list_spikes(
    json: AgentOutput = False,
):
    """
    List active research spikes and references.
    """
    # Stub data
    refs = [
        SpikeReference(id="SPIKE-001", url="https://github.com/features/actions", summary="GitHub Actions Analysis"),
    ]
    
    print_output(refs, title="Spike References")
