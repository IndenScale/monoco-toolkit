import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set, Set
from .models import (
    IssueMetadata,
    IssueType,
    IssueStatus,
    IssueSolution,
    IssueStage,
    IssueDetail,
    IsolationType,
    IssueIsolation,
    IssueID,
    current_time,
    generate_uid,
)
from .criticality import (
    CriticalityLevel,
    CriticalityTypeMapping,
    CriticalityInheritanceService,
)
from monoco.core import git
from monoco.core.config import get_config, MonocoConfig
from monoco.core.lsp import DiagnosticSeverity
from .validator import IssueValidator

from .engine import get_engine
from .git_service import IssueGitService


def get_prefix_map(issues_root: Path) -> Dict[str, str]:
    engine = get_engine(str(issues_root.parent))
    return engine.get_prefix_map()


def get_reverse_prefix_map(issues_root: Path) -> Dict[str, str]:
    prefix_map = get_prefix_map(issues_root)
    return {v: k for k, v in prefix_map.items()}


def get_issue_dir(issue_type: str, issues_root: Path) -> Path:
    engine = get_engine(str(issues_root.parent))
    folder_map = engine.get_folder_map()
    folder = folder_map.get(issue_type, issue_type.capitalize() + "s")
    return issues_root / folder


def _parse_isolation_ref(ref: str) -> str:
    """
    Parse isolation ref and strip any 'branch:' or 'worktree:' prefix.
    
    The isolation.ref field may contain prefixes like 'branch:feat/xxx' or 'worktree:xxx'
    for display/logging purposes, but git commands need the raw branch name.
    
    Args:
        ref: The isolation ref string, may contain prefix
        
    Returns:
        The clean branch name without prefix
    """
    if not ref:
        return ref
    
    # Strip known prefixes
    for prefix in ("branch:", "worktree:"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    
    return ref


def _get_slug(title: str) -> str:
    slug = title.lower()
    # Replace non-word characters (including punctuation, spaces) with hyphens
    # \w matches Unicode word characters (letters, numbers, underscores)
    slug = re.sub(r"[^\w]+", "-", slug)
    slug = slug.strip("-")[:50]

    if not slug:
        slug = "issue"

    return slug


def _unquote_git_path(path: str) -> str:
    """
    Decode Git C-quoting format paths to native strings.

    Git uses C-quoting for paths containing non-ASCII characters or special characters:
    - Wraps the path in double quotes: "path"
    - Escapes bytes as octal: \351\207\215 represents UTF-8 bytes

    Args:
        path: Path string, potentially in Git C-quoting format

    Returns:
        Decoded native path string

    Examples:
        >>> _unquote_git_path('"path-\\351\\207\\215.md"')
        'path-重.md'
        >>> _unquote_git_path('"path\\ with\\ space.md"')
        'path with space.md'
        >>> _unquote_git_path('normal/path.md')
        'normal/path.md'
    """
    path = path.strip()

    # Check if the path is wrapped in double quotes (C-quoting format)
    if not (path.startswith('"') and path.endswith('"')):
        return path

    # Remove outer quotes
    path = path[1:-1]

    # Collect all bytes (octal escapes -> bytes, ASCII chars -> their byte values)
    bytes_list = []
    i = 0
    while i < len(path):
        if path[i] == '\\' and i + 3 < len(path) and path[i+1:i+4].isdigit():
            # This is an octal escape sequence (e.g., \351)
            byte_val = int(path[i+1:i+4], 8)
            bytes_list.append(byte_val)
            i += 4
        else:
            # Regular ASCII character
            bytes_list.append(ord(path[i]))
            i += 1

    # Decode the entire byte sequence as UTF-8
    return bytes(bytes_list).decode('utf-8')


def parse_issue(file_path: Path, raise_error: bool = False) -> Optional[IssueMetadata]:
    if not file_path.suffix == ".md":
        return None

    content = file_path.read_text()
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if not match:
        if raise_error:
            raise ValueError(f"No frontmatter found in {file_path.name}")
        return None

    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            if raise_error:
                raise ValueError(f"Frontmatter is not a dictionary in {file_path.name}")
            return None

        data["path"] = str(file_path.absolute())
        meta = IssueMetadata(**data)
        meta.actions = get_available_actions(meta)
        return meta
    except Exception as e:
        if raise_error:
            raise e
        return None


def _serialize_metadata(metadata: IssueMetadata) -> str:
    """
    Centralized serialization logic to ensure explicit fields and correct ordering.
    """
    # Serialize metadata
    # We want explicit fields even if None/Empty to enforce schema awareness
    data = metadata.model_dump(
        exclude_none=True, mode="json", exclude={"actions", "path"}
    )

    # Force explicit keys if missing (due to exclude_none or defaults)
    if "parent" not in data:
        data["parent"] = None
    if "dependencies" not in data:
        data["dependencies"] = []
    if "related" not in data:
        data["related"] = []
    if "domains" not in data:
        data["domains"] = []
    if "files" not in data:
        data["files"] = []
    if "solution" not in data:
        data["solution"] = None

    # Custom YAML Dumper to preserve None as 'null' and order
    # Helper to order keys: id, uid, type, status, stage, title, ... graph ...
    # Simple sort isn't enough, we rely on insertion order (Python 3.7+)
    ordered_data = {
        k: data[k]
        for k in [
            "id",
            "uid",
            "type",
            "status",
            "stage",
            "title",
            "created_at",
            "updated_at",
        ]
        if k in data
    }
    # Add graph fields
    for k in [
        "priority",
        "parent",
        "dependencies",
        "related",
        "domains",
        "tags",
        "files",
    ]:
        if k in data:
            ordered_data[k] = data[k]
        elif k in ["dependencies", "related", "domains", "tags", "files"]:
            ordered_data[k] = []
        elif k == "parent":
            ordered_data[k] = None

    # Add criticality if present
    if "criticality" in data:
        ordered_data["criticality"] = data["criticality"]

    # Add solution if present (for template generation)
    if "solution" in data:
        ordered_data["solution"] = data["solution"]

    # Add remaining
    for k, v in data.items():
        if k not in ordered_data:
            ordered_data[k] = v

    yaml_header = yaml.dump(
        ordered_data, sort_keys=False, allow_unicode=True, default_flow_style=False
    )

    # Inject Comments for guidance (replace keys with key+comment)
    if "parent" in ordered_data and ordered_data["parent"] is None:
        yaml_header = yaml_header.replace(
            "parent: null", "parent: null # <EPIC-ID> Optional"
        )
    if "solution" in ordered_data and ordered_data["solution"] is None:
        yaml_header = yaml_header.replace(
            "solution: null", "solution: null # implemented, cancelled, wontfix, duplicate"
        )

    return yaml_header


def parse_issue_detail(file_path: Path) -> Optional[IssueDetail]:
    if not file_path.suffix == ".md":
        return None

    content = file_path.read_text()
    # Robust splitting
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if not match:
        return None

    yaml_str = match.group(1)
    body = content[match.end() :].lstrip()

    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            return None

        data["path"] = str(file_path.absolute())
        return IssueDetail(**data, body=body, raw_content=content)
    except Exception:
        return None


def find_next_id(issue_type: str, issues_root: Path, include_archived: bool = False) -> str:
    prefix_map = get_prefix_map(issues_root)
    prefix = prefix_map.get(issue_type, "ISSUE")
    pattern = re.compile(rf"{prefix}-(\d+)")
    max_id = 0

    base_dir = get_issue_dir(issue_type, issues_root)
    # Scan all subdirs: open, backlog, closed, archived (optional)
    status_dirs = ["open", "backlog", "closed"]
    if include_archived:
        status_dirs.append("archived")
    
    for status_dir in status_dirs:
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
    domains: List[str] = [],
    subdir: Optional[str] = None,
    sprint: Optional[str] = None,
    tags: List[str] = [],
    criticality: Optional[CriticalityLevel] = None,
) -> Tuple[IssueMetadata, Path]:
    # Validation
    for dep_id in dependencies:
        if not find_issue_path(issues_root, dep_id):
            raise ValueError(f"Dependency issue {dep_id} not found.")

    for rel_id in related:
        if not find_issue_path(issues_root, rel_id):
            raise ValueError(f"Related issue {rel_id} not found.")

    # Auto-assign default parent for non-epic types if not provided
    if issue_type != IssueType.EPIC and not parent:
        parent = "EPIC-0000"

    # Determine criticality
    # 1. Use provided criticality if specified
    # 2. Check parent for inheritance
    # 3. Apply type-based default
    effective_criticality = criticality

    # Get issue type string for mapping lookup
    issue_type_str = (
        issue_type.value if isinstance(issue_type, IssueType) else str(issue_type)
    )

    if effective_criticality is None:
        # Check parent inheritance
        if parent:
            parent_path = find_issue_path(issues_root, parent)
            if parent_path:
                parent_meta = parse_issue(parent_path)
                if parent_meta and parent_meta.criticality:
                    # Child must inherit at least parent's criticality
                    default_type_criticality = CriticalityTypeMapping.get_default(
                        issue_type_str
                    )
                    effective_criticality = (
                        CriticalityInheritanceService.resolve_child_criticality(
                            parent_meta.criticality, default_type_criticality
                        )
                    )

        # Fall back to type-based default
        if effective_criticality is None:
            effective_criticality = CriticalityTypeMapping.get_default(issue_type_str)

    issue_id = find_next_id(issue_type, issues_root)
    base_type_dir = get_issue_dir(issue_type, issues_root)
    target_dir = base_type_dir / status

    if subdir:
        target_dir = target_dir / subdir

    target_dir.mkdir(parents=True, exist_ok=True)

    # Auto-Populate Tags with required IDs
    auto_tags = set(tags) if tags else set()

    # 1. Add Parent
    if parent:
        auto_tags.add(f"#{parent}")

    # 2. Add Dependencies
    for dep in dependencies:
        auto_tags.add(f"#{dep}")

    # 3. Add Related
    for rel in related:
        auto_tags.add(f"#{rel}")

    # 4. Add Self
    auto_tags.add(f"#{issue_id}")

    final_tags = sorted(list(auto_tags))

    metadata = IssueMetadata(
        id=issue_id,
        uid=generate_uid(),
        type=issue_type,
        status=status,
        stage=stage,
        title=title,
        parent=parent,
        dependencies=dependencies,
        related=related,
        domains=domains,
        sprint=sprint,
        tags=final_tags,
        opened_at=current_time() if status == IssueStatus.OPEN else None,
        criticality=effective_criticality,
    )

    # Enforce lifecycle policies
    from .engine import get_engine

    get_engine().enforce_policy(metadata)

    # Serialize metadata
    yaml_header = _serialize_metadata(metadata)

    slug = _get_slug(title)
    filename = f"{issue_id}-{slug}.md"

    file_content = f"""---
{yaml_header}---

## {issue_id}: {title}

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [ ] Criteria 1

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [ ] Task 1

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
"""
    file_path = target_dir / filename
    file_path.write_text(file_content)

    metadata.path = str(file_path.absolute())

    return metadata, file_path


