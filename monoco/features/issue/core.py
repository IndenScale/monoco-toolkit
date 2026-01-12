import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set, Set
from datetime import datetime
from .models import IssueMetadata, IssueType, IssueStatus, IssueSolution, IssueStage, IssueDetail, IsolationType, IssueIsolation
from monoco.core import git

PREFIX_MAP = {
    IssueType.EPIC: "EPIC",
    IssueType.FEATURE: "FEAT",
    IssueType.CHORE: "CHORE",
    IssueType.FIX: "FIX"
}

REVERSE_PREFIX_MAP = {v: k for k, v in PREFIX_MAP.items()}

def _get_slug(title: str) -> str:
    slug = title.lower()
    # Replace non-word characters (including punctuation, spaces) with hyphens
    # \w matches Unicode word characters (letters, numbers, underscores)
    slug = re.sub(r"[^\w]+", "-", slug)
    slug = slug.strip("-")[:50]
    
    if not slug:
        slug = "issue"
        
    return slug

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

def parse_issue_detail(file_path: Path) -> Optional[IssueDetail]:
    if not file_path.suffix == ".md":
        return None
    
    content = file_path.read_text()
    # Robust splitting
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if not match:
        return None
        
    yaml_str = match.group(1)
    body = content[match.end():].lstrip()
    
    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
             return None
        return IssueDetail(**data, body=body, raw_content=content)
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
    stage: Optional[IssueStage] = None,
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
        stage=stage,
        title=title,
        parent=parent,
        dependencies=dependencies,
        related=related,
        sprint=sprint,
        tags=tags,
        opened_at=datetime.now() if status == IssueStatus.OPEN else None
    )
    
    yaml_header = yaml.dump(metadata.model_dump(exclude_none=True, mode='json'), sort_keys=False, allow_unicode=True)
    slug = _get_slug(title)
    filename = f"{issue_id}-{slug}.md"
    
    file_content = f"""
---
{yaml_header}---

## {issue_id}: {title}

## Objective

## Acceptance Criteria

## Technical Tasks

- [ ] 
"""
    file_path = target_dir / filename
    file_path.write_text(file_content)
