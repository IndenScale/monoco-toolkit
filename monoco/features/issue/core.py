import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from .models import IssueMetadata, IssueType, IssueStatus, IssueSolution, IssueStage

PREFIX_MAP = {
    IssueType.EPIC: "EPIC",
    IssueType.FEATURE: "FEAT",
    IssueType.CHORE: "CHORE",
    IssueType.FIX: "FIX"
}

REVERSE_PREFIX_MAP = {v: k for k, v in PREFIX_MAP.items()}

def get_issue_dir(issue_type: IssueType, issues_root: Path) -> Path:
    mapping = {
        IssueType.EPIC: "Epics",
        IssueType.FEATURE: "Features",
        IssueType.CHORE: "Chores",
        IssueType.FIX: "Fixes",
    }
    return issues_root / mapping[issue_type]

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

def find_next_id(issue_type: IssueType, issues_root: Path) -> str:
    prefix = PREFIX_MAP[issue_type]
    pattern = re.compile(rf"{prefix}-(\d+)")
    max_id = 0
    
    base_dir = get_issue_dir(issue_type, issues_root)
    # Scan all subdirs: open, backlog, closed
    for status_dir in ["open", "backlog", "closed"]:
        d = base_dir / status_dir
        if d.exists():
            for f in d.rglob("*.md"):
                match = pattern.search(f.name)
                if match:
                    max_id = max(max_id, int(match.group(1)))
    
    return f"{prefix}-{max_id + 1:04d}"

def create_issue_file(
    issues_root: Path, 
    issue_type: IssueType, 
    title: str, 
    parent: Optional[str] = None, 
    status: IssueStatus = IssueStatus.OPEN, 
    dependencies: List[str] = [], 
    related: List[str] = [], 
    subdir: Optional[str] = None,
    sprint: Optional[str] = None,
    tags: List[str] = []
) -> Tuple[IssueMetadata, Path]:
    
    # Validation
    for dep_id in dependencies:
        if not find_issue_path(issues_root, dep_id):
            raise ValueError(f"Dependency issue {dep_id} not found.")
            
    for rel_id in related:
        if not find_issue_path(issues_root, rel_id):
            raise ValueError(f"Related issue {rel_id} not found.")

    issue_id = find_next_id(issue_type, issues_root)
    base_type_dir = get_issue_dir(issue_type, issues_root)
    target_dir = base_type_dir / status.value
    
    if subdir:
        target_dir = target_dir / subdir
        
    target_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = IssueMetadata(
        id=issue_id,
        type=issue_type,
        status=status,
        title=title,
        parent=parent,
        dependencies=dependencies,
        related=related,
        sprint=sprint,
        tags=tags,
        opened_at=datetime.now() if status == IssueStatus.OPEN else None
    )
    
    yaml_header = yaml.dump(metadata.model_dump(exclude_none=True, mode='json'), sort_keys=False, allow_unicode=True)
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")[:50]
    filename = f"{issue_id}-{slug}.md"
    
    # Force created_at to be treated as string with quotes if needed, 
    # but standard YAML is fine. To ensure consistency, we can rely on Pydantic's JSON serialization
    # then load to dict for yaml dump. 
    # To fix "date quoting issues", we can force the dumper to quote the date string.
    
    # Custom representer to ensure dates are strings (if they aren't already) and maybe quoted?
    # Actually, the simplest way is to let YAML handle it, but if users see issues, 
    # it might be that they want explicit quotes '2026-01-09'.
    # We can post-process the line.
    
    yaml_header = yaml.dump(metadata.model_dump(exclude_none=True, mode='json'), sort_keys=False, allow_unicode=True)


    file_content = f"""---
{yaml_header}---

## {issue_id}: {title}

## Objective

## Acceptance Criteria

## Technical Tasks

- [ ] 
"""
    file_path = target_dir / filename
    file_path.write_text(file_content)
    return metadata, file_path

def find_issue_path(issues_root: Path, issue_id: str) -> Optional[Path]:
    prefix = issue_id.split("-")[0].upper()
    issue_type = REVERSE_PREFIX_MAP.get(prefix)
    if not issue_type:
        return None
        
    base_dir = get_issue_dir(issue_type, issues_root)
    # Search in all status subdirs recursively
    for f in base_dir.rglob(f"{issue_id}-*.md"):
        return f
    return None