def get_available_actions(meta: IssueMetadata) -> List[Any]:
    from .models import IssueAction
    from .engine import get_engine

    engine = get_engine()
    transitions = engine.get_available_transitions(meta)

    actions = []
    for t in transitions:
        command = t.command_template.format(id=meta.id) if t.command_template else ""

        actions.append(
            IssueAction(
                label=t.label,
                icon=t.icon,
                target_status=t.to_status
                if t.to_status != meta.status or t.to_stage != meta.stage
                else None,
                target_stage=t.to_stage if t.to_stage != meta.stage else None,
                target_solution=t.required_solution,
                command=command,
            )
        )

    return actions


def find_issue_path(issues_root: Path, issue_id: str, include_archived: bool = True) -> Optional[Path]:
    """
    Find the path of an issue file.
    
    Args:
        issues_root: Root directory of issues
        issue_id: Issue ID to find
        include_archived: Whether to search in archived directory (default: True for find operations)
    """
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
        return find_issue_path(member_issues, parsed.local_id, include_archived)

    # Local Search
    try:
        prefix = parsed.local_id.split("-")[0].upper()
    except IndexError:
        return None

    reverse_prefix_map = get_reverse_prefix_map(issues_root)
    issue_type = reverse_prefix_map.get(prefix)
    if not issue_type:
        return None

    base_dir = get_issue_dir(issue_type, issues_root)
    # Search in standard status subdirs first
    for status_dir in ["open", "backlog", "closed"]:
        d = base_dir / status_dir
        if d.exists():
            for f in d.rglob(f"{parsed.local_id}-*.md"):
                return f
    
    # Search in archived if enabled
    if include_archived:
        archived_dir = base_dir / "archived"
        if archived_dir.exists():
            for f in archived_dir.rglob(f"{parsed.local_id}-*.md"):
                return f
    return None


