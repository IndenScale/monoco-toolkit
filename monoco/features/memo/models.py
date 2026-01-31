from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

class Memo(BaseModel):
    uid: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Optional Context
    context: Optional[str] = None
    
    # New Metadata Fields
    author: str = "User"  # User, Assistant, or specific Agent Name
    source: str = "cli"   # cli, agent, mailroom, etc.
    status: Literal["pending", "tracked", "resolved", "dismissed"] = "pending"
    ref: Optional[str] = None  # Linked Issue ID or other reference
    type: Literal["insight", "bug", "feature", "task"] = "insight"
    
    def to_markdown(self) -> str:
        """
        Render the memo to Markdown format.
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
        
        # Status line with checkbox simulation
        status_map = {
            "pending": "[ ] Pending",
            "tracked": "[x] Tracked",
            "resolved": "[x] Resolved",
            "dismissed": "[-] Dismissed"
        }
        meta.append(f"- **Status**: {status_map.get(self.status, '[ ] Pending')}")
        
        if self.ref:
            meta.append(f"- **Ref**: {self.ref}")
            
        if self.context:
            meta.append(f"- **Context**: `{self.context}`")
            
        meta_block = "\n".join(meta)
        
        return f"\n{header}\n{meta_block}\n\n{self.content.strip()}\n"
