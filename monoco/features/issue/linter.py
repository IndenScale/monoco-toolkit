from typing import List, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
import typer
import re
from monoco.core.config import get_config
from . import core
from .validator import IssueValidator
from monoco.core.lsp import Diagnostic, DiagnosticSeverity, Range, Position

console = Console()


# Removed check_environment_policy as per project philosophy:
# Toolkit should not interfere with Git operations.


def check_integrity(issues_root: Path, recursive: bool = False) -> List[Diagnostic]:
    """
    Verify the integrity of the Issues directory using LSP Validator.
    """
    diagnostics = []
    validator = IssueValidator(issues_root)

    all_issue_ids = set()
    id_to_path = {}
    all_issues = []

    # 1. Collection Phase (Build Index)
    # Helper to collect issues from a project
    def collect_project_issues(project_issues_root: Path, project_name: str = "local", include_archived: bool = False):
        project_issues = []
        project_diagnostics = []
        for subdir in ["Epics", "Features", "Chores", "Fixes", "Domains"]:
            d = project_issues_root / subdir
            if d.exists():
                if subdir == "Domains":
                    # Special handling for Domains (not Issue tickets)
                    for f in d.rglob("*.md"):
                        # Domain validation happens here inline or via separate validator
                        # For now, we just index them for reference validation
                        domain_key = f.stem
                        # Ensure H1 matches filename
                        try:
                            content = f.read_text(encoding="utf-8")

                            # 1. H1 Check
                            h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                            if not h1_match:
                                project_diagnostics.append(
                                    Diagnostic(
                                        range=Range(
                                            start=Position(line=0, character=0),
                                            end=Position(line=0, character=0),
                                        ),
                                        message=f"Domain '{f.name}' missing H1 title.",
                                        severity=DiagnosticSeverity.Error,
                                        source="DomainValidator",
                                    )
                                )
                            else:
                                h1_title = h1_match.group(1).strip()
                                # Allow exact match or "Domain: Name" pattern? User said "Title should be same as filename"
                                # But let's be strict: Filename stem MUST match H1
                                # User spec: "标题应该和文件名相同" -> The H1 content (after #) must equal filename stem (spaces sensitive).
                                # But wait, user example "Domain: Agent Onboarding" (bad) vs "Agent Onboarding" (good?).
                                # Actually user said "Attribute key in yaml" should match.
                                # Let's enforce: Filename 'Agent Onboarding.md' -> H1 '# Agent Onboarding'

                                # Check for "Domain: " prefix which is forbidden
                                if h1_title.lower().startswith("domain:"):
                                    project_diagnostics.append(
                                        Diagnostic(
                                            range=Range(
                                                start=Position(line=0, character=0),
                                                end=Position(line=0, character=0),
                                            ),
                                            message=f"Domain H1 must not use 'Domain:' prefix. Found '{h1_title}'.",
                                            severity=DiagnosticSeverity.Error,
                                            source="DomainValidator",
                                        )
                                    )
                                elif h1_title != f.stem:
                                    project_diagnostics.append(
                                        Diagnostic(
                                            range=Range(
                                                start=Position(line=0, character=0),
                                                end=Position(line=0, character=0),
                                            ),
                                            message=f"Domain H1 '{h1_title}' does not match filename '{f.stem}'.",
                                            severity=DiagnosticSeverity.Error,
                                            source="DomainValidator",
                                        )
                                    )

                            # 2. Source Language Check
                            # We import the check from i18n core if not available in validator yet
                            # But linter.py imports core... issue core.

                            # Need source lang. Conf is available below, let's grab it or pass it.
                            # We are inside a helper func, need to access outer scope or pass config.
                            # We'll do it in validation phase? Or here?
                            # 'conf' is defined in outer scope but not passed to this helper.
                            # Let's resolve config inside loop or pass it.
                            # To keep it simple, we do light check here.

                            # Actually, we should collect Domains into a list to pass to Validator
                            # so Validator can check if Issue 'domains' field references valid domains.
                            # We'll use a special set for this.
                            project_issues.append(
                                (f, "DOMAIN", f.stem)
                            )  # Marker for later

                        except Exception as e:
                            project_diagnostics.append(
                                Diagnostic(
                                    range=Range(
                                        start=Position(line=0, character=0),
                                        end=Position(line=0, character=0),
                                    ),
                                    message=f"Domain Read Error: {e}",
                                    severity=DiagnosticSeverity.Error,
                                    source="DomainValidator",
                                )
                            )

                else:
                    # Standard Issues (Epics/Features/etc)
                    files = []
                    # Standard status directories
                    status_dirs = ["open", "closed", "backlog"]
                    # Include archived if requested (for full validation)
                    if include_archived:
                        status_dirs.append("archived")
                    
                    for item in d.iterdir():
                        if item.is_dir():
                            status = item.name.lower()
                            if status in status_dirs:
                                files.extend(item.rglob("*.md"))
                            elif status != "archived": # archived is handled separately if include_archived
                                # Report Illegal Directory immediately
                                project_diagnostics.append(
                                    Diagnostic(
                                        range=Range(
                                            start=Position(line=0, character=0),
                                            end=Position(line=0, character=0),
                                        ),
                                        message=f"Illegal Directory: Issues should be in 'open/', 'closed/', or 'backlog/' directories, not '{status}/' directory.",
                                        severity=DiagnosticSeverity.Error,
                                        source="System",
                                    )
                                )

                    for f in files:
                        try:
                            meta = core.parse_issue(f, raise_error=True)
                            if meta:
                                local_id = meta.id
                                full_id = f"{project_name}::{local_id}"

                                if local_id in id_to_path:
                                    other_path = id_to_path[local_id]
                                    # Report on current file
                                    d_dup = Diagnostic(
                                        range=Range(
                                            start=Position(line=0, character=0),
                                            end=Position(line=0, character=0),
                                        ),
                                        message=f"Duplicate ID Violation: ID '{local_id}' is already used by {other_path.name}",
                                        severity=DiagnosticSeverity.Error,
                                        source=local_id,
                                    )
                                    d_dup.data = {"path": f}
                                    project_diagnostics.append(d_dup)
                                else:
                                    id_to_path[local_id] = f

                                all_issue_ids.add(local_id)
                                all_issue_ids.add(full_id)

                                # Filename Consistency Check
                                # Pattern: {ID}-{slug}.md
                                expected_slug = meta.title.lower().replace(" ", "-")
                                # Remove common symbols from slug for matching
                                expected_slug = re.sub(
                                    r"[^a-z0-9\-]", "", expected_slug
                                )
                                # Trim double dashes
                                expected_slug = re.sub(r"-+", "-", expected_slug).strip(
                                    "-"
                                )

                                filename_stem = f.stem
                                # Check if it starts with ID-
                                if not filename_stem.startswith(f"{meta.id}-"):
                                    project_diagnostics.append(
                                        Diagnostic(
                                            range=Range(
                                                start=Position(line=0, character=0),
                                                end=Position(line=0, character=0),
                                            ),
                                            message=f"Filename Error: Filename '{f.name}' must start with ID '{meta.id}-'",
                                            severity=DiagnosticSeverity.Error,
                                            source=meta.id,
                                            data={"path": f},
                                        )
                                    )
                                else:
                                    # Check slug matching (loose match, ensuring it's present)
                                    actual_slug = filename_stem[len(meta.id) + 1 :]
                                    if not actual_slug:
                                        project_diagnostics.append(
                                            Diagnostic(
                                                range=Range(
                                                    start=Position(line=0, character=0),
                                                    end=Position(line=0, character=0),
                                                ),
                                                message=f"Filename Error: Filename '{f.name}' missing title slug. Expected: '{meta.id}-{expected_slug}.md'",
                                                severity=DiagnosticSeverity.Error,
                                                source=meta.id,
                                                data={"path": f},
                                            )
                                        )

                                project_issues.append((f, meta, project_name))
                        except Exception as e:
                            # Report parsing failure as diagnostic
                            d = Diagnostic(
                                range=Range(
                                    start=Position(line=0, character=0),
                                    end=Position(line=0, character=0),
                                ),
                                message=f"Schema Error: {str(e)}",
                                severity=DiagnosticSeverity.Error,
                                source="System",
                            )
                            d.data = {"path": f}
                            project_diagnostics.append(d)
        return project_issues, project_diagnostics

    conf = get_config(str(issues_root.parent))

    # Identify local project name
    local_project_name = "local"
    if conf and conf.project and conf.project.name:
        local_project_name = conf.project.name.lower()

    # Find Topmost Workspace Root
    workspace_root = issues_root.parent
    for parent in [workspace_root] + list(workspace_root.parents):
        if (parent / ".monoco" / "workspace.yaml").exists() or (
            parent / ".monoco" / "project.yaml"
        ).exists():
            workspace_root = parent

    # Identify local project name
    local_project_name = "local"
    if conf and conf.project and conf.project.name:
        local_project_name = conf.project.name.lower()

    workspace_root_name = local_project_name
    if workspace_root != issues_root.parent:
        root_conf = get_config(str(workspace_root))
        if root_conf and root_conf.project and root_conf.project.name:
            workspace_root_name = root_conf.project.name.lower()

    # Collect from local issues_root
    proj_issues, proj_diagnostics = collect_project_issues(
        issues_root, local_project_name
    )
    all_issues.extend(proj_issues)
    diagnostics.extend(proj_diagnostics)

    if recursive:
        try:
            # Re-read config from workspace root to get all members
            ws_conf = get_config(str(workspace_root))

            # Index Root project if different from current
            if workspace_root != issues_root.parent:
                root_issues_dir = workspace_root / "Issues"
                if root_issues_dir.exists():
                    r_issues, r_diags = collect_project_issues(
                        root_issues_dir, ws_conf.project.name.lower()
                    )
                    all_issues.extend(r_issues)
                    diagnostics.extend(r_diags)

            # Index all members
            for member_name, rel_path in ws_conf.project.members.items():
                member_root = (workspace_root / rel_path).resolve()
                member_issues_dir = member_root / "Issues"
                if member_issues_dir.exists() and member_issues_dir != issues_root:
                    m_issues, m_diags = collect_project_issues(
                        member_issues_dir, member_name.lower()
                    )
                    all_issues.extend(m_issues)
                    diagnostics.extend(m_diags)
        except Exception:
            pass

    # 2. Validation Phase
    valid_domains = set()
    # Build list of actual IssueMetadata objects for domain governance checks
    all_issue_metas = []
    
    # Now validate
    for path, meta, project_name in all_issues:
        if meta == "DOMAIN":
            valid_domains.add(
                project_name
            )  # Record the domain name (which was stored in project_name slot)
        else:
            all_issue_metas.append(meta)

    # FEAT-0136: Project-Level Domain Governance Check
    # Calculate scale metrics
    num_issues = len(all_issue_metas)
    num_epics = len([i for i in all_issue_metas if i.type == "epic"])
    is_large_scale = num_issues > 128 or num_epics > 32
    
    # Check Domain Coverage for large-scale projects
    if is_large_scale and num_epics > 0:
        epics = [i for i in all_issue_metas if i.type == "epic"]
        untracked_epics = [e for e in epics if not e.domains]
        untracked_ratio = len(untracked_epics) / len(epics)
        
        # Rule: Untracked Epics / Total Epics <= 25%
        if untracked_ratio > 0.25:
            # Report this as a project-level diagnostic (attached to first epic or general)
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=0),
                    ),
                    message=f"Domain Governance: Coverage is too low for a project of this scale ({len(untracked_epics)}/{len(epics)} Epics untracked). "
                            f"At least 75% of Epics must have domains assigned.",
                    severity=DiagnosticSeverity.Error,
                    source="DomainGovernance",
                )
            )

    for path, meta, project_name in all_issues:
        if meta == "DOMAIN":
            # Track B: Domain Validation
            # Already did semantic checks in collection phase (H1 etc)
            # Now do Source Language Check
            try:
                from monoco.features.i18n import core as i18n_core

                # We need source_lang from config.
                # We have 'conf' object from earlier.
                source_lang = "en"
                if conf and conf.i18n and conf.i18n.source_lang:
                    source_lang = conf.i18n.source_lang

                if not i18n_core.is_content_source_language(path, source_lang):
                    diagnostics.append(
                        Diagnostic(
                            range=Range(
                                start=Position(line=0, character=0),
                                end=Position(line=0, character=0),
                            ),
                            message=f"Language Mismatch: Domain definition appears not to be in source language '{source_lang}'.",
                            severity=DiagnosticSeverity.Warning,
                            source="DomainValidator",
                        )
                    )
            except Exception:
                pass
            continue

        # Track A: Issue Validation
        content = path.read_text()  # Re-read content for validation

        # A. Run Core Validator
        # Pass valid_domains kwarg (Validator needs update to accept it)
        # FEAT-0136: Also pass all_issue_metas for domain governance checks
        file_diagnostics = validator.validate(
            meta,
            content,
            all_issue_ids,
            current_project=project_name,
            workspace_root=workspace_root_name,
            valid_domains=valid_domains,
            all_issues=all_issue_metas,
        )

        # Add context to diagnostics (Path)
        for d in file_diagnostics:
            d.source = f"{meta.id}"  # Use ID as source context
            d.data = {"path": path}  # Attach path for potential fixers
            diagnostics.append(d)

    return diagnostics