def find_issue_path_across_branches(
    issues_root: Path, 
    issue_id: str, 
    project_root: Optional[Path] = None,
    include_archived: bool = True,
    allow_multi_branch: bool = False
) -> Tuple[Optional[Path], Optional[str], Optional[List[str]]]:
    """
    Find issue path across all local git branches.
    
    Implements the "Golden Path" logic:
    - If issue found in exactly one branch -> return it silently
    - If issue found in multiple branches -> handle based on allow_multi_branch flag
    - If issue not found in any branch -> return None
    
    Args:
        issues_root: Root directory of issues
        issue_id: Issue ID to find
        project_root: Project root (defaults to issues_root.parent)
        include_archived: Whether to search in archived directory
        allow_multi_branch: If True, return all conflicting branches instead of raising error
        
    Returns:
        Tuple of (file_path, branch_name, conflicting_branches) or (None, None, None) if not found
        conflicting_branches is None if no conflict, or a list of branch names if conflict detected
        
    Raises:
        RuntimeError: If issue found in multiple branches and allow_multi_branch is False (conflict)
    """
    # First, try to find in current working tree
    local_path = find_issue_path(issues_root, issue_id, include_archived)
    
    # Determine project root
    if project_root is None:
        project_root = issues_root.parent
    
    # If not a git repo, just return local result
    if not git.is_git_repo(project_root):
        return (local_path, None, None) if local_path else (None, None, None)
    
    # Get current branch
    current_branch = git.get_current_branch(project_root)
    
    # Issue files existing in multiple branches is NORMAL - not a conflict
    # Just return the local path without any conflict checking
    if local_path:
        return local_path, current_branch, None

    # Not found locally, search in all branches
    return _search_issue_in_branches(issues_root, issue_id, project_root, include_archived)


def _find_branches_with_file(project_root: Path, rel_path: str, exclude_branch: str) -> List[str]:
    """
    Find all branches (except excluded) that contain the given file path.
    
    Args:
        project_root: Project root path
        rel_path: Relative path from project root
        exclude_branch: Branch to exclude from search
        
    Returns:
        List of branch names containing the file
    """
    branches_with_file = []
    
    # Get all local branches
    code, stdout, _ = git._run_git(["branch", "--format=%(refname:short)"], project_root)
    if code != 0:
        return []
    
    all_branches = [b.strip() for b in stdout.splitlines() if b.strip()]
    
    for branch in all_branches:
        if branch == exclude_branch:
            continue
            
        # Check if file exists in this branch
        code, _, _ = git._run_git(["show", f"{branch}:{rel_path}"], project_root)
        if code == 0:
            branches_with_file.append(branch)
    
    return branches_with_file