def update_issue(issues_root: Path, issue_id: str, status: Optional[IssueStatus] = None, stage: Optional[IssueStage] = None, solution: Optional[IssueSolution] = None) -> IssueMetadata:
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")
        
    # Read full content
    content = path.read_text()
    
    # Split Frontmatter and Body
    match = re.search(r"^---(.*?)---\n(.*)$", content, re.DOTALL | re.MULTILINE)
    if not match:
        # Fallback
        match_simple = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
        if match_simple:
            yaml_str = match_simple.group(1)
            body = content[match_simple.end():]
        else:
            raise ValueError(f"Could not parse frontmatter for {issue_id}")
    else:
        yaml_str = match.group(1)
        body = match.group(2)

    try:
        data = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError:
        raise ValueError(f"Invalid YAML metadata in {issue_id}")

    current_status_str = data.get("status", "open") # default to open if missing?
    # Normalize current status to Enum for comparison
    try:
        current_status = IssueStatus(current_status_str.lower())
    except ValueError:
        current_status = IssueStatus.OPEN

    # Logic: Status Update
    target_status = status if status else current_status
    
    # Validation: For closing
    current_solution = data.get("solution")
    if target_status == IssueStatus.CLOSED:
        if not solution and not current_solution:
            raise ValueError(f"Closing an issue requires a solution. Please provide --solution or edit the file metadata.")
            
    # Update Data
    if status:
        data['status'] = status.value
    
    # Validation: Close Guard (Anti-Shortcut)
    if target_status == IssueStatus.CLOSED:
        # Check current stage (from file content)
        # Note: 'data' is already potentially modified with new status, 
        # but we need to check the OLD stage unless stage is also being updated.
        # If the user is passing "status=CLOSED", we must check what the stage WAS.
        # Actually 'data' here is:
        # 1. Loaded from file
        # 2. 'status' is overwritten if passed.
        # But 'stage' in data is still the old one UNLESS 'stage' arg was passed.
        
        current_data_stage = data.get('stage')
        # If user explicitly sets stage (e.g. to done) while closing, we should allow it?
        # Requirement: "CANNOT transition to closed IF stage: doing"
        # The intent is to force them to 'review' or 'todo' first.
        # So even if they say "close + done", if the previous state was "doing", should we block?
        # Usage: monoco issue close <id> --solution implemented
        # The command does NOT update stage. So data['stage'] is the old stage.
        
        if current_data_stage == IssueStage.DOING.value:
             # Exception: Unless they are explicitly resetting stage to something else?
             # command doesn't allow stage setting.
             # So checking data['stage'] is sufficient.
             raise ValueError("Cannot close issue in progress (Doing). Please review (`monoco issue submit`) or stop (`monoco issue open`) first.")

    if stage:
        data['stage'] = stage.value
    if solution:
        data['solution'] = solution.value
    
    # Lifecycle Hooks
    # 1. Opened At: If transitioning to OPEN
    if target_status == IssueStatus.OPEN and current_status != IssueStatus.OPEN:
        # Only set if not already set? Or always reset?
        # Let's set it if not present, or update it to reflect "Latest activation"
        # FEAT-0012 says: "update opened_at to now"
        data['opened_at'] = datetime.now()
    
    # 2. Backlog Push: Handled by IssueMetadata.validate_lifecycle (Status=Backlog -> Stage=None)
    # 3. Closed: Handled by IssueMetadata.validate_lifecycle (Status=Closed -> Stage=Done, ClosedAt=Now)

    # Touch updated_at
    data['updated_at'] = datetime.now()
    
    # Re-hydrate through Model to trigger Logic (Stage, ClosedAt defaults)
    try:
        updated_meta = IssueMetadata(**data)
    except Exception as e:
        raise ValueError(f"Failed to validate updated metadata: {e}")
        
    # Serialize back
    new_yaml = yaml.dump(updated_meta.model_dump(exclude_none=True, mode='json'), sort_keys=False, allow_unicode=True)
    
    # Reconstruct File
    match_header = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    body_content = content[match_header.end():]
    if body_content.startswith('\n'):
        body_content = body_content[1:] 
        
    new_content = f"---\n{new_yaml}---\n{body_content}"
    
    path.write_text(new_content)
    
    # 3. Handle physical move if status changed
    if status and status != current_status:
        # Move file
        prefix = issue_id.split("-")[0].upper()
        base_type_dir = get_issue_dir(REVERSE_PREFIX_MAP[prefix], issues_root)
        
        try:
            rel_path = path.relative_to(base_type_dir)
            # Remove the first component (current status directory)
            structure_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path(path.name)
        except ValueError:
            structure_path = Path(path.name)

        target_path = base_type_dir / target_status.value / structure_path
            
        if path != target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target_path)
    
    return updated_meta

