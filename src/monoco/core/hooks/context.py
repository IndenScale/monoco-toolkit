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
    def from_agent_task(
        cls,
        task: Any,
        project_root: Optional[Path] = None,
    ) -> "HookContext":
        """
        Create a HookContext from an AgentTask.
        
        Args:
            task: The AgentTask object
            project_root: Optional project root path
            
        Returns:
            A populated HookContext
        """
        # Build IssueInfo if we have an issue_id
        issue_info = None
        issue_id = getattr(task, "issue_id", None)
        if issue_id:
            issue_info = IssueInfo(
                id=issue_id,
            )
            
            # Try to load full issue metadata
            try:
                from monoco.features.issue.core import find_issue_path, parse_issue
                from monoco.core.config import find_monoco_root
                
                if project_root is None:
                    project_root = find_monoco_root()
                
                issues_root = project_root / "Issues"
                issue_path = find_issue_path(issues_root, issue_id)
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
            session_id=getattr(task, "task_id", "unknown"),
            role_name=getattr(task, "role_name", "unknown"),
            session_status="pending",
            created_at=getattr(task, "created_at", datetime.now()),
            issue=issue_info,
            git=git_info,
        )
    
    @classmethod
    def from_session_state(
        cls,
        session_id: str,
        role_name: str,
        issue_id: Optional[str],
        status: str,
        project_root: Optional[Path] = None,
    ) -> "HookContext":
        """
        Create a HookContext from session state parameters.
        
        This is a more flexible factory method that doesn't depend on
        specific session implementations.
        
        Args:
            session_id: The session/task ID
            role_name: The role name
            issue_id: Optional issue ID
            status: Session status
            project_root: Optional project root path
            
        Returns:
            A populated HookContext
        """
        # Build IssueInfo if we have an issue_id
        issue_info = None
        if issue_id:
            issue_info = IssueInfo(
                id=issue_id,
            )
            
            # Try to load full issue metadata
            try:
                from monoco.features.issue.core import find_issue_path, parse_issue
                from monoco.core.config import find_monoco_root
                
                if project_root is None:
                    project_root = find_monoco_root()
                
                issues_root = project_root / "Issues"
                issue_path = find_issue_path(issues_root, issue_id)
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
            session_id=session_id,
            role_name=role_name,
            session_status=status,
            created_at=datetime.now(),
            issue=issue_info,
            git=git_info,
        )