def _search_issue_in_branches(
    issues_root: Path,
    issue_id: str,
    project_root: Path,
    include_archived: bool = True
) -> Tuple[Optional[Path], Optional[str], Optional[List[str]]]:
    """
    Search for an issue file across all branches.
    
    Returns:
        Tuple of (file_path, branch_name, conflicting_branches) or (None, None, None)
        conflicting_branches is None if no conflict, or a list of branch names if conflict detected
        
    Raises:
        RuntimeError: If issue found in multiple branches and allow_multi_branch is False
    """
    parsed = IssueID(issue_id)
    
    if not parsed.is_local:
        # For workspace issues, just use standard find
        path = find_issue_path(issues_root, issue_id, include_archived)
        return (path, None, None) if path else (None, None, None)
    
    # Get issue type from prefix
    try:
        prefix = parsed.local_id.split("-")[0].upper()
    except IndexError:
        return None, None, None
    
    reverse_prefix_map = get_reverse_prefix_map(issues_root)
    issue_type = reverse_prefix_map.get(prefix)
    if not issue_type:
        return None, None, None
    
    # Build possible paths to search
    base_dir = get_issue_dir(issue_type, issues_root)
    rel_base = base_dir.relative_to(project_root)
    
    status_dirs = ["open", "backlog", "closed"]
    if include_archived:
        status_dirs.append("archived")
    
    # Search pattern: Issues/{Type}/{status}/{issue_id}-*.md
    found_in_branches: List[Tuple[str, str]] = []  # (branch, file_path)
    
    # Get all local branches
    code, stdout, _ = git._run_git(["branch", "--format=%(refname:short)"], project_root)
    if code != 0:
        return None, None, None
    
    all_branches = [b.strip() for b in stdout.splitlines() if b.strip()]
    
    for branch in all_branches:
        # List files in each status directory for this branch
        for status_dir in status_dirs:
            dir_path = f"{rel_base}/{status_dir}"
            
            # List all files in this directory on the branch
            code, stdout, _ = git._run_git(
                ["ls-tree", "-r", "--name-only", branch, dir_path], 
                project_root
            )
            
            if code != 0 or not stdout.strip():
                continue
            
            # Find matching issue file (Handling quoted paths from git ls-tree)
            pattern = f"{parsed.local_id}-"
            for line in stdout.splitlines():
                line = line.strip()
                # Git quotes non-ASCII paths: "Issues/Chores/...md"
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                
                if pattern in line and line.endswith(".md"):
                    found_in_branches.append((branch, line))
    
    if not found_in_branches:
        return None, None, None
    
    if len(found_in_branches) > 1:
        # Found in multiple branches - return all branches for caller to handle
        branches = [b for b, _ in found_in_branches]
        branch, file_path = found_in_branches[0]
        full_path = project_root / file_path
        return full_path, branch, branches
    
    # Golden path: exactly one match
    branch, file_path = found_in_branches[0]
    
    # Checkout the file to working tree
    try:
        git.git_checkout_files(project_root, branch, [file_path])
        full_path = project_root / file_path
        return full_path, branch, None
    except Exception:
        # If checkout fails, return the path anyway - caller can handle
        full_path = project_root / file_path
        return full_path, branch, None


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
    tags: Optional[List[str]] = None,
    files: Optional[List[str]] = None,
    criticality: Optional[CriticalityLevel] = None,
    no_commit: bool = False,
    project_root: Optional[Path] = None,
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
            body = content[match_simple.end() :]
        else:
            raise ValueError(f"Could not parse frontmatter for {issue_id}")
    else:
        yaml_str = match.group(1)
        body = match.group(2)

    try:
        data = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError:
        raise ValueError(f"Invalid YAML metadata in {issue_id}")

    current_status_str = data.get("status", "open")  # default to open if missing?
    # Normalize current status to Enum for comparison
    try:
        current_status = IssueStatus(current_status_str.lower())
    except ValueError:
        current_status = IssueStatus.OPEN

    current_stage_str = data.get("stage")
    current_stage = IssueStage(current_stage_str.lower()) if current_stage_str else None

    # Logic: Status Update
    target_status = status if status else current_status

    # If status is changing, we don't default target_stage to current_stage
    # because the new status might have different allowed stages.
    # enforce_policy will handle setting the correct default stage for the new status.
    if status and status != current_status:
        target_stage = stage
    else:
        target_stage = stage if stage else current_stage

    # Engine Validation
    from .engine import get_engine

    engine = get_engine()

    # Map solution string to enum if present
    effective_solution = solution
    if not effective_solution and data.get("solution"):
        try:
            effective_solution = IssueSolution(data.get("solution").lower())
        except ValueError:
            pass

    # Reconstruct temporary metadata for policy validation
    temp_meta = IssueMetadata(**data)

    # Use engine to validate the transition
    transition = engine.validate_transition(
        from_status=current_status,
        from_stage=current_stage,
        to_status=target_status,
        to_stage=target_stage,
        solution=effective_solution,
        meta=temp_meta,
    )

    if target_status == "closed":
        # Policy: Dependencies must be closed
        dependencies_to_check = (
            dependencies if dependencies is not None else data.get("dependencies", [])
        )
        if dependencies_to_check:
            for dep_id in dependencies_to_check:
                dep_path = find_issue_path(issues_root, dep_id)
                if dep_path:
                    dep_meta = parse_issue(dep_path)
                    if dep_meta and dep_meta.status != "closed":
                        raise ValueError(
                            f"Dependency Block: Cannot close {issue_id} because dependency {dep_id} is [Status: {dep_meta.status}]."
                        )

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
        data["status"] = status

    if stage:
        data["stage"] = stage
    if solution:
        data["solution"] = solution

    if title:
        data["title"] = title

    if parent is not None:
        if parent == "":
            data.pop("parent", None)  # Remove parent field
        else:
            data["parent"] = parent

    if sprint is not None:
        data["sprint"] = sprint

    if dependencies is not None:
        data["dependencies"] = dependencies

    if related is not None:
        data["related"] = related

    if tags is not None:
        data["tags"] = tags

    if files is not None:
        data["files"] = files

    # Criticality update (only through escalation workflow)
    if criticality is not None:
        current_criticality = data.get("criticality")
        if current_criticality:
            current_level = CriticalityLevel(current_criticality)
            # Only allow escalation (increase), never lowering
            if criticality > current_level:
                data["criticality"] = criticality.value
            elif criticality < current_level:
                raise ValueError(
                    f"Cannot lower criticality from {current_level.value} to {criticality.value}. "
                    "Criticality is immutable and can only be increased through escalation workflow."
                )
        else:
            # Set if not previously set
            data["criticality"] = criticality.value

    # Lifecycle Hooks
    # 1. Opened At: If transitioning to OPEN
    if target_status == IssueStatus.OPEN and current_status != IssueStatus.OPEN:
        # Only set if not already set? Or always reset?
        # Let's set it if not present, or update it to reflect "Latest activation"
        # FEAT-0012 says: "update opened_at to now"
        data["opened_at"] = current_time()

    # 2. Backlog Push: Handled by IssueMetadata.validate_lifecycle (Status=Backlog -> Stage=None)
    # 3. Closed: Handled by IssueMetadata.validate_lifecycle (Status=Closed -> Stage=Done, ClosedAt=Now)

    # Touch updated_at
    data["updated_at"] = current_time()

    # Re-hydrate through Model
    try:
        updated_meta = IssueMetadata(**data)

        # Enforce lifecycle policies (defaults, auto-corrections)
        # This ensures that when we update, we also fix invalid states (like Closed but not Done)
        from .engine import get_engine

        get_engine().enforce_policy(updated_meta)

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
    new_yaml = _serialize_metadata(updated_meta)

    # Reconstruct File
    match_header = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if not match_header:
        body_content = body
    else:
        body_content = content[match_header.end() :]

    if body_content.startswith("\n"):
        body_content = body_content[1:]

    new_content = f"---\n{new_yaml}---\n{body_content}"

    path.write_text(new_content)

    # 3. Handle physical move if status changed
    # Save old path before move for git tracking
    old_path_before_move = path
    if status and status != current_status:
        # Move file
        prefix = issue_id.split("-")[0].upper()
        reverse_prefix_map = get_reverse_prefix_map(issues_root)
        base_type_dir = get_issue_dir(reverse_prefix_map[prefix], issues_root)

        try:
            rel_path = path.relative_to(base_type_dir)
            structure_path = (
                Path(*rel_path.parts[1:])
                if len(rel_path.parts) > 1
                else Path(path.name)
            )
        except ValueError:
            structure_path = Path(path.name)

        target_path = base_type_dir / target_status / structure_path

        if path != target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target_path)
            path = target_path  # Update local path variable for returned meta

    # Hook: Recursive Aggregation (FEAT-0003)
    if updated_meta.parent:
        recalculate_parent(issues_root, updated_meta.parent)

    # Auto-commit issue file changes (FEAT-0115)
    if not no_commit:
        # Determine the action type for commit message
        action = "update"
        if status and status != current_status:
            action = status  # "open", "closed", "backlog"
        elif stage and stage != current_stage:
            action = stage  # "draft", "doing", "review", "done"

        # Resolve project root if not provided
        if project_root is None:
            project_root = issues_root.parent

        # Only auto-commit if we're in a git repo
        git_service = IssueGitService(project_root)
        if git_service.is_git_repository():
            # Use the saved old path before file move for git tracking
            old_path_for_git = None
            if status and status != current_status and old_path_before_move != path:
                old_path_for_git = old_path_before_move

            commit_result = git_service.commit_issue_change(
                issue_id=issue_id,
                action=action,
                issue_file_path=path,
                old_file_path=old_path_for_git,
                no_commit=no_commit,
            )
            # Attach commit result to metadata for optional inspection
            updated_meta.commit_result = commit_result

    # Update returned metadata with final absolute path
    updated_meta.path = str(path.absolute())
    updated_meta.actions = get_available_actions(updated_meta)

    # Execute Post Actions (Trigger)
    if transition and hasattr(transition, "post_actions") and transition.post_actions:
        _execute_post_actions(transition.post_actions, updated_meta)

    return updated_meta


