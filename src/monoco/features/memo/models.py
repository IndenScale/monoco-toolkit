from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Memo(BaseModel):
    """
    Memo (Fleeting Note) - Signal Queue Model.
    
    In the Signal Queue paradigm (FEAT-0165):
    - Memo is a signal, not an asset
    - File existence = signal pending
    - File deletion = signal consumed
    - No status tracking - Git is the archive
    
    Attributes:
        uid: Unique identifier (6-char hex)
        content: The memo content
        timestamp: When the memo was created
        context: Optional context (file:line, etc.)
        author: Who created the memo (User, Assistant, Agent name)
        source: How the memo was created (cli, agent)
        type: Type of memo (insight, bug, feature, task)
    """
    uid: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Optional Context
    context: Optional[str] = None
    
    # Metadata Fields
    author: str = "User"  # User, Assistant, or specific Agent Name
    source: str = "cli"   # cli, agent, etc.
    type: Literal["insight", "bug", "feature", "task"] = "insight"
    
    def to_markdown(self) -> str:
        """
        Render the memo to Markdown format.
        
        Signal Queue Model:
        - No status field (existence is the state)
        - No ref field (traceability via git history)
        """
        ts_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        header = f"## [{self.uid}] {ts_str}"
        
        # Metadata block
        meta = []
        if self.author != "User":
            meta.append(f"- **From**: {self.author}")
        if self.source != "cli":
            meta.append(f"- **Source**: {self.source}")
        if self.type != "insight":
             meta.append(f"- **Type**: {self.type}")
        
        if self.context:
            meta.append(f"- **Context**: `{self.context}`")
            
        meta_block = "\n".join(meta)
        
        return f"\n{header}\n{meta_block}\n\n{self.content.strip()}\n"
