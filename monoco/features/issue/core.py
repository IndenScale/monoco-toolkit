import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set, Set
from datetime import datetime
from .models import IssueMetadata, IssueType, IssueStatus, IssueSolution, IssueStage, IssueDetail, IsolationType, IssueIsolation, IssueID, current_time, generate_uid
from monoco.core import git
from monoco.core.config import get_config, MonocoConfig
from monoco.core.lsp import DiagnosticSeverity
from .validator import IssueValidator

PREFIX_MAP = {
    IssueType.EPIC: "EPIC",
    IssueType.FEATURE: "FEAT",
    IssueType.CHORE: "CHORE",
    IssueType.FIX: "FIX"
}

REVERSE_PREFIX_MAP = {v: k for k, v in PREFIX_MAP.items()}

def enforce_lifecycle_policy(meta: IssueMetadata) -> None:
    """
    Apply business rules to ensure IssueMetadata consistency.
    Should be called during Create or Update (but NOT during Read/Lint).
    """
    if meta.status == IssueStatus.BACKLOG:
        meta.stage = IssueStage.FREEZED
    
    elif meta.status == IssueStatus.CLOSED:
        # Enforce stage=done for closed issues
        if meta.stage != IssueStage.DONE:
            meta.stage = IssueStage.DONE
        # Auto-fill closed_at if missing
        if not meta.closed_at:
            meta.closed_at = current_time()
    
    elif meta.status == IssueStatus.OPEN:
        # Ensure valid stage for open status
        if meta.stage is None:
            meta.stage = IssueStage.DRAFT

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
        
        data['path'] = str(file_path.absolute())
        meta = IssueMetadata(**data)
        meta.actions = get_available_actions(meta)
        return meta
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
             
        data['path'] = str(file_path.absolute())
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
        uid=generate_uid(),  # Generate global unique identifier
        type=issue_type,
        status=status,
        stage=stage,
        title=title,
        parent=parent,
        dependencies=dependencies,
        related=related,
        sprint=sprint,
        tags=tags,
        opened_at=current_time() if status == IssueStatus.OPEN else None
    )
    
    # Enforce lifecycle policies (defaults, auto-corrections)
    enforce_lifecycle_policy(metadata)

    yaml_header = yaml.dump(metadata.model_dump(exclude_none=True, mode='json'), sort_keys=False, allow_unicode=True)
    slug = _get_slug(title)
    filename = f"{issue_id}-{slug}.md"
    
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
    
    # Inject path into returned metadata
    metadata.path = str(file_path.absolute())
    
    return metadata, file_path
def get_available_actions(meta: IssueMetadata) -> List[Any]:
    from .models import IssueAction
    actions = []

    if meta.status == IssueStatus.OPEN:
        # Stage-based movements
        if meta.stage == IssueStage.DRAFT:
            actions.append(IssueAction(label="Start", target_status=IssueStatus.OPEN, target_stage=IssueStage.DOING))
            actions.append(IssueAction(label="Freeze", target_status=IssueStatus.BACKLOG))
        elif meta.stage == IssueStage.DOING:
            actions.append(IssueAction(label="Stop", target_status=IssueStatus.OPEN, target_stage=IssueStage.DRAFT))
            actions.append(IssueAction(label="Submit", target_status=IssueStatus.OPEN, target_stage=IssueStage.REVIEW))
        elif meta.stage == IssueStage.REVIEW:
            actions.append(IssueAction(label="Approve", target_status=IssueStatus.CLOSED, target_stage=IssueStage.DONE, target_solution=IssueSolution.IMPLEMENTED))
            actions.append(IssueAction(label="Reject", target_status=IssueStatus.OPEN, target_stage=IssueStage.DOING))
        elif meta.stage == IssueStage.DONE:
            actions.append(IssueAction(label="Reopen", target_status=IssueStatus.OPEN, target_stage=IssueStage.DRAFT))
            actions.append(IssueAction(label="Close", target_status=IssueStatus.CLOSED, target_stage=IssueStage.DONE, target_solution=IssueSolution.IMPLEMENTED))
        
        # Generic cancel
        actions.append(IssueAction(label="Cancel", target_status=IssueStatus.CLOSED, target_stage=IssueStage.DONE, target_solution=IssueSolution.CANCELLED))

    elif meta.status == IssueStatus.BACKLOG:
        actions.append(IssueAction(label="Pull", target_status=IssueStatus.OPEN, target_stage=IssueStage.DRAFT))
        actions.append(IssueAction(label="Cancel", target_status=IssueStatus.CLOSED, target_stage=IssueStage.DONE, target_solution=IssueSolution.CANCELLED))

    elif meta.status == IssueStatus.CLOSED:
        actions.append(IssueAction(label="Reopen", target_status=IssueStatus.OPEN, target_stage=IssueStage.DRAFT))

    return actions

