import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .models import IssueMetadata, IssueType, IssueStatus

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

def create_issue_file(issues_root: Path, issue_type: IssueType, title: str, parent: Optional[str] = None, status: IssueStatus = IssueStatus.OPEN, dependencies: List[str] = [], related: List[str] = [], subdir: Optional[str] = None) -> str:
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
        related=related
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
    
    # Hack: Force quotes around created_at date if it looks like YYYY-MM-DD
    yaml_header = re.sub(r"created_at: ['\"]?(\d{4}-\d{2}-\d{2})['\"]?", r'created_at: "\1"', yaml_header)

    file_content = f"""---
{yaml_header}---

## {issue_id}: {title}

## Objective

## Acceptance Criteria

## Technical Tasks

- [ ] 
"""
    (target_dir / filename).write_text(file_content)
    return issue_id

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

def update_issue_status(issues_root: Path, issue_id: str, new_status: IssueStatus, solution: Optional[IssueSolution] = None):
    path = find_issue_path(issues_root, issue_id)
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
    prefix = issue_id.split("-")[0].upper()
    base_type_dir = get_issue_dir(REVERSE_PREFIX_MAP[prefix], issues_root)
    
    # Calculate target path while preserving subdirectory structure
    try:
        # Determine relative path from the Type root (e.g. "open/Component/Sub/STORY-123.md")
        rel_path = path.relative_to(base_type_dir)
        # Remove the first component (current status directory) to get the structural path
        structure_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path(path.name)
    except ValueError:
        # Fallback if path logic fails
        structure_path = Path(path.name)

    target_path = base_type_dir / new_status.value / structure_path
        
    if path != target_path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target_path)
        
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

### 目录结构
`ISSUES/{TYPE}/{STATUS}/`
- `{TYPE}`: `Epics`, `Features`, `Chores`, `Fixes`
- `{STATUS}`: `open`, `backlog`, `closed`

### 路径流转
使用 `monoco issue`：
1. **Create**: `monoco issue create <type> --title "..."`
2. **Transition**: `monoco issue open/close/backlog <id>`
3. **View**: `monoco issue scope`
4. **Validation**: `monoco issue lint`
"""

PROMPT_CONTENT = """### Issue Management
System for managing tasks using `monoco issue`.
- **Create**: `monoco issue create <type> -t "Title"` (types: epic, feature, chore, fix)
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint` (Must run after manual edits)
- **Structure**: Issues are stored in `ISSUES/`. Do not move them manually unless you update metadata."""

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

