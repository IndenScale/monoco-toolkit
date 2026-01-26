import re
from typing import List, Set, Optional
from pathlib import Path

from monoco.core.lsp import Diagnostic, DiagnosticSeverity, Range, Position
from monoco.core.config import get_config
from monoco.features.i18n.core import detect_language
from .models import IssueMetadata
from .domain.parser import MarkdownParser
from .domain.models import ContentBlock
from .resolver import ReferenceResolver, ResolutionContext


class IssueValidator:
    """
    Centralized validation logic for Issue Tickets.
    Returns LSP-compatible Diagnostics.
    """

    def __init__(self, issue_root: Optional[Path] = None):
        self.issue_root = issue_root

    def validate(
        self,
        meta: IssueMetadata,
        content: str,
        all_issue_ids: Set[str] = set(),
        current_project: Optional[str] = None,
        workspace_root: Optional[str] = None,
    ) -> List[Diagnostic]:
        """
        Validate an issue and return diagnostics.
        """
        diagnostics = []
        self._current_project = current_project
        self._workspace_root = workspace_root

        # Parse Content into Blocks (Domain Layer)
        # Handle case where content might be just body (from update_issue) or full file
        if content.startswith("---"):
            try:
                issue_domain = MarkdownParser.parse(content)
                blocks = issue_domain.body.blocks
            except Exception:
                # Fallback if parser fails (e.g. invalid YAML)
                # We continue with empty blocks or try partial parsing?
                # For now, let's try to parse blocks ignoring FM
                lines = content.splitlines()
                # Find end of FM
                start_line = 0
                if lines[0].strip() == "---":
                    for i in range(1, len(lines)):
                        if lines[i].strip() == "---":
                            start_line = i + 1
                            break
                blocks = MarkdownParser._parse_blocks(
                    lines[start_line:], start_line_offset=start_line
                )
        else:
            # Assume content is just body
            lines = content.splitlines()
            blocks = MarkdownParser._parse_blocks(lines, start_line_offset=0)

        # 1. State Matrix Validation
        diagnostics.extend(self._validate_state_matrix(meta, content))

        # 2. State Requirements (Strict Verification)
        diagnostics.extend(self._validate_state_requirements(meta, blocks))

        # 3. Structure Consistency (Headings) - Using Blocks
        diagnostics.extend(self._validate_structure_blocks(meta, blocks))

        # 4. Lifecycle/Integrity (Solution, etc.)
        diagnostics.extend(self._validate_integrity(meta, content))

        # 5. Reference Integrity
        diagnostics.extend(self._validate_references(meta, content, all_issue_ids))

        # 5.5 Domain Integrity
        diagnostics.extend(self._validate_domains(meta, content, all_issue_ids))

        # 6. Time Consistency
        diagnostics.extend(self._validate_time_consistency(meta, content))

        # 7. Checkbox Syntax - Using Blocks
        diagnostics.extend(self._validate_checkbox_logic_blocks(blocks))

        # 8. Language Consistency
        diagnostics.extend(self._validate_language_consistency(meta, content))

        return diagnostics

    def _validate_language_consistency(
        self, meta: IssueMetadata, content: str
    ) -> List[Diagnostic]:
        diagnostics = []
        try:
            config = get_config()
            source_lang = config.i18n.source_lang

            # Check for language mismatch (specifically zh vs en)
            if source_lang.lower() == "zh":
                detected = detect_language(content)
                if detected == "en":
                    diagnostics.append(
                        self._create_diagnostic(
                            "Language Mismatch: Project source language is 'zh' but content appears to be 'en'.",
                            DiagnosticSeverity.Warning,
                        )
                    )
        except Exception:
            pass
        return diagnostics

    def _create_diagnostic(
        self, message: str, severity: DiagnosticSeverity, line: int = 0
    ) -> Diagnostic:
        """Helper to create a diagnostic object."""
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=0),
                end=Position(line=line, character=100),  # Arbitrary end
            ),
            severity=severity,
            message=message,
        )

    def _get_field_line(self, content: str, field_name: str) -> int:
        """Helper to find the line number of a field in the front matter."""
        lines = content.split("\n")
        in_fm = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "---":
                if not in_fm:
                    in_fm = True
                    continue
                else:
                    break  # End of FM
            if in_fm:
                # Match "field:", "field :", or "field: value"
                if re.match(rf"^{re.escape(field_name)}\s*:", stripped):
                    return i
        return 0

    def _validate_state_matrix(
        self, meta: IssueMetadata, content: str
    ) -> List[Diagnostic]:
        diagnostics = []

        # Check based on parsed metadata (now that auto-correction is disabled)
        if meta.status == "closed" and meta.stage != "done":
            line = self._get_field_line(content, "status")
            diagnostics.append(
                self._create_diagnostic(
                    f"State Mismatch: Closed issues must be in 'Done' stage (found: {meta.stage if meta.stage else 'None'})",
                    DiagnosticSeverity.Error,
                    line=line,
                )
            )

        if meta.status == "backlog" and meta.stage != "freezed":
            line = self._get_field_line(content, "status")
            diagnostics.append(
                self._create_diagnostic(
                    f"State Mismatch: Backlog issues must be in 'Freezed' stage (found: {meta.stage if meta.stage else 'None'})",
                    DiagnosticSeverity.Error,
                    line=line,
                )
            )

        return diagnostics

    def _validate_state_requirements(
        self, meta: IssueMetadata, blocks: List[ContentBlock]
    ) -> List[Diagnostic]:
        diagnostics = []

        # 1. Map Blocks to Sections
        sections = {"tasks": [], "ac": [], "review": []}
        current_section = None

        for block in blocks:
            if block.type == "heading":
                title = block.content.strip().lower()
                # Parse title to identify sections (supporting Chinese and English synonyms)
                if any(
                    kw in title
                    for kw in [
                        "technical tasks",
                        "工作包",
                        "技术任务",
                        "key deliverables",
                        "关键交付",
                        "重点工作",
                        "子功能",
                        "子故事",
                        "child features",
                        "stories",
                        "需求",
                        "requirements",
                        "implementation",
                        "实现",
                        "交付",
                        "delivery",
                        "规划",
                        "plan",
                        "tasks",
                        "任务",
                    ]
                ):
                    current_section = "tasks"
                elif any(
                    kw in title
                    for kw in ["acceptance criteria", "验收标准", "交付目标", "验收"]
                ):
                    current_section = "ac"
                elif any(
                    kw in title
                    for kw in [
                        "review comments",
                        "确认事项",
                        "评审记录",
                        "复盘记录",
                        "review",
                        "评审",
                        "确认",
                    ]
                ):
                    current_section = "review"
                elif title.startswith("###"):
                    # Subheading: allow continued collection for the current section
                    pass
                else:
                    current_section = None
            elif block.type == "task_item":
                if current_section and current_section in sections:
                    sections[current_section].append(block)

        # 2. Logic: DOING -> Must have defined tasks
        if meta.stage in ["doing", "review", "done"]:
            if not sections["tasks"]:
                # We can't strictly point to a line if section missing, but we can point to top/bottom
                # Or just a general error.
                diagnostics.append(
                    self._create_diagnostic(
                        "State Requirement (DOING+): Must define 'Technical Tasks' (at least 1 checkbox).",
                        DiagnosticSeverity.Warning,
                    )
                )

        # 3. Logic: REVIEW -> Tasks must be Completed ([x]) or Cancelled ([~], [+])
        # No [ ] (ToDo) or [-]/[/] (Doing) allowed.
        if meta.stage in ["review", "done"]:
            for block in sections["tasks"]:
                content = block.content.strip()
                # Check for explicit illegal states
                if re.search(r"-\s*\[\s+\]", content):
                    diagnostics.append(
                        self._create_diagnostic(
                            f"State Requirement ({meta.stage.upper()}): Technical Tasks must be resolved. Found Todo [ ]: '{content}'",
                            DiagnosticSeverity.Error,
                            line=block.line_start,
                        )
                    )
                elif re.search(r"-\s*\[[-\/]]", content):
                    diagnostics.append(
                        self._create_diagnostic(
                            f"State Requirement ({meta.stage.upper()}): Technical Tasks must be finished (not Doing). Found Doing [-]: '{content}'",
                            DiagnosticSeverity.Error,
                            line=block.line_start,
                        )
                    )

        # 4. Logic: DONE -> AC must be Verified ([x])
        if meta.stage == "done":
            for block in sections["ac"]:
                content = block.content.strip()
                if not re.search(r"-\s*\[[xX]\]", content):
                    diagnostics.append(
                        self._create_diagnostic(
                            f"State Requirement (DONE): Acceptance Criteria must be passed ([x]). Found: '{content}'",
                            DiagnosticSeverity.Error,
                            line=block.line_start,
                        )
                    )

            # 5. Logic: DONE -> Review Checkboxes (if any) must be Resolved ([x] or [~])
            for block in sections["review"]:
                content = block.content.strip()
                # Must be [x], [X], [~], [+]
                # Therefore [ ], [-], [/] are invalid blocking states
                if re.search(r"-\s*\[[\s\-\/]\]", content):
                    diagnostics.append(
                        self._create_diagnostic(
                            f"State Requirement (DONE): Actionable Review Comments must be resolved ([x] or [~]). Found: '{content}'",
                            DiagnosticSeverity.Error,
                            line=block.line_start,
                        )
                    )

        return diagnostics

    def _validate_structure_blocks(
        self, meta: IssueMetadata, blocks: List[ContentBlock]
    ) -> List[Diagnostic]:
        diagnostics = []

        # 1. Heading check: ## {issue-id}: {issue-title}
        expected_header = f"## {meta.id}: {meta.title}"
        header_found = False

        # 2. Review Comments Check
        review_header_found = False
        review_content_found = False

        review_header_index = -1

        for i, block in enumerate(blocks):
            if block.type == "heading":
                stripped = block.content.strip()
                if stripped == expected_header:
                    header_found = True

                # Flexible matching for Review Comments header
                if any(
                    kw in stripped
                    for kw in ["Review Comments", "评审备注", "评审记录", "Review"]
                ):
                    review_header_found = True
                    review_header_index = i

        # Check content after review header
        if review_header_found:
            # Check if there are blocks after review_header_index that are NOT empty
            for j in range(review_header_index + 1, len(blocks)):
                if blocks[j].type != "empty":
                    review_content_found = True
                    break

        if not header_found:
            diagnostics.append(
                self._create_diagnostic(
                    f"Structure Error: Missing Level 2 Heading '{expected_header}'",
                    DiagnosticSeverity.Warning,
                )
            )

        if meta.stage in ["review", "done"]:
            if not review_header_found:
                diagnostics.append(
                    self._create_diagnostic(
                        "Review Requirement: Missing '## Review Comments' section.",
                        DiagnosticSeverity.Error,
                    )
                )
            elif not review_content_found:
                diagnostics.append(
                    self._create_diagnostic(
                        "Review Requirement: '## Review Comments' section is empty.",
                        DiagnosticSeverity.Error,
                    )
                )
        return diagnostics

    def _validate_integrity(
        self, meta: IssueMetadata, content: str
    ) -> List[Diagnostic]:
        diagnostics = []
        if meta.status == "closed" and not meta.solution:
            line = self._get_field_line(content, "status")
            diagnostics.append(
                self._create_diagnostic(
                    f"Data Integrity: Closed issue {meta.id} missing 'solution' field.",
                    DiagnosticSeverity.Error,
                    line=line,
                )
            )

        # Tags Integrity Check
        # Requirement: tags field must carry parent dependencies and related issue id
        required_tags = set()

        # Self ID
        required_tags.add(f"#{meta.id}")

        if meta.parent:
            # Strip potential user # if accidentally added in models, though core stripped it
            # But here we want the tag TO HAVE #
            p = meta.parent if not meta.parent.startswith("#") else meta.parent[1:]
            required_tags.add(f"#{p}")

        for d in meta.dependencies:
            _d = d if not d.startswith("#") else d[1:]
            required_tags.add(f"#{_d}")

        for r in meta.related:
            _r = r if not r.startswith("#") else r[1:]
            required_tags.add(f"#{_r}")

        current_tags = set(meta.tags) if meta.tags else set()
        missing_tags = required_tags - current_tags

        if missing_tags:
            line = self._get_field_line(content, "tags")
            # If tags field doesn't exist, line is 0, which is fine
            # We join them for display
            missing_str = ", ".join(sorted(missing_tags))
            diagnostics.append(
                self._create_diagnostic(
                    f"Tag Check: Missing required context tags: {missing_str}",
                    DiagnosticSeverity.Warning,
                    line=line,
                )
            )

        return diagnostics

    def _validate_references(
        self, meta: IssueMetadata, content: str, all_ids: Set[str]
    ) -> List[Diagnostic]:
        diagnostics = []

        # Initialize Resolver
        resolver = None
        if all_ids:
            context = ResolutionContext(
                current_project=self._current_project or "local",
                workspace_root=self._workspace_root,
                available_ids=all_ids,
            )
            resolver = ReferenceResolver(context)

        # Malformed ID Check
        if meta.parent and meta.parent.startswith("#"):
            line = self._get_field_line(content, "parent")
            diagnostics.append(
                self._create_diagnostic(
                    f"Malformed ID: Parent '{meta.parent}' should not start with '#'.",
                    DiagnosticSeverity.Warning,
                    line=line,
                )
            )

        if meta.dependencies:
            for dep in meta.dependencies:
                if dep.startswith("#"):
                    line = self._get_field_line(content, "dependencies")
                    diagnostics.append(
                        self._create_diagnostic(
                            f"Malformed ID: Dependency '{dep}' should not start with '#'.",
                            DiagnosticSeverity.Warning,
                            line=line,
                        )
                    )

        if meta.related:
            for rel in meta.related:
                if rel.startswith("#"):
                    line = self._get_field_line(content, "related")
                    diagnostics.append(
                        self._create_diagnostic(
                            f"Malformed ID: Related '{rel}' should not start with '#'.",
                            DiagnosticSeverity.Warning,
                            line=line,
                        )
                    )

        if not all_ids or not resolver:
            return diagnostics

        # Logic: Epics must have a parent (unless it is the Sink Root EPIC-0000)
        if meta.type == "epic" and meta.id != "EPIC-0000" and not meta.parent:
            line = self._get_field_line(content, "parent")
            diagnostics.append(
                self._create_diagnostic(
                    "Hierarchy Violation: Epics must have a parent (e.g., 'EPIC-0000').",
                    DiagnosticSeverity.Error,
                    line=line,
                )
            )

        if (
            meta.parent
            and meta.parent != "EPIC-0000"
            and not meta.parent.startswith("#")
            and not resolver.is_valid_reference(meta.parent)
        ):
            line = self._get_field_line(content, "parent")
            diagnostics.append(
                self._create_diagnostic(
                    f"Broken Reference: Parent '{meta.parent}' not found.",
                    DiagnosticSeverity.Error,
                    line=line,
                )
            )

        for dep in meta.dependencies:
            if not resolver.is_valid_reference(dep):
                line = self._get_field_line(content, "dependencies")
                diagnostics.append(
                    self._create_diagnostic(
                        f"Broken Reference: Dependency '{dep}' not found.",
                        DiagnosticSeverity.Error,
                        line=line,
                    )
                )

        # Body Reference Check
        # Regex for generic issue ID: (EPIC|FEAT|CHORE|FIX)-\d{4}
        # We scan line by line to get line numbers
        lines = content.split("\n")
        # Skip frontmatter for body check to avoid double counting (handled above)
        in_fm = False
        fm_end = 0
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_fm:
                    in_fm = True
                else:
                    fm_end = i
                    break

        for i, line in enumerate(lines):
            if i <= fm_end:
                continue  # Skip frontmatter

            # Find all matches
            matches = re.finditer(r"\b((?:EPIC|FEAT|CHORE|FIX)-\d{4})\b", line)
            for match in matches:
                ref_id = match.group(1)
                # Check for namespaced ID before this match?
                # The regex above only catches the ID part.
                # Let's adjust regex to optionally catch namespace::
                full_match = re.search(
                    r"\b(?:([a-z0-9_-]+)::)?(" + re.escape(ref_id) + r")\b",
                    line[max(0, match.start() - 50) : match.end()],
                )

                check_id = ref_id
                if full_match and full_match.group(1):
                    check_id = f"{full_match.group(1)}::{ref_id}"

                if ref_id != meta.id and not resolver.is_valid_reference(check_id):
                    diagnostics.append(
                        self._create_diagnostic(
                            f"Broken Reference: Issue '{check_id}' not found.",
                            DiagnosticSeverity.Warning,
                            line=i,
                        )
                    )
        return diagnostics
        return diagnostics

    def _validate_time_consistency(
        self, meta: IssueMetadata, content: str
    ) -> List[Diagnostic]:
        diagnostics = []
        c = meta.created_at
        o = meta.opened_at
        u = meta.updated_at
        cl = meta.closed_at

        created_line = self._get_field_line(content, "created_at")
        opened_line = self._get_field_line(content, "opened_at")

        if o and c > o:
            diagnostics.append(
                self._create_diagnostic(
                    "Time Travel: created_at > opened_at",
                    DiagnosticSeverity.Warning,
                    line=created_line,
                )
            )

        if u and c > u:
            diagnostics.append(
                self._create_diagnostic(
                    "Time Travel: created_at > updated_at",
                    DiagnosticSeverity.Warning,
                    line=created_line,
                )
            )

        if cl:
            if c > cl:
                diagnostics.append(
                    self._create_diagnostic(
                        "Time Travel: created_at > closed_at",
                        DiagnosticSeverity.Error,
                        line=created_line,
                    )
                )
            if o and o > cl:
                diagnostics.append(
                    self._create_diagnostic(
                        "Time Travel: opened_at > closed_at",
                        DiagnosticSeverity.Error,
                        line=opened_line,
                    )
                )

        return diagnostics

    def _validate_domains(
        self, meta: IssueMetadata, content: str, all_ids: Set[str] = set()
    ) -> List[Diagnostic]:
        diagnostics = []
        # Check if 'domains' field exists in frontmatter text
        # We rely on text parsing because Pydantic defaults 'domains' to [] if missing.

        # If line is 0, it might be the first line (rare) or missing.
        # _get_field_line returns 0 if not found, but also if found at line 0?
        # Let's check if the field actually exists in text.
        has_domains_field = False
        lines = content.splitlines()
        in_fm = False
        field_line = 0
        for i, line_content in enumerate(lines):
            stripped = line_content.strip()
            if stripped == "---":
                if not in_fm:
                    in_fm = True
                else:
                    break
            elif in_fm:
                if stripped.startswith("domains:"):
                    has_domains_field = True
                    field_line = i
                    break

        # Governance Maturity Check
        # Rule: If Epics > 8 or Issues > 50, enforce Domain usage
        num_issues = len(all_ids)
        num_epics = len(
            [i for i in all_ids if "EPIC-" in i]
        )  # Simple heuristic, ideally check type

        is_mature = num_issues > 50 or num_epics > 8

        if not has_domains_field:
            if is_mature:
                # We report it on line 0 (start of file) or line 1
                diagnostics.append(
                    self._create_diagnostic(
                        "Governance Maturity: Project scale (Epics>8 or Issues>50) requires 'domains' field in frontmatter.",
                        DiagnosticSeverity.Warning,
                        line=0,
                    )
                )

        # Domain Content Validation
        from .domain_service import DomainService

        service = DomainService()

        if hasattr(meta, "domains") and meta.domains:
            for domain in meta.domains:
                if service.is_alias(domain):
                    canonical = service.get_canonical(domain)
                    diagnostics.append(
                        self._create_diagnostic(
                            f"Domain Alias: '{domain}' is an alias for '{canonical}'. Preference: Canonical.",
                            DiagnosticSeverity.Warning,
                            line=field_line,
                        )
                    )
                elif not service.is_defined(domain):
                    if service.config.strict:
                        diagnostics.append(
                            self._create_diagnostic(
                                f"Unknown Domain: '{domain}' is not defined in domain ontology.",
                                DiagnosticSeverity.Error,
                                line=field_line,
                            )
                        )
                    else:
                        diagnostics.append(
                            self._create_diagnostic(
                                f"Unknown Domain: '{domain}' is not defined in domain ontology.",
                                DiagnosticSeverity.Warning,
                                line=field_line,
                            )
                        )

        return diagnostics

    def _validate_checkbox_logic_blocks(
        self, blocks: List[ContentBlock]
    ) -> List[Diagnostic]:
        diagnostics = []

        for block in blocks:
            if block.type == "task_item":
                content = block.content.strip()
                # Syntax Check: - [?]
                # Added supported chars: /, ~, +
                match = re.match(r"- \[([ x\-/~+])\]", content)
                if not match:
                    # Check for Common errors
                    if re.match(r"- \[.{2,}\]", content):  # [xx] or [  ]
                        diagnostics.append(
                            self._create_diagnostic(
                                "Invalid Checkbox: Use single character [ ], [x], [-], [/]",
                                DiagnosticSeverity.Error,
                                block.line_start,
                            )
                        )
                    elif re.match(r"- \[([^ x\-/~+])\]", content):  # [v], [o]
                        diagnostics.append(
                            self._create_diagnostic(
                                "Invalid Checkbox Status: Use [ ], [x], [/], [~]",
                                DiagnosticSeverity.Error,
                                block.line_start,
                            )
                        )

        return diagnostics