def find_issue_path(issues_root: Path, issue_id: str) -> Optional[Path]:
    parsed = IssueID(issue_id)

    if not parsed.is_local:
        if not parsed.namespace:
            return None

        # Resolve Workspace
        # Traverse up from issues_root to find a config that defines the namespace
        project_root = issues_root.parent
        
        # Try current root first
        conf = MonocoConfig.load(str(project_root))
        member_rel_path = conf.project.members.get(parsed.namespace)
        
        if not member_rel_path:
            return None
            
        member_root = (project_root / member_rel_path).resolve()
        # Assume standard "Issues" directory for members to avoid loading full config
        member_issues = member_root / "Issues"
        
        if not member_issues.exists():
             return None
        
        # Recursively search in member project
        return find_issue_path(member_issues, parsed.local_id)

    # Local Search
    try:
        prefix = parsed.local_id.split("-")[0].upper()
    except IndexError:
        return None
        
    issue_type = REVERSE_PREFIX_MAP.get(prefix)
    if not issue_type:
        return None
        
    base_dir = get_issue_dir(issue_type, issues_root)
    # Search in all status subdirs recursively
    for f in base_dir.rglob(f"{parsed.local_id}-*.md"):
        return f
    return None

def update_issue(
    issues_root: Path, 
    issue_id: str, 
    status: Optional[IssueStatus] = None, 
    stage: Optional[IssueStage] = None, 
    solution: Optional[IssueSolution] = None,
    title: Optional[str] = None,
    parent: Optional[str] = None,
    sprint: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    related: Optional[List[str]] = None,
    tags: Optional[List[str]] = None
) -> IssueMetadata:
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")
        
    # Read full content
    content = path.read_text()
    
    # Split Frontmatter and Body
    match = re.search(r"^---(.*?)---\n(.*)\n", content, re.DOTALL | re.MULTILINE)
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
        # Validator will check solution presence
        current_data_stage = data.get('stage')
        
        # Policy: IMPLEMENTED requires REVIEW stage
        if effective_solution == IssueSolution.IMPLEMENTED.value:
            if current_data_stage != IssueStage.REVIEW.value:
                raise ValueError(f"Lifecycle Policy: 'Implemented' issues must be submitted for review first.\nCurrent stage: {current_data_stage}\nAction: Run `monoco issue submit {issue_id}`.")

     # Policy: No closing from DOING (General Safety)
        if current_data_stage == IssueStage.DOING.value:
             raise ValueError("Cannot close issue in progress (Doing). Please review (`monoco issue submit`) or stop (`monoco issue open`) first.")
             
        # Policy: Dependencies must be closed
        dependencies_to_check = dependencies if dependencies is not None else data.get('dependencies', [])
        if dependencies_to_check:
            for dep_id in dependencies_to_check:
                dep_path = find_issue_path(issues_root, dep_id)
                if dep_path:
                    dep_meta = parse_issue(dep_path)
                    if dep_meta and dep_meta.status != IssueStatus.CLOSED:
                        raise ValueError(f"Dependency Block: Cannot close {issue_id} because dependency {dep_id} is [Status: {dep_meta.status.value}].")
    
    # Validate new parent/dependencies/related exist
    if parent is not None and parent != "":
        if not find_issue_path(issues_root, parent):
            raise ValueError(f"Parent issue {parent} not found.")
    
    if dependencies is not None:
        for dep_id in dependencies:
            if not find_issue_path(issues_root, dep_id):
                raise ValueError(f"Dependency issue {dep_id} not found.")
    
    if related is not None:
        for rel_id in related:
            if not find_issue_path(issues_root, rel_id):
                raise ValueError(f"Related issue {rel_id} not found.")
            
    # Update Data
    if status:
        data['status'] = status.value

    if stage:
        data['stage'] = stage.value
    if solution:
        data['solution'] = solution.value
    
    if title:
        data['title'] = title

    if parent is not None:
        if parent == "":
            data.pop('parent', None)  # Remove parent field
        else:
            data['parent'] = parent

    if sprint is not None:
        data['sprint'] = sprint
    
    if dependencies is not None:
        data['dependencies'] = dependencies
    
    if related is not None:
        data['related'] = related
    
    if tags is not None:
        data['tags'] = tags
    
    # Lifecycle Hooks
    # 1. Opened At: If transitioning to OPEN
    if target_status == IssueStatus.OPEN and current_status != IssueStatus.OPEN:
        # Only set if not already set? Or always reset?
        # Let's set it if not present, or update it to reflect "Latest activation"
        # FEAT-0012 says: "update opened_at to now"
        data['opened_at'] = current_time()
    
    # 2. Backlog Push: Handled by IssueMetadata.validate_lifecycle (Status=Backlog -> Stage=None)
    # 3. Closed: Handled by IssueMetadata.validate_lifecycle (Status=Closed -> Stage=Done, ClosedAt=Now)

    # Touch updated_at
    data['updated_at'] = current_time()
    
    # Re-hydrate through Model
    try:
        updated_meta = IssueMetadata(**data)
        
        # Enforce lifecycle policies (defaults, auto-corrections)
        # This ensures that when we update, we also fix invalid states (like Closed but not Done)
        enforce_lifecycle_policy(updated_meta)

        # Delegate to IssueValidator for static state validation
        # We need to construct the full content to validate body-dependent rules (like checkboxes)
        # Note: 'body' here is the OLD body. We assume update_issue doesn't change body.
        # If body is invalid (unchecked boxes) and we move to DONE, this MUST fail.
        validator = IssueValidator(issues_root)
        diagnostics = validator.validate(updated_meta, body)
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        if errors:
             raise ValueError(f"Validation Failed: {errors[0].message}")

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
            path = target_path # Update local path variable for returned meta

    # Hook: Recursive Aggregation (FEAT-0003)
    if updated_meta.parent:
        recalculate_parent(issues_root, updated_meta.parent)
    
    # Update returned metadata with final absolute path
    updated_meta.path = str(path.absolute())
    updated_meta.actions = get_available_actions(updated_meta)
    return updated_meta

