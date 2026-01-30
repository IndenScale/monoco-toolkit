"""
Hook Context - Data passed to hooks during session lifecycle events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class IssueInfo:
    """Information about the issue associated with a session."""
    id: str
    status: Optional[str] = None
    stage: Optional[str] = None
    title: Optional[str] = None
    branch_name: Optional[str] = None
    is_merged: bool = False
    
    @classmethod
    def from_metadata(cls, metadata: Any) -> "IssueInfo":
        """Create IssueInfo from IssueMetadata."""
        return cls(
            id=getattr(metadata, "id", ""),
            status=getattr(metadata, "status", None),
            stage=getattr(metadata, "stage", None),
            title=getattr(metadata, "title", None),
            branch_name=getattr(metadata, "isolation", {}).get("ref") if hasattr(metadata, "isolation") and metadata.isolation else None,
            is_merged=False,  # Will be determined by GitCleanupHook
        )


@dataclass
class GitInfo:
    """Git repository information."""
    project_root: Path
    current_branch: Optional[str] = None
    has_uncommitted_changes: bool = False
    default_branch: str = "main"
    
    def __post_init__(self):
        if self.current_branch is None:
            # Lazy load current branch
            try:
                from monoco.core import git
                self.current_branch = git.get_current_branch(self.project_root)
            except Exception:
                self.current_branch = None


@dataclass
class HookContext:
    """
    Context object passed to lifecycle hooks.
    
    Contains all relevant information about the session, issue, and environment
    that hooks might need to perform their operations.
    """
    
    # Session Information
    session_id: str
    role_name: str
    session_status: str
    created_at: datetime
    
    # Issue Information
    issue: Optional[IssueInfo] = None
    
    # Git Information
    git: Optional[GitInfo] = None
    
    # Additional Context
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_runtime_session(
        cls,
        runtime_session: Any,
        project_root: Optional[Path] = None,
    ) -> "HookContext":
        """
        Create a HookContext from a RuntimeSession.
        
        Args:
            runtime_session: The RuntimeSession object
            project_root: Optional project root path
            
        Returns:
            A populated HookContext
        """
        model = runtime_session.model
        
        # Build IssueInfo if we have an issue_id
        issue_info = None
        if model.issue_id:
            issue_info = IssueInfo(
                id=model.issue_id,
                branch_name=model.branch_name,
            )
            
            # Try to load full issue metadata
            try:
                from monoco.features.issue.core import find_issue_path, parse_issue
                from monoco.core.config import find_monoco_root
                
                if project_root is None:
                    project_root = find_monoco_root()
                
                issues_root = project_root / "Issues"
                issue_path = find_issue_path(issues_root, model.issue_id)
                if issue_path:
                    metadata = parse_issue(issue_path)
                    if metadata:
                        issue_info = IssueInfo.from_metadata(metadata)
            except Exception:
                pass  # Use basic issue info
        
        # Build GitInfo
        git_info = None
        if project_root:
            git_info = GitInfo(project_root=project_root)
        
        return cls(
            session_id=model.id,
            role_name=model.role_name,
            session_status=model.status,
            created_at=model.created_at,
            issue=issue_info,
            git=git_info,
        )