def validate_transition(
    current_status: IssueStatus,
    current_stage: Optional[IssueStage],
    target_status: IssueStatus,
    target_stage: Optional[IssueStage],
    target_solution: Optional[str],
    issue_dependencies: List[str],
    issues_root: Path,
    issue_id: str
):
    """
    Centralized validation logic for state transitions.
    """
    # Policy: Prevent Backlog -> Review
    if target_stage == IssueStage.REVIEW and current_status == IssueStatus.BACKLOG:
         raise ValueError(f"Lifecycle Policy: Cannot submit Backlog issue directly. Run `monoco issue pull {issue_id}` first.")

    if target_status == IssueStatus.CLOSED:
        if not target_solution:
            raise ValueError(f"Closing an issue requires a solution. Please provide --solution or edit the file metadata.")
            
        # Policy: IMPLEMENTED requires REVIEW stage (unless we are already in REVIEW)
        # Check current stage.
        if target_solution == IssueSolution.IMPLEMENTED.value:
            # If we are transitioning FROM Review, it's fine.
            # If we are transitioning TO Closed, current stage must be Review.
            if current_stage != IssueStage.REVIEW:
                raise ValueError(f"Lifecycle Policy: 'Implemented' issues must be submitted for review first.\nCurrent stage: {current_stage}\nAction: Run `monoco issue submit {issue_id}`.")

        # Policy: No closing from DOING (General Safety)
        if current_stage == IssueStage.DOING:
             raise ValueError("Cannot close issue in progress (Doing). Please review (`monoco issue submit`) or stop (`monoco issue open`) first.")
             
        # Policy: Dependencies must be closed
        if issue_dependencies:
            for dep_id in issue_dependencies:
                dep_path = find_issue_path(issues_root, dep_id)
                if dep_path:
                    dep_meta = parse_issue(dep_path)
                    if dep_meta and dep_meta.status != IssueStatus.CLOSED:
                        raise ValueError(f"Dependency Block: Cannot close {issue_id} because dependency {dep_id} is not closed.")

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
    match = re.search(r"^---(.*?)---\n(.*)$\n", content, re.DOTALL | re.MULTILINE)
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
    effective_solution = solution.value if solution else data.get("solution")
    
    # Policy: Prevent Backlog -> Review
    if stage == IssueStage.REVIEW and current_status == IssueStatus.BACKLOG:
         raise ValueError(f"Lifecycle Policy: Cannot submit Backlog issue directly. Run `monoco issue pull {issue_id}` first.")

    if target_status == IssueStatus.CLOSED:
        if not effective_solution:
            raise ValueError(f"Closing an issue requires a solution. Please provide --solution or edit the file metadata.")
            
        current_data_stage = data.get('stage')
        
        # Policy: IMPLEMENTED requires REVIEW stage
        if effective_solution == IssueSolution.IMPLEMENTED.value:
            if current_data_stage != IssueStage.REVIEW.value:
                raise ValueError(f"Lifecycle Policy: 'Implemented' issues must be submitted for review first.\nCurrent stage: {current_data_stage}\nAction: Run `monoco issue submit {issue_id}`.")

     # Policy: No closing from DOING (General Safety)
        if current_data_stage == IssueStage.DOING.value:
             raise ValueError("Cannot close issue in progress (Doing). Please review (`monoco issue submit`) or stop (`monoco issue open`) first.")
             
        # Policy: Dependencies must be closed
        dependencies = data.get('dependencies', [])
        if dependencies:
            for dep_id in dependencies:
                dep_path = find_issue_path(issues_root, dep_id)
                if dep_path:
                    dep_meta = parse_issue(dep_path)
                    if dep_meta and dep_meta.status != IssueStatus.CLOSED:
                        raise ValueError(f"Dependency Block: Cannot close {issue_id} because dependency {dep_id} is [Status: {dep_meta.status.value}].")
            
    # Update Data
    if status:
        data['status'] = status.value

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
    if not match_header:
        body_content = body
    else:
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
            structure_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path(path.name)
        except ValueError:
            structure_path = Path(path.name)

        target_path = base_type_dir / target_status.value / structure_path
            
        if path != target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target_path)

    # Hook: Recursive Aggregation (FEAT-0003)
    if updated_meta.parent:
        recalculate_parent(issues_root, updated_meta.parent)
        
    return updated_meta