def start_issue_isolation(issues_root: Path, issue_id: str, mode: IsolationType, project_root: Path) -> IssueMetadata:
    """
    Start physical isolation for an issue (Branch or Worktree).
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")

    issue = parse_issue(path)
    if not issue:
        raise ValueError(f"Could not parse metadata for issue {issue_id}")
    
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
        data['updated_at'] = current_time()

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
    if not issue:
        raise ValueError(f"Could not parse metadata for issue {issue_id}")
        
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
            data['updated_at'] = current_time()
            
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
        "prompts": {} # Handled by adapter via resource files
    }


def list_issues(issues_root: Path, recursive_workspace: bool = False) -> List[IssueMetadata]:
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

    if recursive_workspace:
        # Resolve Workspace Members
        try:
            # weak assumption: issues_root.parent is project_root
            project_root = issues_root.parent
            conf = get_config(str(project_root))
            
            for name, rel_path in conf.project.members.items():
                member_root = (project_root / rel_path).resolve()
                member_issues_dir = member_root / "Issues" # Standard convention
                
                if member_issues_dir.exists():
                    # Fetch member issues (non-recursive to avoid loops)
                    member_issues = list_issues(member_issues_dir, False)
                    for m in member_issues:
                        # Namespace the ID to avoid collisions and indicate origin
                        m.id = f"{name}::{m.id}"
                        issues.append(m)
        except Exception:
            # Fail silently on workspace resolution errors (config missing etc)
            pass

    return issues

def get_board_data(issues_root: Path) -> Dict[str, List[IssueMetadata]]:
    """
    Get open issues grouped by their stage for Kanban view.
    """
    board = {
        IssueStage.DRAFT.value: [],
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
        meta = parse_issue(path)
        if not meta:
            raise ValueError(f"Could not parse metadata for issue {issue_id}")
        return meta
        
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
    
    meta = parse_issue(path)
    if not meta:
         raise ValueError(f"Could not parse metadata for issue {issue_id}")
    return meta

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

def parse_search_query(query: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Parse a search query string into explicit positives, optional terms, and negatives.
    Supported syntax:
      - `+term`: Must include (AND)
      - `-term`: Must not include (NOT)
      - `term`: Optional (Nice to have) - OR logic if no +term exists
      - `"phrase with space"`: Quoted match
    """
    if not query:
        return [], [], []
        
    import shlex
    try:
        tokens = shlex.split(query)
    except ValueError:
        # Fallback for unbalanced quotes
        tokens = query.split()

    explicit_positives = []
    terms = []
    negatives = []
    
    for token in tokens:
        token_lower = token.lower()
        if token_lower.startswith("-") and len(token_lower) > 1:
            negatives.append(token_lower[1:])
        elif token_lower.startswith("+") and len(token_lower) > 1:
            explicit_positives.append(token_lower[1:])
        else:
            terms.append(token_lower)
            
    return explicit_positives, terms, negatives

