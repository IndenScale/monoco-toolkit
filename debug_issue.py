
from pathlib import Path
import sys
import os

# Adjust path to include monoco package
sys.path.append(str(Path.cwd()))

from monoco.features.issue.core import find_issue_path
from monoco.features.issue.models import IssueID
from monoco.core.config import get_config

cwd = Path.cwd()
print(f"CWD: {cwd}")

issues_root = cwd / "Issues"
print(f"Issues Root: {issues_root}")

issue_id = "monoco::EPIC-0004"
print(f"Target ID: {issue_id}")

parsed = IssueID(issue_id)
print(f"Parsed: Namespace={parsed.namespace}, LocalID={parsed.local_id}")

project_root = issues_root.parent
print(f"Project Root: {project_root}")

conf = get_config(str(project_root))
print(f"Config Members: {conf.project.members}")

member_rel = conf.project.members.get(parsed.namespace)
print(f"Member Rel Path: {member_rel}")

if member_rel:
    member_root = (project_root / member_rel).resolve()
    print(f"Member Root: {member_root}")
    member_issues = member_root / "Issues"
    print(f"Member Issues: {member_issues} (Exists: {member_issues.exists()})")
    
    if member_issues.exists():
        found = find_issue_path(member_issues, parsed.local_id)
        print(f"Found Path: {found}")
    else:
        print("Member Issues dir not found")
else:
    print("Member not found in config")

path = find_issue_path(issues_root, issue_id)
print(f"Result: {path}")
