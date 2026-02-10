"""
Ralph Loop Models - Agent Session Relay Data Structures.
"""

from datetime import datetime
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field


class LastWords(BaseModel):
    """
    Key information left by the current Agent for the successor.

    Signal Queue Model:
    - Last Words are a signal, not an asset
    - File existence = relay pending
    - File deletion = relay consumed (successor started)
    - Git is the archive
    """
    completed_work: str = Field(description="已完成的工作和验证结果")
    current_state: str = Field(description="当前代码/文件状态")
    obstacles: Optional[str] = Field(None, description="遇到的障碍或不确定的问题")
    next_steps: str = Field(description="建议的下一步方向")
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """Render Last Words to Markdown format."""
        lines = [
            "# Ralph Loop - Last Words",
            "",
            f"**Generated**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 已完成的工作",
            self.completed_work,
            "",
            "## 当前状态",
            self.current_state,
            "",
        ]
        if self.obstacles:
            lines.extend([
                "## 遇到的障碍",
                self.obstacles,
                "",
            ])
        lines.extend([
            "## 建议的下一步",
            self.next_steps,
            "",
        ])
        return "\n".join(lines)

    @classmethod
    def from_prompt(cls, prompt: str) -> "LastWords":
        """Create LastWords from a simple prompt string."""
        return cls(
            completed_work="参见原始 Agent 的完整上下文",
            current_state=prompt,
            next_steps="继续推进当前 Issue",
        )


class RelayStatus:
    """Relay status enumeration."""
    PENDING = "pending"      # Last Words written, waiting for successor
    ACTIVE = "active"        # Successor agent running
    COMPLETED = "completed"  # Relay finished
    FAILED = "failed"        # Relay failed


class RalphRelay(BaseModel):
    """
    Ralph Loop Relay Record.

    Tracks the state of an Agent-to-Agent handoff for a specific Issue.
    """
    issue_id: str = Field(description="关联的 Issue ID")
    session_id: Optional[str] = Field(None, description="原始 Agent 的会话 ID")

    # Relay State
    status: str = Field(default=RelayStatus.PENDING)
    last_words_path: Optional[Path] = Field(None, description="Last Words 文件路径")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)

    # Successor Info
    successor_pid: Optional[int] = Field(None, description="继任 Agent 的进程 ID")

    class Config:
        arbitrary_types_allowed = True
