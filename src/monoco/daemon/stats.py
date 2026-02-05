from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from pydantic import BaseModel
from monoco.features.issue.core import list_issues
from monoco.features.issue.models import IssueStatus, IssueMetadata


class ActivityType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    CLOSED = "closed"


class ActivityItem(BaseModel):
    id: str
    type: ActivityType
    issue_id: str
    issue_title: str
    timestamp: datetime
    description: Optional[str] = None


class DashboardStats(BaseModel):
    total_backlog: int
    completed_this_week: int
    blocked_issues_count: int
    velocity_trend: int  # Delta compared to last week
    recent_activities: List[ActivityItem] = []


def calculate_dashboard_stats(issues_root: Path) -> DashboardStats:
    raw_issues = list_issues(issues_root)

    # 1. Pre-process for fast lookup and deduplication
    issue_map: Dict[str, IssueMetadata] = {i.id: i for i in raw_issues}
    issues = list(issue_map.values())

    backlog_count = 0
    completed_this_week = 0
    completed_last_week = 0
    blocked_count = 0

    now = datetime.now()
    one_week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    activity_window = now - timedelta(days=3)  # Show activities from last 3 days

    activities: List[ActivityItem] = []

    for issue in issues:
        # --- Stats Calculation ---
        # Total Backlog
        if issue.status == IssueStatus.BACKLOG:
            backlog_count += 1

        # Completed This Week & Last Week
        if issue.status == IssueStatus.CLOSED and issue.closed_at:
            closed_at = issue.closed_at
            if closed_at >= one_week_ago:
                completed_this_week += 1
            elif closed_at >= two_weeks_ago and closed_at < one_week_ago:
                completed_last_week += 1

        # Blocked Issues
        if issue.status == IssueStatus.OPEN:
            is_blocked = False
            for dep_id in issue.dependencies:
                dep_issue = issue_map.get(dep_id)
                if not dep_issue or dep_issue.status != IssueStatus.CLOSED:
                    is_blocked = True
                    break
            if is_blocked:
                blocked_count += 1

        # --- Activity Feed Generation ---
        # 1. Created Event
        if issue.created_at >= activity_window:
            activities.append(
                ActivityItem(
                    id=f"act_create_{issue.id}",
                    type=ActivityType.CREATED,
                    issue_id=issue.id,
                    issue_title=issue.title,
                    timestamp=issue.created_at,
                    description="Issue created",
                )
            )

        # 2. Closed Event
        if (
            issue.status == IssueStatus.CLOSED
            and issue.closed_at
            and issue.closed_at >= activity_window
        ):
            activities.append(
                ActivityItem(
                    id=f"act_close_{issue.id}",
                    type=ActivityType.CLOSED,
                    issue_id=issue.id,
                    issue_title=issue.title,
                    timestamp=issue.closed_at,
                    description="Issue completed",
                )
            )

        # 3. Updated Event (Heuristic: updated recently and not just created/closed)
        # We skip 'updated' if it's too close to created_at or closed_at to avoid noise
        if issue.updated_at >= activity_window:
            is_creation = (
                abs((issue.updated_at - issue.created_at).total_seconds()) < 60
            )
            is_closing = (
                issue.closed_at
                and abs((issue.updated_at - issue.closed_at).total_seconds()) < 60
            )

            if not is_creation and not is_closing:
                activities.append(
                    ActivityItem(
                        id=f"act_update_{issue.id}_{issue.updated_at.timestamp()}",
                        type=ActivityType.UPDATED,
                        issue_id=issue.id,
                        issue_title=issue.title,
                        timestamp=issue.updated_at,
                        description="Issue updated",
                    )
                )

    # Sort activities by timestamp desc and take top 20
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    recent_activities = activities[:20]

    velocity_trend = completed_this_week - completed_last_week

    return DashboardStats(
        total_backlog=backlog_count,
        completed_this_week=completed_this_week,
        blocked_issues_count=blocked_count,
        velocity_trend=velocity_trend,
        recent_activities=recent_activities,
    )
