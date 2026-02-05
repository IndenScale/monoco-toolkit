import os
import json
import sys
import typer
from typing import Any, List, Union, Annotated, Optional
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich import print as rprint


def _set_agent_mode(value: bool):
    if value:
        os.environ["AGENT_FLAG"] = "true"


# Reusable dependency for commands
AgentOutput = Annotated[
    bool,
    typer.Option(
        "--json", help="Output in compact JSON for Agents", callback=_set_agent_mode
    ),
]


class OutputManager:
    """
    Manages output rendering based on the environment (Human vs Agent).
    """
    
    _console = Console(stderr=False)
    _stderr_console = Console(stderr=True)

    @staticmethod
    def is_agent_mode() -> bool:
        """
        Check if running in Agent Mode.
        """
        return os.getenv("AGENT_FLAG", "").lower() in ("true", "1") or os.getenv(
            "MONOCO_AGENT", ""
        ).lower() in ("true", "1")

    @staticmethod
    def print(
        data: Union[BaseModel, List[BaseModel], dict, list, str], title: str = "", style: Optional[str] = None
    ):
        """
        Data frontend (Command Result) -> Stdout.
        """
        if OutputManager.is_agent_mode():
            OutputManager._render_agent(data, stream=sys.stdout)
        else:
            OutputManager._render_human(data, title, style=style, stream=sys.stdout)

    @staticmethod
    def info(message: str, suggestions: Optional[List[str]] = None):
        """
        Auxiliary info / Suggestions -> Stderr.
        """
        if OutputManager.is_agent_mode():
            OutputManager._render_agent({"info": message, "suggestions": suggestions}, stream=sys.stderr)
        else:
            OutputManager._stderr_console.print(f"[bold blue]ℹ[/bold blue] {message}")
            if suggestions:
                for s in suggestions:
                    OutputManager._stderr_console.print(f"  [yellow]•[/yellow] {s}")

    @staticmethod
    def error(message: str):
        """
        Error message -> Stderr.
        """
        if OutputManager.is_agent_mode():
            OutputManager._render_agent({"error": message}, stream=sys.stderr)
        else:
            OutputManager._stderr_console.print(f"[bold red]Error:[/bold red] {message}")

    @staticmethod
    def _render_agent(data: Any, stream=sys.stdout):
        """
        Agent channel: Zero decoration, Pure Data -> Specific Stream.
        """
        def _encoder(obj):
            if isinstance(obj, BaseModel):
                return obj.model_dump(mode="json", exclude_none=True)
            if hasattr(obj, "value"):  # Enum support
                return obj.value
            return str(obj)

        output = ""
        if isinstance(data, BaseModel):
            output = data.model_dump_json(exclude_none=True)
        elif isinstance(data, list) and data and all(isinstance(item, BaseModel) for item in data):
            output = json.dumps(
                [item.model_dump(mode="json", exclude_none=True) for item in data],
                separators=(",", ":"),
            )
        else:
            output = json.dumps(data, separators=(",", ":"), default=_encoder)
        
        stream.write(output + "\n")
        stream.flush()

    @staticmethod
    def _render_human(data: Any, title: str, style: Optional[str] = None, stream=sys.stdout):
        """
        Human channel: Visual priority.
        """
        console = Console(file=stream)

        if title:
            console.rule(f"[bold blue]{title}[/bold blue]")

        if isinstance(data, str):
            console.print(data, style=style)
            return

        # Special handling for Lists of Pydantic Models -> Table
        if isinstance(data, list) and data and isinstance(data[0], BaseModel):
            table = Table(show_header=True, header_style="bold magenta")

            # Introspect fields from the first item
            model_type = type(data[0])
            fields = model_type.model_fields.keys()

            for field in fields:
                table.add_column(field.replace("_", " ").title())

            for item in data:
                row = [str(getattr(item, field)) for field in fields]
                table.add_row(*row)

            console.print(table)
            return

        # Fallback to pretty print
        if isinstance(data, (dict, list)):
            console.print(data)
        else:
            console.print(str(data))


# Global helpers
print_output = OutputManager.print
print_info = OutputManager.info
print_error = OutputManager.error