def run_lint(
    issues_root: Path,
    recursive: bool = False,
    fix: bool = False,
    format: str = "table",
    file_paths: Optional[List[str]] = None,
):
    """
    Run lint with optional auto-fix and format selection.

    Args:
        issues_root: Root directory of issues
        recursive: Recursively scan workspace members
        fix: Apply auto-fixes
        format: Output format (table, json)
        file_paths: Optional list of paths to files to validate (LSP/Pre-commit mode)
    """
    # No environment policy check here.
    # Toolkit should remain focused on Issue integrity.

    diagnostics = []

    # File list mode (for LSP integration or pre-commit)
    if file_paths:
        # Pre-scan entire workspace to get all issue IDs for reference validation
        # We need this context even when validating a single file
        all_issue_ids = set()
        for subdir in ["Epics", "Features", "Chores", "Fixes"]:
            d = issues_root / subdir
            if d.exists():
                for status in ["open", "closed", "backlog"]:
                    status_dir = d / status
                    if status_dir.exists():
                        for f in status_dir.rglob("*.md"):
                            try:
                                m = core.parse_issue(f)
                                if m:
                                    all_issue_ids.add(m.id)
                            except Exception:
                                pass

        # Collect valid domains
        valid_domains = set()
        domains_dir = issues_root / "Domains"
        if domains_dir.exists():
            for f in domains_dir.rglob("*.md"):
                valid_domains.add(f.stem)

        validator = IssueValidator(issues_root)

        for file_path in file_paths:
            file = Path(file_path).resolve()
            if not file.exists():
                console.print(f"[red]Error:[/red] File not found: {file_path}")
                continue  # Skip missing files but continue linting others

            # Parse and validate file
            try:
                meta = core.parse_issue(file, raise_error=True)
                if not meta:
                    console.print(
                        f"[yellow]Warning:[/yellow] Failed to parse issue metadata from {file_path}. Skipping."
                    )
                    continue

                content = file.read_text()

                # Try to resolve current project name for context
                current_project_name = "local"
                conf = get_config(str(issues_root.parent))
                if conf and conf.project and conf.project.name:
                    current_project_name = conf.project.name.lower()

                file_diagnostics = validator.validate(
                    meta,
                    content,
                    all_issue_ids,
                    current_project=current_project_name,
                    valid_domains=valid_domains,
                )

                # Add context
                for d in file_diagnostics:
                    d.source = meta.id
                    d.data = {"path": file}
                    diagnostics.append(d)

            except Exception as e:
                console.print(
                    f"[red]Error:[/red] Validation failed for {file_path}: {e}"
                )
                # We don't exit here, we collect errors
    else:
        # Full workspace scan mode
        diagnostics = check_integrity(issues_root, recursive)

    # Filter only Warnings and Errors
    issues = [d for d in diagnostics if d.severity <= DiagnosticSeverity.Warning]

    if fix:
        fixed_count = 0
        console.print("[dim]Attempting auto-fixes...[/dim]")

        # We must track processed paths to avoid redundant writes if multiple errors exist
        processed_paths = set()

        # Group diagnostics by file path
        from collections import defaultdict

        file_diags = defaultdict(list)
        for d in issues:
            if d.data.get("path"):
                file_diags[d.data["path"]].append(d)

        for path, diags in file_diags.items():
            try:
                content = path.read_text()
                new_content = content
                has_changes = False

                # Parse meta once for the file
                try:
                    meta = core.parse_issue(path)
                except Exception:
                    console.print(
                        f"[yellow]Skipping fix for {path.name}: Cannot parse metadata[/yellow]"
                    )
                    continue

                # Apply fixes for this file
                for d in diags:
                    if "Structure Error" in d.message:
                        expected_header = f"## {meta.id}: {meta.title}"

                        # Check if strictly present
                        if expected_header in new_content:
                            continue

                        # Strategy: Look for existing heading with same ID to replace
                        # Matches: "## ID..." or "## ID ..."
                        # Regex: ^##\s+ID\b.*$
                        # We use meta.id which is safe.
                        heading_regex = re.compile(
                            rf"^##\s+{re.escape(meta.id)}.*$", re.MULTILINE
                        )

                        match_existing = heading_regex.search(new_content)

                        if match_existing:
                            # Replace existing incorrect heading
                            # We use sub to replace just the first occurrence
                            new_content = heading_regex.sub(
                                expected_header, new_content, count=1
                            )
                            has_changes = True
                        else:
                            # Insert after frontmatter
                            fm_match = re.search(
                                r"^---(.*?)---", new_content, re.DOTALL | re.MULTILINE
                            )
                            if fm_match:
                                end_pos = fm_match.end()
                                header_block = f"\n\n{expected_header}\n"
                                new_content = (
                                    new_content[:end_pos]
                                    + header_block
                                    + new_content[end_pos:].lstrip()
                                )
                                has_changes = True

                    if (
                        "Review Requirement: Missing '## Review Comments' section"
                        in d.message
                    ):
                        if "## Review Comments" not in new_content:
                            new_content = (
                                new_content.rstrip()
                                + "\n\n## Review Comments\n\n- [ ] Self-Review\n"
                            )
                            has_changes = True

                    if "Malformed ID" in d.message:
                        lines = new_content.splitlines()
                        if d.range and d.range.start.line < len(lines):
                            line_idx = d.range.start.line
                            line = lines[line_idx]
                            # Remove # from quoted strings or raw values
                            new_line = line.replace("'#", "'").replace('"#', '"')
                            if new_line != line:
                                lines[line_idx] = new_line
                                new_content = "\n".join(lines) + "\n"
                                has_changes = True

                    if (
                        "Hierarchy Violation" in d.message
                        and "Epics must have a parent" in d.message
                    ):
                        try:
                            fm_match = re.search(
                                r"^---(.*?)---", new_content, re.DOTALL | re.MULTILINE
                            )
                            if fm_match:
                                import yaml

                                fm_text = fm_match.group(1)
                                data = yaml.safe_load(fm_text) or {}

                                # Default to EPIC-0000
                                data["parent"] = "EPIC-0000"

                                new_fm_text = yaml.dump(
                                    data, sort_keys=False, allow_unicode=True
                                )
                                # Replace FM block
                                new_content = new_content.replace(
                                    fm_match.group(1), "\n" + new_fm_text
                                )
                                has_changes = True
                        except Exception as ex:
                            console.print(
                                f"[red]Failed to fix parent hierarchy: {ex}[/red]"
                            )

                    if "Tag Check: Missing required context tags" in d.message:
                        # Extract missing tags from message
                        # Message format: "Tag Check: Missing required context tags: #TAG1, #TAG2"
                        try:
                            parts = d.message.split(": ")
                            if len(parts) >= 3:
                                tags_str = parts[-1]
                                missing_tags = [t.strip() for t in tags_str.split(",")]

                                # We need to update content via core.update_issue logic effectively
                                # But we are in a loop potentially with other string edits.
                                # IMPORTANT: Mixed strategy (Regex vs Object Update) is risky.
                                # However, tags are in YAML frontmatter.
                                # Since we might have modified new_content already (string), using core.update_issue on file is dangerous (race condition with memory).
                                # Better to append to tags list in YAML via regex or yaml parser on new_content.

                                # Parsing Frontmatter from new_content
                                fm_match = re.search(
                                    r"^---(.*?)---",
                                    new_content,
                                    re.DOTALL | re.MULTILINE,
                                )
                                if fm_match:
                                    import yaml

                                    fm_text = fm_match.group(1)
                                    data = yaml.safe_load(fm_text) or {}
                                    current_tags = data.get("tags", [])
                                    if not isinstance(current_tags, list):
                                        current_tags = []

                                    # Add missing
                                    updated_tags = sorted(
                                        list(set(current_tags) | set(missing_tags))
                                    )
                                    data["tags"] = updated_tags

                                    # Dump back
                                    new_fm_text = yaml.dump(
                                        data, sort_keys=False, allow_unicode=True
                                    )

                                    # Replace FM block
                                    new_content = new_content.replace(
                                        fm_match.group(1), "\n" + new_fm_text
                                    )
                                    has_changes = True
                        except Exception as ex:
                            console.print(f"[red]Failed to fix tags: {ex}[/red]")

                if has_changes:
                    path.write_text(new_content)
                    fixed_count += 1
                    console.print(f"[dim]Fixed: {path.name}[/dim]")
            except Exception as e:
                console.print(f"[red]Failed to fix {path.name}: {e}[/red]")

            # Separate Try-Block for Domains Fix to avoid nesting logic too deep
            try:
                content = path.read_text()
                new_content = content
                has_changes = False

                # Check diagnostics again for this file
                current_file_diags = file_diags.get(path, [])

                needs_domain_fix = any(
                    "Missing 'domains' field" in d.message for d in current_file_diags
                )

                if needs_domain_fix:
                    # Add 'domains: []' to frontmatter
                    # We insert it before 'tags:' if possible, or at end of keys
                    fm_match = re.search(
                        r"^---(.*?)---", new_content, re.DOTALL | re.MULTILINE
                    )
                    if fm_match:
                        import yaml

                        fm_text = fm_match.group(1)
                        # We prefer to edit text directly to preserve comments if possible,
                        # but for adding a key, robust way is ensuring it's in.
                        pass

                        # Simple Regex Insertion: find "tags:" and insert before it
                        if "tags:" in fm_text:
                            new_fm_text = fm_text.replace("tags:", "domains: []\ntags:")
                            new_content = new_content.replace(
                                fm_match.group(1), new_fm_text
                            )
                            has_changes = True
                        else:
                            # Append to end
                            new_fm_text = fm_text.rstrip() + "\ndomains: []\n"
                            new_content = new_content.replace(
                                fm_match.group(1), new_fm_text
                            )
                            has_changes = True

                if has_changes:
                    path.write_text(new_content)
                    if not any(
                        path == p for p in processed_paths
                    ):  # count once per file
                        fixed_count += 1
                        processed_paths.add(path)
                    console.print(f"[dim]Fixed (Domains): {path.name}[/dim]")

            except Exception as e:
                console.print(f"[red]Failed to fix domains for {path.name}: {e}[/red]")

            # Domain Alias and Format Fix
            try:
                format_fixes = [
                    d
                    for d in current_file_diags
                    if "Domain Format Error:" in d.message
                    or "Domain Alias:" in d.message
                ]
                if format_fixes:
                    fm_match = re.search(
                        r"^---(.*?)---", new_content, re.DOTALL | re.MULTILINE
                    )
                    if fm_match:
                        import yaml

                        fm_text = fm_match.group(1)
                        data = yaml.safe_load(fm_text) or {}

                        domain_changed = False
                        if "domains" in data and isinstance(data["domains"], list):
                            domains = data["domains"]
                            for d in format_fixes:
                                if "Domain Format Error:" in d.message:
                                    # Message: Domain Format Error: 'alias' must be PascalCase (e.g., 'canonical').
                                    m = re.search(
                                        r"Domain Format Error: '([^']+)' must be PascalCase \(e.g\., '([^']+)'\)",
                                        d.message,
                                    )
                                else:
                                    # Message: Domain Alias: 'alias' is an alias for 'canonical'.
                                    m = re.search(
                                        r"Domain Alias: '([^']+)' is an alias for '([^']+)'",
                                        d.message,
                                    )

                                if m:
                                    old_d = m.group(1)
                                    new_d = m.group(2)

                                    if old_d in domains:
                                        # Replace exact match
                                        domains = [
                                            new_d if x == old_d else x for x in domains
                                        ]
                                        domain_changed = True

                            if domain_changed:
                                # Deduplicate while preserving order if needed, but set is easier
                                seen = set()
                                unique_domains = []
                                for dom in domains:
                                    if dom not in seen:
                                        unique_domains.append(dom)
                                        seen.add(dom)

                                data["domains"] = unique_domains
                                new_fm_text = yaml.dump(
                                    data, sort_keys=False, allow_unicode=True
                                )
                                new_content = new_content.replace(
                                    fm_match.group(1), "\n" + new_fm_text
                                )
                                has_changes = True
                                path.write_text(new_content)
                                if not any(path == p for p in processed_paths):
                                    fixed_count += 1
                                    processed_paths.add(path)
                                console.print(
                                    f"[dim]Fixed (Domain Normalization): {path.name}[/dim]"
                                )

            except Exception as e:
                console.print(
                    f"[red]Failed to fix domain normalization for {path.name}: {e}[/red]"
                )

        console.print(f"[green]Applied auto-fixes to {fixed_count} files.[/green]")

        # Re-run validation to verify
        if file_paths:
            diagnostics = []  # Reset
            # Re-validate file list
            validator = IssueValidator(issues_root)
            # We assume all_issue_ids is already populated from the first pass if it was needed
            # But let's be safe and assume we might need to re-scan if IDs changed (unlikely during lint)
            # For simplicity, we reuse the validator instance but might need fresh content

            for file_path in file_paths:
                file = Path(file_path).resolve()
                if not file.exists():
                    continue

                try:
                    meta = core.parse_issue(file)
                    content = file.read_text()
                    file_diagnostics = validator.validate(
                        meta,
                        content,
                        all_issue_ids,
                        valid_domains=valid_domains,
                    )
                    for d in file_diagnostics:
                        d.source = meta.id
                        d.data = {"path": file}
                        diagnostics.append(d)
                except Exception:
                    pass
        else:
            diagnostics = check_integrity(issues_root, recursive)
        issues = [d for d in diagnostics if d.severity <= DiagnosticSeverity.Warning]

    # Output formatting
    if format == "json":
        from pydantic import RootModel

        # Use RootModel to export a list of models
        print(RootModel(issues).model_dump_json(indent=2))
        if any(d.severity == DiagnosticSeverity.Error for d in issues):
            raise typer.Exit(code=1)
        return

    if not issues:
        console.print(
            "[green]✔[/green] Issue integrity check passed. No integrity errors found."
        )
    else:
        table = Table(
            title="Issue Integrity Report",
            show_header=True,
            header_style="bold magenta",
            border_style="red",
        )
        table.add_column("Issue", style="cyan")
        table.add_column("Severity", justify="center")
        table.add_column("Line", justify="right", style="dim")
        table.add_column("Message")

        for d in issues:
            sev_style = "red" if d.severity == DiagnosticSeverity.Error else "yellow"
            sev_label = "ERROR" if d.severity == DiagnosticSeverity.Error else "WARN"
            line_str = str(d.range.start.line + 1) if d.range else "-"
            table.add_row(
                d.source or "Unknown",
                f"[{sev_style}]{sev_label}[/{sev_style}]",
                line_str,
                d.message,
            )

        console.print(table)

        if any(d.severity == DiagnosticSeverity.Error for d in issues):
            console.print(
                "\n[yellow]Tip: Run 'monoco issue lint --fix' to attempt automatic repairs.[/yellow]"
            )
            raise typer.Exit(code=1)

        if issues:
            console.print(
                "\n[yellow]Tip: Run 'monoco issue lint --fix' to attempt automatic repairs.[/yellow]"
            )