def start_issue_isolation(issues_root: Path, issue_id: str, mode: IsolationType, project_root: Path) -> IssueMetadata:
    """
    Start physical isolation for an issue (Branch or Worktree).
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")

    issue = parse_issue(path)
    
    # Idempotency / Conflict Check
    if issue.isolation:
        if issue.isolation.type == mode:
             # Already isolated in same mode, maybe just switch context?
             # For now, we just warn or return.
             # If branch exists, we make sure it's checked out in CLI layer maybe?
             # But here we assume we want to setup metadata.
             pass
        else:
             raise ValueError(f"Issue {issue_id} is already isolated as '{issue.isolation.type}'. Please cleanup first.")

    slug = _get_slug(issue.title)
    branch_name = f"feat/{issue_id.lower()}-{slug}" 
    
    isolation_meta = None

    if mode == IsolationType.BRANCH:
        if not git.branch_exists(project_root, branch_name):
            git.create_branch(project_root, branch_name, checkout=True)
        else:
            # Check if we are already on it? 
            # If not, checkout.
            current = git.get_current_branch(project_root)
            if current != branch_name:
                git.checkout_branch(project_root, branch_name)
        
        isolation_meta = IssueIsolation(type=IsolationType.BRANCH, ref=branch_name)

    elif mode == IsolationType.WORKTREE:
        wt_path = project_root / ".monoco" / "worktrees" / f"{issue_id.lower()}-{slug}"
        
        # Check if worktree exists physically
        if wt_path.exists():
             # Check if valid git worktree?
             pass
        else:
             wt_path.parent.mkdir(parents=True, exist_ok=True)
             git.worktree_add(project_root, branch_name, wt_path)
             
        isolation_meta = IssueIsolation(type=IsolationType.WORKTREE, ref=branch_name, path=str(wt_path))
    
    # Persist Metadata
    # We load raw, update isolation field, save.
    content = path.read_text()
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if match:
        yaml_str = match.group(1)
        data = yaml.safe_load(yaml_str) or {}
        
        data['isolation'] = isolation_meta.model_dump(mode='json')
        # Also ensure stage is DOING (logic link)
        data['stage'] = IssueStage.DOING.value
        data['updated_at'] = datetime.now()

        new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
        new_content = content.replace(match.group(1), "\n" + new_yaml)
        path.write_text(new_content)
        
        return IssueMetadata(**data)
        
    return issue

def prune_issue_resources(issues_root: Path, issue_id: str, force: bool, project_root: Path) -> List[str]:
    """
    Cleanup physical resources. Returns list of actions taken.
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        # Issue might be deleted?
        # If we can't find issue, we can't read metadata to know what to prune.
        # We rely on CLI to pass context or we fail.
        raise FileNotFoundError(f"Issue {issue_id} not found.")
        
    issue = parse_issue(path)
    deleted_items = []

    if not issue.isolation:
        return []

    if issue.isolation.type == IsolationType.BRANCH:
        branch = issue.isolation.ref
        current = git.get_current_branch(project_root)
        if current == branch:
             raise RuntimeError(f"Cannot delete active branch '{branch}'. Please checkout 'main' first.")
        
        if git.branch_exists(project_root, branch):
            git.delete_branch(project_root, branch, force=force)
            deleted_items.append(f"branch:{branch}")
            
    elif issue.isolation.type == IsolationType.WORKTREE:
        wt_path_str = issue.isolation.path
        if wt_path_str:
            wt_path = Path(wt_path_str)
            # Normalize path if relative
            if not wt_path.is_absolute():
                wt_path = project_root / wt_path
            
            if wt_path.exists():
                git.worktree_remove(project_root, wt_path, force=force)
                deleted_items.append(f"worktree:{wt_path.name}")
            
            # Also delete the branch associated? 
            # Worktree create makes a branch. When removing worktree, branch remains.
            # Usually we want to remove the branch too if it was created for this issue.
            branch = issue.isolation.ref
            if branch and git.branch_exists(project_root, branch):
                 # We can't delete branch if it is checked out in the worktree we just removed?
                 # git worktree remove unlocks the branch.
                 git.delete_branch(project_root, branch, force=force)
                 deleted_items.append(f"branch:{branch}")

    # Clear Metadata
    content = path.read_text()
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if match:
        yaml_str = match.group(1)
        data = yaml.safe_load(yaml_str) or {}
        
        if 'isolation' in data:
            del data['isolation']
            data['updated_at'] = datetime.now()
            
            new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
            new_content = content.replace(match.group(1), "\n" + new_yaml)
            path.write_text(new_content)
            
    return deleted_items



def delete_issue_file(issues_root: Path, issue_id: str):
    """
    Physical removal of an issue file.
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")
    
    path.unlink()
        
# Resources
SKILL_CONTENT = """
---
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