def check_issue_match(issue: IssueMetadata, explicit_positives: List[str], terms: List[str], negatives: List[str], full_content: str = "") -> bool:
    """
    Check if an issue matches the search criteria.
    Consider fields: id, title, status, stage, type, tags, dependencies, related.
    Optional: full_content (body) if available.
    """
    # 1. Aggregate Searchable Text
    # We join all fields with spaces to create a searchable blob
    searchable_parts = [
        issue.id,
        issue.title,
        issue.status.value,
        issue.type.value,
        str(issue.stage.value) if issue.stage else "",
        *(issue.tags or []),
        *(issue.dependencies or []),
        *(issue.related or []),
        full_content
    ]
    
    # Normalize blob
    blob = " ".join(filter(None, searchable_parts)).lower()
    
    # 2. Check Negatives (Fast Fail)
    for term in negatives:
        if term in blob:
            return False
            
    # 3. Check Explicit Positives (Must match ALL)
    for term in explicit_positives:
        if term not in blob:
            return False
            
    # 4. Check Terms (Nice to Have)
    # If explicit_positives exist, terms are optional (implicit inclusion).
    # If NO explicit_positives, terms act as Implicit OR (must match at least one).
    if terms:
        if not explicit_positives:
             # Must match at least one term
             if not any(term in blob for term in terms):
                 return False
        
    return True

def search_issues(issues_root: Path, query: str) -> List[IssueMetadata]:
    """
    Search issues using advanced query syntax.
    Returns list of matching IssueMetadata.
    """
    explicit_positives, terms, negatives = parse_search_query(query)
    
    # Optimization: If no query, return empty? Or all?
    # Usually search implies input. CLI `list` is for all.
    # But if query is empty string, we return all?
    # Let's align with "grep": empty pattern matches everything? 
    # Or strict: empty query -> all.
    if not explicit_positives and not terms and not negatives:
         return list_issues(issues_root)

    matches = []
    all_files = []
    
    # 1. Gather all files first (we need to read content for deep search)
    # Using list_issues is inefficient if we need body content, as list_issues only parses frontmatter (usually).
    # But parse_issue uses `IssueMetadata` which ignores body.
    # We need a robust way. `parse_issue` reads full text but discards body in current implementation?
    # Wait, `parse_issue` in core.py *only* reads frontmatter via `yaml.safe_load(match.group(1))`.
    # It does NOT return body.
    
    # To support deep search (Body), we need to read files.
    # Let's iterate files directly.
    
    for issue_type in IssueType:
        base_dir = get_issue_dir(issue_type, issues_root)
        for status_dir in ["open", "backlog", "closed"]:
            d = base_dir / status_dir
            if d.exists():
                for f in d.rglob("*.md"):
                    all_files.append(f)

    for f in all_files:
        # We need full content for body search
        try:
            content = f.read_text()
            # Parse Metadata
            match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
            if not match:
                continue
            
            yaml_str = match.group(1)
            data = yaml.safe_load(yaml_str)
            if not isinstance(data, dict):
                 continue
            
            meta = IssueMetadata(**data)
            
            # Match
            if check_issue_match(meta, explicit_positives, terms, negatives, full_content=content):
                matches.append(meta)
                
        except Exception:
            continue
            
    return matches

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
        current_stage = data.get("stage", "draft").lower()
        
        if current_status == "open" and current_stage == "draft":
            # Check if any child is active
            active_children = [c for c in children if c.status == IssueStatus.OPEN and c.stage != IssueStage.DRAFT]
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

