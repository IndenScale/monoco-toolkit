import sys
from pathlib import Path

# Add Toolkit to sys.path
sys.path.append("/Users/indenscale/Documents/Projects/Monoco/Toolkit")

from monoco.daemon.stats import calculate_dashboard_stats


def run():
    issues_root = Path("/Users/indenscale/Documents/Projects/Monoco/Toolkit/Issues")
    print(f"Scanning {issues_root}...")

    stats = calculate_dashboard_stats(issues_root)

    print(f"Found {len(stats.recent_activities)} activities.")

    seen_ids = set()
    for act in stats.recent_activities:
        print(f"[{act.type}] {act.id} - {act.issue_title} ({act.timestamp})")
        if act.id in seen_ids:
            print(f"!!! DUPLICATE ID FOUND: {act.id}")
        seen_ids.add(act.id)

        # Check for duplicate issue + type
        # e.g. multiple UPDATED for same issue

    # Group by issue
    by_issue = {}
    for act in stats.recent_activities:
        if act.issue_id not in by_issue:
            by_issue[act.issue_id] = []
        by_issue[act.issue_id].append(act)

    for issue_id, acts in by_issue.items():
        if len(acts) > 1:
            print(f"Issue {issue_id} has multiple activities: {[a.type for a in acts]}")


if __name__ == "__main__":
    run()
