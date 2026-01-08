import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .models import IssueMetadata, IssueType, IssueStatus

def get_issue_dir(issue_type: IssueType, root_dir: Path) -> Path:
    mapping = {
        IssueType.EPIC: "EPICS",
        IssueType.STORY: "STORIES",
        IssueType.TASK: "TASKS",
        IssueType.BUG: "BUGS",
    }
    return root_dir / "ISSUES" / mapping[issue_type]

def parse_issue(file_path: Path) -> Optional[IssueMetadata]:
    if not file_path.suffix == ".md":
        return None
    
    content = file_path.read_text()
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if not match:
        return None
    
    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
             return None
        return IssueMetadata(**data)
    except Exception:
        return None

def find_next_id(issue_type: IssueType, root_dir: Path) -> str:
    pattern = re.compile(rf"{issue_type.value.upper()}-(\d+)")
    max_id = 0
    
    base_dir = get_issue_dir(issue_type, root_dir)
    # Scan all subdirs: open, backlog, closed
    for status_dir in ["open", "backlog", "closed"]:
        d = base_dir / status_dir
        if d.exists():
            for f in d.glob("*.md"):
                match = pattern.search(f.name)
                if match:
                    max_id = max(max_id, int(match.group(1)))
    
    return f"{issue_type.value.upper()}-{max_id + 1:04d}"

def create_issue_file(root_dir: Path, issue_type: IssueType, title: str, parent: Optional[str] = None, status: IssueStatus = IssueStatus.OPEN) -> str:
    issue_id = find_next_id(issue_type, root_dir)
    base_type_dir = get_issue_dir(issue_type, root_dir)
    target_dir = base_type_dir / status.value
    target_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = IssueMetadata(
        id=issue_id,
        type=issue_type,
        status=status,
        title=title,
        parent=parent
    )
    
    yaml_header = yaml.dump(metadata.model_dump(exclude_none=True), sort_keys=False, allow_unicode=True)
    slug = title.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)[:30]
    filename = f"{issue_id}-{slug}.md"
    
    file_content = f"""---
{yaml_header}---

# {issue_id}: {title}

## Objective

## Acceptance Criteria

## Technical Tasks

- [ ] 
"""
    (target_dir / filename).write_text(file_content)
    return issue_id

def find_issue_path(root_dir: Path, issue_id: str) -> Optional[Path]:
    issue_type_str = issue_id.split("-")[0].lower()
    try:
        issue_type = IssueType(issue_type_str)
    except ValueError:
        return None
        
    base_dir = get_issue_dir(issue_type, root_dir)
    # Search in all status subdirs recursively
    for f in base_dir.rglob(f"{issue_id}-*.md"):
        return f
    return None

def update_issue_status(root_dir: Path, issue_id: str, new_status: IssueStatus, solution: Optional[IssueSolution] = None):
    path = find_issue_path(root_dir, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")
        
    current_meta = parse_issue(path)
    if not current_meta:
        raise ValueError(f"Could not parse metadata for {issue_id}")

    # Validation: For closing, we MUST have a solution either in args or in file
    if new_status == IssueStatus.CLOSED:
        final_solution = solution or current_meta.solution
        if not final_solution:
            raise ValueError(f"Closing an issue requires a solution. Please provide --solution or edit the file metadata.")
        solution = final_solution

    content = path.read_text()
    
    # 1. Update status
    new_content = re.sub(r"status: \w+", f"status: {new_status.value}", content)
    
    # 2. Update solution if provided or validated
    if solution:
        sol_val = solution.value
        if "solution:" in new_content:
            new_content = re.sub(r"solution:.*", f"solution: {sol_val}", new_content)
        else:
            if "tags:" in new_content:
                new_content = new_content.replace("tags:", f"solution: {sol_val}\ntags:")
            else:
                new_content = new_content.replace("---", f"solution: {sol_val}\n---", 1)

    path.write_text(new_content)
    
    # 3. Handle physical move
    base_type_dir = get_issue_dir(IssueType(issue_id.split("-")[0].lower()), root_dir)
    target_dir = base_type_dir / new_status.value
        
    if path.parent != target_dir:
        target_dir.mkdir(parents=True, exist_ok=True)
        new_path = target_dir / path.name
        path.rename(new_path)
