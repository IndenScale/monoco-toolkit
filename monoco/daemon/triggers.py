from typing import TYPE_CHECKING, Optional, List, Any
from pathlib import Path
from monoco.features.memo.core import load_memos
from monoco.features.issue.models import IssueMetadata, IssueStatus, IssueStage

if TYPE_CHECKING:
    from monoco.features.issue.models import IssueMetadata

class TriggerPolicy:
    """
    Base class for trigger policies.
    """
    def evaluate(self, context: dict) -> bool:
        raise NotImplementedError

class MemoAccumulationPolicy(TriggerPolicy):
    """
    Trigger when pending memos exceed a threshold.
    """
    def __init__(self, count_threshold: int = 5):
        self.count_threshold = count_threshold

    def evaluate(self, context: dict) -> bool:
        issues_root = context.get("issues_root")
        if not issues_root:
            return False
        
        if isinstance(issues_root, str):
            issues_root = Path(issues_root)
            
        try:
            memos = load_memos(issues_root)
            pending_memos = [m for m in memos if m.status == "pending"]
            return len(pending_memos) >= self.count_threshold
        except Exception as e:
            print(f"Error evaluating MemoAccumulationPolicy: {e}")
            return False

class HandoverPolicy(TriggerPolicy):
    """
    Trigger when an issue enters a specific state (e.g. Open/Doing for Engineer).
    """
    def __init__(self, target_status: IssueStatus, target_stage: IssueStage):
        self.target_status = target_status
        self.target_stage = target_stage

    def evaluate(self, context: dict) -> bool:
        issue: Optional[IssueMetadata] = context.get("issue")
        if not issue:
            return False
            
        return (
            issue.status == self.target_status 
            and issue.stage == self.target_stage
        )