def _execute_post_actions(actions: List[str], meta: IssueMetadata):
    """
    Execute a list of shell commands as post-actions.
    Supports template substitution with issue metadata.
    """
    import shlex
    import subprocess
    from rich.console import Console
    
    console = Console()
    data = meta.model_dump(mode="json")
    
    for action in actions:
        try:
            # Safe template substitution
            cmd = action.format(**data)
        except KeyError as e:
            console.print(f"[yellow]Trigger Warning:[/yellow] Missing key for template '{action}': {e}")
            continue
            
        console.print(f"[bold cyan]Triggering:[/bold cyan] {cmd}")
        
        args = shlex.split(cmd)
        
        try:
            # Run in foreground to allow interaction if needed (e.g. agent output)
            subprocess.run(args, check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Trigger Failed:[/red] Command '{cmd}' exited with code {e.returncode}")
        except Exception as e:
            console.print(f"[red]Trigger Error:[/red] {e}")


def start_issue_isolation(
    issues_root: Path, issue_id: str, mode: str, project_root: Path
) -> IssueMetadata:
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
            raise ValueError(
                f"Issue {issue_id} is already isolated as '{issue.isolation.type}'. Please cleanup first."
            )

    slug = _get_slug(issue.title)
    branch_name = f"feat/{issue_id.lower()}-{slug}"

    isolation_meta = None

    if mode == "branch":
        if not git.branch_exists(project_root, branch_name):
            git.create_branch(project_root, branch_name, checkout=True)
        else:
            # Check if we are already on it?
            # If not, checkout.
            current = git.get_current_branch(project_root)
            if current != branch_name:
                git.checkout_branch(project_root, branch_name)

        isolation_meta = IssueIsolation(type="branch", ref=branch_name)

    elif mode == "worktree":
        wt_path = project_root / ".monoco" / "worktrees" / f"{issue_id.lower()}-{slug}"

        # Check if worktree exists physically
        if wt_path.exists():
            # Check if valid git worktree?
            pass
        else:
            wt_path.parent.mkdir(parents=True, exist_ok=True)
            git.worktree_add(project_root, branch_name, wt_path)

        isolation_meta = IssueIsolation(
            type="worktree", ref=branch_name, path=str(wt_path)
        )

    # Persist Metadata
    # We load raw, update isolation field, save.
    content = path.read_text()
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if match:
        yaml_str = match.group(1)
        data = yaml.safe_load(yaml_str) or {}

        data["isolation"] = isolation_meta.model_dump(mode="json")
        # Also ensure stage is DOING (logic link)
        data["stage"] = "doing"
        data["updated_at"] = current_time()

        new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
        new_content = content.replace(match.group(1), "\n" + new_yaml)
        path.write_text(new_content)

        return IssueMetadata(**data)

    return issue


def prune_issue_resources(
    issues_root: Path, issue_id: str, force: bool, project_root: Path
) -> List[str]:
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
        branch = _parse_isolation_ref(issue.isolation.ref)
        current = git.get_current_branch(project_root)
        if current == branch:
            raise RuntimeError(
                f"Cannot delete active branch '{branch}'. Please checkout 'main' first."
            )

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
            branch = _parse_isolation_ref(issue.isolation.ref)
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

        if "isolation" in data:
            del data["isolation"]
            data["updated_at"] = current_time()

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


def _has_uncommitted_changes(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Check if there are uncommitted changes in the working directory.
    
    Returns:
        Tuple of (has_changes, list_of_changed_files)
    """
    # Check for staged changes
    cmd_staged = ["diff", "--cached", "--name-only"]
    code, stdout, _ = git._run_git(cmd_staged, project_root)
    staged_files = [f.strip() for f in stdout.splitlines() if f.strip()] if code == 0 else []
    
    # Check for unstaged changes
    cmd_unstaged = ["diff", "--name-only"]
    code, stdout, _ = git._run_git(cmd_unstaged, project_root)
    unstaged_files = [f.strip() for f in stdout.splitlines() if f.strip()] if code == 0 else []
    
    # Check for untracked files
    cmd_untracked = ["ls-files", "--others", "--exclude-standard"]
    code, stdout, _ = git._run_git(cmd_untracked, project_root)
    untracked_files = [f.strip() for f in stdout.splitlines() if f.strip()] if code == 0 else []
    
    all_changes = list(set(staged_files + unstaged_files + untracked_files))
    all_changes.sort()
    
    return len(all_changes) > 0, all_changes


def sync_issue_files(issues_root: Path, issue_id: str, project_root: Path) -> List[str]:
    """
    Sync 'files' field in issue metadata with actual changed files in git.
    
    Pre-condition: All changes must be committed. If there are uncommitted changes,
    this function will raise an error with instructions on how to proceed.
    
    Strategies:
    1. Isolation Ref: If issue has isolation (branch/worktree), use that ref.
    2. Convention: If no isolation, look for branch `*/<id>-*`.
    3. Current Branch: If current branch matches pattern.

    Compares against default branch (usually 'main' or 'master').
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")

    issue = parse_issue(path)
    if not issue:
        raise ValueError(f"Could not parse issue {issue_id}")

    # CHORE-0036: Check for uncommitted changes
    has_uncommitted, uncommitted_files = _has_uncommitted_changes(project_root)
    if has_uncommitted:
        files_list = "\n  - ".join([""] + uncommitted_files)
        raise RuntimeError(
            f"Uncommitted changes detected in working directory:{files_list}\n\n"
            f"You must explicitly handle these files before syncing:\n"
            f"  1. git add <files> && git commit -m '...'  (to commit)\n"
            f"  2. git checkout -- <files>                   (to discard)\n"
            f"  3. echo '<pattern>' >> .gitignore            (to ignore)\n"
            f"  4. git rm <files>                            (to remove)\n\n"
            f"After handling, run: monoco issue sync-files {issue_id}"
        )

    # Determine Target Branch
    target_ref = None

    if issue.isolation and issue.isolation.ref:
        target_ref = _parse_isolation_ref(issue.isolation.ref)
        if target_ref == "current":
             target_ref = git.get_current_branch(project_root)
    else:
        # Heuristic Search
        # 1. Is current branch related?
        current = git.get_current_branch(project_root)
        if issue_id.lower() in current.lower():
            target_ref = current
        else:
            # 2. Search for branch
            # Limitation: core.git doesn't list all branches yet.
            # We skip this for now to avoid complexity, relying on isolation or current context.
            pass

    if not target_ref:
        raise RuntimeError(
            f"Could not determine git branch for Issue {issue_id}. Please ensure issue is started or you are on the feature branch."
        )

    # Determine Base Branch (assume main, or config?)
    # For now hardcode main, eventually read from config
    base_ref = "main"

    # Check if base exists, if not try master
    if not git.branch_exists(project_root, base_ref):
        if git.branch_exists(project_root, "master"):
            base_ref = "master"
        else:
            # Fallback: remote/main?
            pass

    # Git Diff
    # git diff --name-only base...target
    cmd = ["diff", "--name-only", f"{base_ref}...{target_ref}"]
    code, stdout, stderr = git._run_git(cmd, project_root)

    if code != 0:
        raise RuntimeError(f"Git diff failed: {stderr}")

    changed_files = [f.strip() for f in stdout.splitlines() if f.strip()]

    # Decode Git C-quoting format paths to native paths
    changed_files = [_unquote_git_path(f) for f in changed_files]

    # Sort for consistency
    changed_files.sort()

    # Update Issue
    # Only update if changed
    if changed_files != issue.files:
        update_issue(issues_root, issue_id, files=changed_files)
        return changed_files

    return []


def merge_issue_changes(
    issues_root: Path, issue_id: str, project_root: Path
) -> List[str]:
    """
    Perform Smart Atomic Merge or selection checkout of touched files.
    Ensures safe mainline synchronization by only merging files tracked in 'files' field.
    """
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise FileNotFoundError(f"Issue {issue_id} not found.")

    issue = parse_issue(path)
    if not issue:
        raise ValueError(f"Could not parse issue {issue_id}")

    if not issue.files:
        # If no files tracked, nothing to merge.
        return []

    # Determine Source (Feature Branch)
    # We prioritize what's in the issue metadata on LOCAL (main).
    # If not there, we try heuristic.
    source_ref = None
    if issue.isolation and issue.isolation.ref:
        source_ref = _parse_isolation_ref(issue.isolation.ref)
    else:
        # Heuristic: Search for branch by convention
        # We can't use 'current' here safely if we are on main,
        # but let's assume we might be calling this from elsewhere?
        # Actually, for 'close', we are likely on main.
        # So we search for a branch named 'feat/{id}-*' or similar?
        pass

    # If local metadata doesn't have isolation ref, we might be stuck.
    # But let's assume valid workflow.
    if not source_ref:
          # Try to find a branch starting with feat/{id} or {id}
          # This is a bit weak, needs better implementation in 'git' or 'issue' module
          # For now, if we can't find it, we error.
          pass

    if not source_ref or not git.branch_exists(project_root, source_ref):
        # Fallback: maybe we are currently ON the feature branch?
        # If so, source_ref should be current. But we expect to call this from MAIN.
        pass
        
    if not source_ref:
         raise RuntimeError(f"Could not determine source branch for Issue {issue_id}. Ensure isolation ref is set.")

    if not git.branch_exists(project_root, source_ref):
         raise RuntimeError(f"Source branch {source_ref} does not exist.")

    # RE-READ Issue from Source Branch
    # The 'files' list on main might be outdated. We need the list from the feature branch.
    relative_path = path.relative_to(project_root)
    
    try:
        # Read file content from git
        code, access_content, _ = git._run_git(["show", f"{source_ref}:{relative_path}"], project_root)
        if code == 0:
            # Parse it
            # We need to extract yaml frontmatter manually or use existing parser if it supported text input
            import re
            import yaml
            match = re.search(r"^---(.*?)---", access_content, re.DOTALL | re.MULTILINE)
            if match:
                data = yaml.safe_load(match.group(1)) or {}
                source_files = data.get("files", [])
                if source_files:
                    # Update issue object with latest files for this operation
                    issue.files = source_files
    except Exception as e:
        # If reading fails (maybe path changed?), we fall back to local 'files'
        pass

    if not issue.files:
         return []

    # Compatibility: Decode any legacy escaped paths in files field
    # This handles files stored before the _unquote_git_path fix was applied
    decoded_files = [_unquote_git_path(f) for f in issue.files]

    if not decoded_files:
        return []

    # Identify the issue file path
    relative_issue_path = str(path.relative_to(project_root))

    # Separate files: issue file vs code files
    code_files = [f for f in decoded_files if f != relative_issue_path]

    # 1. Conflict Check (only for code files, issue file skips conflict check)
    current_head = git.get_current_branch(project_root)
    try:
        base = git.get_merge_base(project_root, current_head, source_ref)
    except Exception as e:
        raise RuntimeError(f"Failed to determine merge base: {e}")

    conflicts = []
    for f in code_files:
        # Has main changed this file?
        if git.has_diff(project_root, base, current_head, [f]):
            # Has feature also changed this file?
            if git.has_diff(project_root, base, source_ref, [f]):
                conflicts.append(f)

    if conflicts:
        raise RuntimeError(
            f"Atomic Merge Conflict: The following files changed on both mainline and {issue_id}:\n"
            + "\n".join([f"  - {f}" for f in conflicts])
            + "\n\nPlease resolve manually using Cherry-Pick as per AGENTS.md policy."
        )

    # 2. Perform Atomic Merge (Selective Checkout)
    # Issue file is always included (no conflict check), along with conflict-free code files
    files_to_merge = decoded_files
    try:
        git.git_checkout_files(project_root, source_ref, files_to_merge)
    except Exception as e:
        raise RuntimeError(f"Selective checkout failed: {e}")

    return files_to_merge


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
使用 `monoco issue`:
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
        "skills": {"issues-management": SKILL_CONTENT},
        "prompts": {},  # Handled by adapter via resource files
    }


def list_issues(
    issues_root: Path, recursive_workspace: bool = False, include_archived: bool = False
) -> List[IssueMetadata]:
    """
    List all issues in the project.
    
    Args:
        issues_root: Root directory of issues
        recursive_workspace: Include issues from workspace members
        include_archived: Include archived issues (default: False)
    """
    issues = []
    engine = get_engine(str(issues_root.parent))
    all_types = engine.get_all_types()

    for issue_type in all_types:
        base_dir = get_issue_dir(issue_type, issues_root)
        status_dirs = ["open", "backlog", "closed"]
        if include_archived:
            status_dirs.append("archived")
        
        for status_dir in status_dirs:
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
                member_issues_dir = member_root / "Issues"  # Standard convention

                if member_issues_dir.exists():
                    # Fetch member issues (non-recursive to avoid loops)
                    member_issues = list_issues(member_issues_dir, False)
                    for m in member_issues:
                        # Namespace the ID to avoid collisions and indicate origin
                        # CRITICAL: Also namespace references to keep parent-child structure intact
                        if m.parent and "::" not in m.parent:
                            m.parent = f"{name}::{m.parent}"

                        if m.dependencies:
                            m.dependencies = [
                                f"{name}::{d}" if d and "::" not in d else d
                                for d in m.dependencies
                            ]

                        if m.related:
                            m.related = [
                                f"{name}::{r}" if r and "::" not in r else r
                                for r in m.related
                            ]

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
    board = {"draft": [], "doing": [], "review": [], "done": []}

    issues = list_issues(issues_root)
    for issue in issues:
        if issue.status == "open" and issue.stage:
            stage_val = issue.stage
            if stage_val in board:
                board[stage_val].append(issue)
        elif issue.status == "closed":
            # Optionally show recently closed items in DONE column
            board["done"].append(issue)

    return board


def validate_issue_integrity(
    meta: IssueMetadata, all_issue_ids: Set[str] = set()
) -> List[str]:
    """
    Validate metadata integrity (Solution, Lifecycle, etc.)
    UI-agnostic.
    """
    errors = []
    if meta.status == "closed" and not meta.solution:
        errors.append(
            f"Solution Missing: {meta.id} is closed but has no solution field."
        )

    if meta.parent:
        if all_issue_ids and meta.parent not in all_issue_ids:
            errors.append(
                f"Broken Link: {meta.id} refers to non-existent parent {meta.parent}."
            )

    if meta.status == "backlog" and meta.stage != "freezed":
        errors.append(
            f"Lifecycle Error: {meta.id} is backlog but stage is not freezed (found: {meta.stage})."
        )

    return errors


def update_issue_content(
    issues_root: Path, issue_id: str, new_content: str
) -> IssueMetadata:
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

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
        tmp.write(new_content)
        tmp_path = Path(tmp.name)

    try:
        meta = parse_issue(tmp_path)
        if not meta:
            raise ValueError("Invalid Issue Content: Frontmatter missing or invalid.")

        if meta.id != issue_id:
            raise ValueError(
                f"Cannot change Issue ID (Original: {issue_id}, New: {meta.id})"
            )

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
        reverse_prefix_map = get_reverse_prefix_map(issues_root)
        base_type_dir = get_issue_dir(reverse_prefix_map[prefix], issues_root)

        # Calculate structure path (preserve subdir)
        try:
            rel_path = path.relative_to(base_type_dir)
            # Remove the first component (current status directory) which might be 'open', 'closed' etc.
            # But wait, find_issue_path found it. 'rel_path' includes status dir.
            # e.g. open/Backend/Auth/FEAT-123.md -> parts=('open', 'Backend', 'Auth', 'FEAT-123.md')
            structure_path = (
                Path(*rel_path.parts[1:])
                if len(rel_path.parts) > 1
                else Path(path.name)
            )
        except ValueError:
            # Fallback if path is weird
            structure_path = Path(path.name)

        target_path = base_type_dir / meta.status / structure_path

        if path != target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target_path)

        return meta

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def update_issue_field(
    issue_path: Path,
    field: str,
    value: Any,
) -> IssueMetadata:
    """
    Update a specific field in an issue's frontmatter.

    Args:
        issue_path: Path to the issue file
        field: Field name to update
        value: New value for the field

    Returns:
        Updated IssueMetadata
    """
    # Read full content
    content = issue_path.read_text()

    # Split Frontmatter and Body
    match = re.search(r"^---(.*?)---\n(.*)", content, re.DOTALL | re.MULTILINE)
    if not match:
        raise ValueError(f"Could not parse frontmatter for {issue_path}")

    yaml_str = match.group(1)
    body = match.group(2)

    try:
        data = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML metadata: {e}")

    # Update the field
    data[field] = value
    data["updated_at"] = current_time()

    # Serialize back directly (not through model) to preserve all fields
    yaml_header = yaml.dump(
        data, sort_keys=False, allow_unicode=True, default_flow_style=False
    )

    # Reconstruct File
    new_content = f"---\n{yaml_header}---\n{body}"
    issue_path.write_text(new_content)

    # Re-hydrate through Model to validate and return
    updated_meta = IssueMetadata(**data)
    return updated_meta