def move_issue(
    source_issues_root: Path,
    issue_id: str,
    target_issues_root: Path,
    renumber: bool = False
) -> Tuple[IssueMetadata, Path]:
    """
    Move an issue from one project to another.
    
    Args:
        source_issues_root: Source project's Issues directory
        issue_id: ID of the issue to move
        target_issues_root: Target project's Issues directory
        renumber: If True, automatically renumber on ID conflict
        
    Returns:
        Tuple of (updated metadata, new file path)
        
    Raises:
        FileNotFoundError: If source issue doesn't exist
        ValueError: If ID conflict exists and renumber=False
    """
    # 1. Find source issue
    source_path = find_issue_path(source_issues_root, issue_id)
    if not source_path:
        raise FileNotFoundError(f"Issue {issue_id} not found in source project.")
    
    # 2. Parse issue metadata
    issue = parse_issue_detail(source_path)
    if not issue:
        raise ValueError(f"Failed to parse issue {issue_id}.")
    
    # 3. Check for ID conflict in target
    target_conflict_path = find_issue_path(target_issues_root, issue_id)
    
    if target_conflict_path:
        # Conflict detected
        conflict_issue = parse_issue(target_conflict_path)
        
        # Check if it's the same issue (same UID)
        if issue.uid and conflict_issue and conflict_issue.uid == issue.uid:
            raise ValueError(
                f"Issue {issue_id} (uid: {issue.uid}) already exists in target project. "
                "This appears to be a duplicate."
            )
        
        # Different issues with same ID
        if not renumber:
            conflict_info = ""
            if conflict_issue:
                conflict_info = f" (uid: {conflict_issue.uid}, created: {conflict_issue.created_at}, stage: {conflict_issue.stage})"
            raise ValueError(
                f"ID conflict: Target project already has {issue_id}{conflict_info}.\n"
                f"Use --renumber to automatically assign a new ID."
            )
        
        # Auto-renumber
        new_id = find_next_id(issue.type, target_issues_root)
        old_id = issue.id
        issue.id = new_id
    else:
        new_id = issue.id
        old_id = issue.id
    
    # 4. Construct target path
    target_type_dir = get_issue_dir(issue.type, target_issues_root)
    target_status_dir = target_type_dir / issue.status.value
    
    # Preserve subdirectory structure if any
    try:
        source_type_dir = get_issue_dir(issue.type, source_issues_root)
        rel_path = source_path.relative_to(source_type_dir)
        # Remove status directory component
        structure_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path(source_path.name)
    except ValueError:
        structure_path = Path(source_path.name)
    
    # Update filename if ID changed
    if new_id != old_id:
        old_filename = source_path.name
        new_filename = old_filename.replace(old_id, new_id, 1)
        structure_path = structure_path.parent / new_filename if structure_path.parent != Path('.') else Path(new_filename)
    
    target_path = target_status_dir / structure_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 5. Update content if ID changed
    if new_id != old_id:
        # Update frontmatter
        content = issue.raw_content or ""
        match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
        if match:
            yaml_str = match.group(1)
            data = yaml.safe_load(yaml_str) or {}
            data['id'] = new_id
            data['updated_at'] = current_time()
            
            new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
            
            # Update body (replace old ID in heading)
            body = content[match.end():]
            body = body.replace(f"## {old_id}:", f"## {new_id}:", 1)
            
            new_content = f"---\n{new_yaml}---{body}"
        else:
            new_content = issue.raw_content or ""
    else:
        new_content = issue.raw_content or ""
    
    # 6. Write to target
    target_path.write_text(new_content)
    
    # 7. Remove source
    source_path.unlink()
    
    # 8. Return updated metadata
    final_meta = parse_issue(target_path)
    if not final_meta:
        raise ValueError(f"Failed to parse moved issue at {target_path}")
        
    return final_meta, target_path