def delete_issue_file(issues_root: Path, issue_id: str):
    """
    Physical removal of an issue file.
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")
    
    path.unlink()
        
# Resources
SKILL_CONTENT = """---
name: issues-management
description: Monoco Issue System 的官方技能定义。将 Issue 视为通用原子 (Universal Atom)，管理 Epic/Feature/Chore/Fix 的生命周期。
---

# 自我管理 (Monoco Issue System)

使用此技能在 Monoco 项目中创建和管理 **Issue** (通用原子)。

## 核心本体论 (Core Ontology)

### 1. 战略层 (Strategy)
- **🏆 EPIC (史诗)**: 宏大目标，愿景的容器。Mindset: Architect。

### 2. 价值层 (Value)
- **✨ FEATURE (特性)**: 用户视角的价值增量。Mindset: Product Owner。
- **原子性原则**: Feature = Design + Dev + Test + Doc + i18n。它们是一体的。

### 3. 执行层 (Execution)
- **🧹 CHORE (杂务)**: 工程性维护，不产生直接用户价值。Mindset: Builder。
- **🐞 FIX (修复)**: 修正偏差。Mindset: Debugger。

## 准则 (Guidelines)

### 目录结构 (Strict Enforced)
`Issues/{Type}/{status}/`

- **Type Level (Capitalized Plural)**: `Epics`, `Features`, `Chores`, `Fixes`
- **Status Level (Lowercase)**: `open`, `backlog`, `closed`

### 路径流转
使用 `monoco issue`：
1. **Create**: `monoco issue create <type> --title "..."`
2. **Transition**: `monoco issue open/close/backlog <id>`
3. **View**: `monoco issue scope`
4. **Validation**: `monoco issue lint`
5. **Modification**: `monoco issue start/submit/delete <id>`
"""

PROMPT_CONTENT = """### Issue Management
System for managing tasks using `monoco issue`.
- **Create**: `monoco issue create <type> -t "Title"` (types: epic, feature, chore, fix)
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint` (Must run after manual edits)
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`). Do not deviate.
"""

def init(issues_root: Path):
    """Initialize the Issues directory structure."""
    issues_root.mkdir(parents=True, exist_ok=True)
    
    # Standard Directories based on new Terminology
    for subdir in ["Epics", "Features", "Chores", "Fixes"]:
        (issues_root / subdir).mkdir(exist_ok=True)
        # Create status subdirs? Usually handled by open/backlog, 
        # but creating them initially is good for guidance.
        for status in ["open", "backlog", "closed"]:
            (issues_root / subdir / status).mkdir(exist_ok=True)
            
    # Create gitkeep to ensure they are tracked? Optional.

def get_resources() -> Dict[str, Any]:
    return {
        "skills": {
            "issues-management": SKILL_CONTENT
        },
        "prompts": {
            "issues-management": PROMPT_CONTENT
        }
    }


def list_issues(issues_root: Path) -> List[IssueMetadata]:
    """
    List all issues in the project.
    """
    issues = []
    for issue_type in IssueType:
        base_dir = get_issue_dir(issue_type, issues_root)
        for status_dir in ["open", "backlog", "closed"]:
            d = base_dir / status_dir
            if d.exists():
                for f in d.rglob("*.md"):
                    meta = parse_issue(f)
                    if meta:
                        issues.append(meta)
    return issues
