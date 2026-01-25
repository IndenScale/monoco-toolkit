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


@app.command("check")
def check_domain(domain: str = typer.Argument(..., help="Domain name to check")):
    """Check if a domain is valid and resolve it."""
    service = DomainService()

    if service.is_canonical(domain):
        console.print(f"[green]✔ '{domain}' is a canonical domain.[/green]")
    elif service.is_alias(domain):
        canonical = service.get_canonical(domain)
        console.print(f"[yellow]➜ '{domain}' is an alias for '{canonical}'.[/yellow]")
    else:
        if service.config.strict:
            console.print(f"[red]✘ '{domain}' is NOT a valid domain.[/red]")
        else:
            console.print(
                f"[yellow]⚠ '{domain}' is undefined (Strict Mode: OFF).[/yellow]"
            )
