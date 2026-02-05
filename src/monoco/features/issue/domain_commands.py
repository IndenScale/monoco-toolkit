import typer
from rich.table import Table
from rich.console import Console
from monoco.features.issue.domain_service import DomainService

app = typer.Typer(help="Manage domain ontology.")
console = Console()


@app.command("list")
def list_domains():
    """List defined domains and aliases."""
    service = DomainService()
    config = service.config

    table = Table(title=f"Domain Ontology (Strict: {config.strict})")
    table.add_column("Canonical Name", style="bold cyan")
    table.add_column("Description", style="white")
    table.add_column("Aliases", style="yellow")

    for item in config.items:
        table.add_row(
            item.name,
            item.description or "",
            ", ".join(item.aliases) if item.aliases else "-",
        )

    console.print(table)