def generate_delivery_report(
    issues_root: Path, issue_id: str, project_root: Path
) -> IssueMetadata:
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
        short_hash = c["hash"][:7]
        commit_list_md.append(f"- `{short_hash}` {c['subject']}")
        for f in c["files"]:
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


def check_issue_match(
    issue: IssueMetadata,
    explicit_positives: List[str],
    terms: List[str],
    negatives: List[str],
    full_content: str = "",
) -> bool:
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
        issue.status,
        issue.type,
        str(issue.stage) if issue.stage else "",
        *(issue.tags or []),
        *(issue.dependencies or []),
        *(issue.related or []),
        full_content,
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


def search_issues(issues_root: Path, query: str, include_archived: bool = False) -> List[IssueMetadata]:
    """
    Search issues using advanced query syntax.
    Returns list of matching IssueMetadata.
    
    Args:
        issues_root: Root directory of issues
        query: Search query string
        include_archived: Include archived issues in search (default: False)
    """
    explicit_positives, terms, negatives = parse_search_query(query)

    # Optimization: If no query, return empty? Or all?
    # Usually search implies input. CLI `list` is for all.
    # But if query is empty string, we return all?
    # Let's align with "grep": empty pattern matches everything?
    # Or strict: empty query -> all.
    if not explicit_positives and not terms and not negatives:
        return list_issues(issues_root, include_archived=include_archived)

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

    engine = get_engine(str(issues_root.parent))
    all_types = engine.get_all_types()

    for issue_type in all_types:
        base_dir = get_issue_dir(issue_type, issues_root)
        status_dirs = ["open", "backlog", "closed"]
        if include_archived:
            status_dirs.append("archived")
        
        for status_dir in status_dirs:
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
            if check_issue_match(
                meta, explicit_positives, terms, negatives, full_content=content
            ):
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
        return  # Should we warn?

    children = get_children(issues_root, parent_id)
    if not children:
        return

    total = len(children)
    closed = len([c for c in children if c.status == "closed"])
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
            active_children = [
                c for c in children if c.status == "open" and c.stage != "draft"
            ]
            closed_children = [c for c in children if c.status == "closed"]

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
    renumber: bool = False,
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
    target_status_dir = target_type_dir / issue.status

    # Preserve subdirectory structure if any
    try:
        source_type_dir = get_issue_dir(issue.type, source_issues_root)
        rel_path = source_path.relative_to(source_type_dir)
        # Remove status directory component
        structure_path = (
            Path(*rel_path.parts[1:])
            if len(rel_path.parts) > 1
            else Path(source_path.name)
        )
    except ValueError:
        structure_path = Path(source_path.name)

    # Update filename if ID changed
    if new_id != old_id:
        old_filename = source_path.name
        new_filename = old_filename.replace(old_id, new_id, 1)
        structure_path = (
            structure_path.parent / new_filename
            if structure_path.parent != Path(".")
            else Path(new_filename)
        )

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
            data["id"] = new_id
            data["updated_at"] = current_time()

            new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)

            # Update body (replace old ID in heading)
            body = content[match.end() :]
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
