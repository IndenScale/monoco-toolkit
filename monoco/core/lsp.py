from enum import IntEnum
from typing import List, Optional, Union
from pydantic import BaseModel

class Position(BaseModel):
    """
    Position in a text document expressed as zero-based line and character offset.
    """
    line: int
    character: int

    def __lt__(self, other):
        if self.line != other.line:
            return self.line < other.line
        return self.character < other.character

class Range(BaseModel):
    """
    A range in a text document expressed as (zero-based) start and end positions.
    """
    start: Position
    end: Position

    def __repr__(self):
        return f"{self.start.line}:{self.start.character}-{self.end.line}:{self.end.character}"

class Location(BaseModel):
    """
    Represents a location inside a resource, such as a line of code inside a text file.
    """
    uri: str
    range: Range

class DiagnosticSeverity(IntEnum):
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4

class DiagnosticRelatedInformation(BaseModel):
    """
    Represents a related message and source code location for a diagnostic.
    """
    # location: Location  # Defined elsewhere or simplified here
    message: str

class Diagnostic(BaseModel):
    """
    Represents a diagnostic, such as a compiler error or warning.
    """
    range: Range
    severity: Optional[DiagnosticSeverity] = None
    code: Optional[Union[int, str]] = None
    source: Optional[str] = "monoco"
    message: str
    related_information: Optional[List[DiagnosticRelatedInformation]] = None
    data: Optional[dict] = None  # To carry extra info (e.g. for code actions)

    def to_user_string(self) -> str:
        """Helper to format for CLI output"""
        severity_map = {
            1: "[red]Error[/red]",
            2: "[yellow]Warning[/yellow]",
            3: "[blue]Info[/blue]",
            4: "[dim]Hint[/dim]"
        }
        sev = severity_map.get(self.severity, "Error")
        return f"{sev}: {self.message} (Line {self.range.start.line + 1})"