PROMPT_CONTENT = """
### Issue Management
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

def get_board_data(issues_root: Path) -> Dict[str, List[IssueMetadata]]:
    """
    Get open issues grouped by their stage for Kanban view.
    """
    board = {
        IssueStage.TODO.value: [],
        IssueStage.DOING.value: [],
        IssueStage.REVIEW.value: [],
        IssueStage.DONE.value: []
    }
    
    issues = list_issues(issues_root)
    for issue in issues:
        if issue.status == IssueStatus.OPEN and issue.stage:
            stage_val = issue.stage.value
            if stage_val in board:
                board[stage_val].append(issue)
        elif issue.status == IssueStatus.CLOSED:
            # Optionally show recently closed items in DONE column
            board[IssueStage.DONE.value].append(issue)
            
    return board

def validate_issue_integrity(meta: IssueMetadata, all_issue_ids: Set[str] = set()) -> List[str]:
    """
    Validate metadata integrity (Solution, Lifecycle, etc.)
    UI-agnostic.
    """
    errors = []
    if meta.status == IssueStatus.CLOSED and not meta.solution:
        errors.append(f"Solution Missing: {meta.id} is closed but has no solution field.")
            
    if meta.parent:
        if all_issue_ids and meta.parent not in all_issue_ids:
             errors.append(f"Broken Link: {meta.id} refers to non-existent parent {meta.parent}.")

    if meta.status == IssueStatus.BACKLOG and meta.stage != IssueStage.FREEZED:
        errors.append(f"Lifecycle Error: {meta.id} is backlog but stage is not freezed (found: {meta.stage}).")
        
    return errors

def update_issue_content(issues_root: Path, issue_id: str, new_content: str) -> IssueMetadata:
    """
    Update the raw content of an issue file.
    Validates integrity before saving.
    Handles file moves if status changes.
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")

    # 1. Parse New Content (using temp file to reuse parse_issue logic)
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as tmp:
        tmp.write(new_content)
        tmp_path = Path(tmp.name)
        
    try:
        meta = parse_issue(tmp_path)
        if not meta:
             raise ValueError("Invalid Issue Content: Frontmatter missing or invalid.")
        
        if meta.id != issue_id:
             raise ValueError(f"Cannot change Issue ID (Original: {issue_id}, New: {meta.id})")

        # 2. Integrity Check
        errors = validate_issue_integrity(meta)
        if errors:
            raise ValueError(f"Validation Failed: {'; '.join(errors)}")
            
        # 3. Write and Move
        # We overwrite the *current* path first
        path.write_text(new_content)
        
        # Check if we need to move (Status Change)
        # We need to re-derive the expected path based on new status
        # Reuse logic from update_issue (simplified)
        
        prefix = issue_id.split("-")[0].upper()
        base_type_dir = get_issue_dir(REVERSE_PREFIX_MAP[prefix], issues_root)
        
        # Calculate structure path (preserve subdir)
        try:
            rel_path = path.relative_to(base_type_dir)
            # Remove the first component (current status directory) which might be 'open', 'closed' etc.
            # But wait, find_issue_path found it. 'rel_path' includes status dir.
            # e.g. open/Backend/Auth/FEAT-123.md -> parts=('open', 'Backend', 'Auth', 'FEAT-123.md')
            structure_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path(path.name)
        except ValueError:
            # Fallback if path is weird
            structure_path = Path(path.name)

        target_path = base_type_dir / meta.status.value / structure_path
            
        if path != target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target_path)
            
        return meta

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def generate_delivery_report(issues_root: Path, issue_id: str, project_root: Path) -> IssueMetadata:
    """
    Scan git history for commits related to this issue (Ref: ID),
    aggregate touched files, and append/update '## Delivery' section in the issue body.
    """
    from monoco.core import git
    
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")

    # 1. Scan Git
    commits = git.search_commits_by_message(project_root, f"Ref: {issue_id}")
    
    if not commits:
        return parse_issue(path)
        
    # 2. Aggregate Data
    all_files = set()
    commit_list_md = []
    
    for c in commits:
        short_hash = c['hash'][:7]
        commit_list_md.append(f"- `{short_hash}` {c['subject']}")
        for f in c['files']:
            all_files.add(f)
            
    sorted_files = sorted(list(all_files))
    
    # 3. Format Report
    delivery_section = f"""
## Delivery
<!-- Monoco Auto Generated -->
**Commits ({len(commits)})**:
{chr(10).join(commit_list_md)}

**Touched Files ({len(sorted_files)})**:
""" + "\n".join([f"- `{f}`" for f in sorted_files])

    # 4. Update File Content
    content = path.read_text()
    
    # Check if Delivery section exists
    if "## Delivery" in content:
        # Replace existing section
        # We assume Delivery is the last section or we replace until end or next H2?
        # For simplicity, if ## Delivery exists, we regex replace it and everything after it 
        # OR we just replace the section block if we can identify it.
        # Let's assume it's at the end or we replace the specific block `## Delivery...`
        # But regex matching across newlines is tricky if we don't know where it ends.
        # Safe bet: If "## Delivery" exists, find it and replace everything after it?
        # Or look for "<!-- Monoco Auto Generated -->"
        
        pattern = r"## Delivery.*"
        # If we use DOTALL, it replaces everything until end of string?
        # Yes, usually Delivery report is appended at the end.
        content = re.sub(pattern, delivery_section.strip(), content, flags=re.DOTALL)
    else:
        # Append
        if not content.endswith("\n"):
            content += "\n"
        content += "\n" + delivery_section.strip() + "\n"
        
    path.write_text(content)
    
    # 5. Update Metadata (delivery stats)
    # We might want to store 'files_count' in metadata for the recursive aggregation (FEAT-0003)
    # But IssueMetadata doesn't have a 'delivery' dict field yet.
    # We can add it to 'extra' or extend the model later.
    # For now, just persisting the text is enough for FEAT-0002.
    
    return parse_issue(path)

