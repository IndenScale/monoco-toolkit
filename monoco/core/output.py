import os
import json
import typer
from typing import Any, List, Union, Annotated
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

    @staticmethod
    def is_agent_mode() -> bool:
        """
        Check if running in Agent Mode.
        Triggers:
            1. Environment variable AGENT_FLAG=true (or 1)
            2. Environment variable MONOCO_AGENT=true (or 1)
        """
        return os.getenv("AGENT_FLAG", "").lower() in ("true", "1") or os.getenv(
            "MONOCO_AGENT", ""
        ).lower() in ("true", "1")

    @staticmethod
    def print(
        data: Union[BaseModel, List[BaseModel], dict, list, str], title: str = ""
    ):
        """
        Dual frontend dispatcher.
        """
        if OutputManager.is_agent_mode():
            OutputManager._render_agent(data)
        else:
            OutputManager._render_human(data, title)

    @staticmethod
    def error(message: str):
        """
        Print error message.
        """
        if OutputManager.is_agent_mode():
            print(json.dumps({"error": message}))
        else:
            rprint(f"[bold red]Error:[/bold red] {message}")

    @staticmethod
    def _render_agent(data: Any):
        """
        Agent channel: Zero decoration, Pure Data, Max Token Density.
        Uses compact JSON.
        """
        if isinstance(data, BaseModel):
            print(data.model_dump_json(exclude_none=True))
        elif isinstance(data, list) and all(
            isinstance(item, BaseModel) for item in data
        ):
            # Pydantic v2 adapter for list of models
            print(
                json.dumps(
                    [item.model_dump(mode="json", exclude_none=True) for item in data],
                    separators=(",", ":"),
                )
            )
        else:
            # Fallback for dicts/lists/primitives
            def _encoder(obj):
                if isinstance(obj, BaseModel):
                    return obj.model_dump(mode="json", exclude_none=True)
                if hasattr(obj, "value"):  # Enum support
                    return obj.value
                return str(obj)

            try:
                print(json.dumps(data, separators=(",", ":"), default=_encoder))
            except TypeError:
                print(str(data))

    @staticmethod
    def _render_human(data: Any, title: str):
        """
        Human channel: Visual priority.
        """
        console = Console()

        if title:
            console.rule(f"[bold blue]{title}[/bold blue]")

        if isinstance(data, str):
            console.print(data)
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

        # Fallback to rich pretty print
        rprint(data)


# Global helper
print_output = OutputManager.print
print_error = OutputManager.error