def get_children(issues_root: Path, parent_id: str) -> List[IssueMetadata]:
    """Find all direct children of an issue."""
    all_issues = list_issues(issues_root)
    return [i for i in all_issues if i.parent == parent_id]

def count_files_in_delivery(issue_path: Path) -> int:
    """Parse the ## Delivery section to count files."""
    try:
        content = issue_path.read_text()
        match = re.search(r"\*\*Touched Files \((\d+)\)\*\*", content)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 0

def recalculate_parent(issues_root: Path, parent_id: str):
    """
    Update parent Epic/Feature stats based on children.
    - Progress (Closed/Total)
    - Total Files Touched (Sum of children's delivery)
    """
    parent_path = find_issue_path(issues_root, parent_id)
    if not parent_path:
        return # Should we warn?
        
    children = get_children(issues_root, parent_id)
    if not children:
        return

    total = len(children)
    closed = len([c for c in children if c.status == IssueStatus.CLOSED])
    # Progress string: "3/5"
    progress_str = f"{closed}/{total}"
    
    # Files count
    total_files = 0
    for child in children:
        child_path = find_issue_path(issues_root, child.id)
        if child_path:
            total_files += count_files_in_delivery(child_path)

    # Update Parent    # We need to reuse update logic but without validation/status change
    # Just generic metadata update.
    # update_issue is too heavy/strict. 
    # Let's implement a lighter `patch_metadata` helper or reuse logic. 
    
    content = parent_path.read_text()
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if match:
        yaml_str = match.group(1)
        data = yaml.safe_load(yaml_str) or {}
        
        # Check if changed to avoid churn
        old_progress = data.get("progress")
        old_files = data.get("files_count")
        
        if old_progress == progress_str and old_files == total_files:
            return
            
        data["progress"] = progress_str
        data["files_count"] = total_files
        
        # Also maybe update status?
        # FEAT-0003 Req: "If first child starts doing, auto-start Parent?"
        # If parent is OPEN/TODO and child is DOING/REVIEW/DONE, set parent to DOING?
        current_status = data.get("status", "open").lower()
        current_stage = data.get("stage", "todo").lower()
        
        if current_status == "open" and current_stage == "todo":
            # Check if any child is active
            active_children = [c for c in children if c.status == IssueStatus.OPEN and c.stage != IssueStage.TODO]
            closed_children = [c for c in children if c.status == IssueStatus.CLOSED]
            
            if active_children or closed_children:
                data["stage"] = "doing"
        
        # Serialize
        new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
        # Replace header
        new_content = content.replace(match.group(1), "\n" + new_yaml)
        parent_path.write_text(new_content)
        
        # Recurse up?
        parent_parent = data.get("parent")
        if parent_parent:
            recalculate_parent(issues_root, parent_parent)
