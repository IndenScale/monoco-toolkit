import re
import yaml
from typing import List, Set, Optional, Dict
from pathlib import Path

from monoco.core.lsp import Diagnostic, DiagnosticSeverity, Range, Position
from .models import IssueMetadata, IssueStatus, IssueStage, IssueType

class IssueValidator:
    """
    Centralized validation logic for Issue Tickets.
    Returns LSP-compatible Diagnostics.
    """
    
    def __init__(self, issue_root: Optional[Path] = None):
        self.issue_root = issue_root

    def validate(self, meta: IssueMetadata, content: str, all_issue_ids: Set[str] = set()) -> List[Diagnostic]:
        diagnostics = []
        
        # 1. State Matrix Validation
        diagnostics.extend(self._validate_state_matrix(meta, content))
        
        # 2. Content Completeness (Checkbox check)
        diagnostics.extend(self._validate_content_completeness(meta, content))
        
        # 3. Structure Consistency (Headings)
        diagnostics.extend(self._validate_structure(meta, content))
        
        # 4. Lifecycle/Integrity (Solution, etc.)
        diagnostics.extend(self._validate_integrity(meta, content))
        
        # 5. Reference Integrity
        diagnostics.extend(self._validate_references(meta, content, all_issue_ids))

        # 6. Time Consistency
        diagnostics.extend(self._validate_time_consistency(meta, content))

        # 7. Checkbox Syntax
        diagnostics.extend(self._validate_checkbox_logic(content))
        
        return diagnostics

    def _create_diagnostic(self, message: str, severity: DiagnosticSeverity, line: int = 0) -> Diagnostic:
        """Helper to create a diagnostic object."""
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=0),
                end=Position(line=line, character=100) # Arbitrary end
            ),
            severity=severity,
            message=message
        )

    def _get_field_line(self, content: str, field_name: str) -> int:
        """Helper to find the line number of a field in the front matter."""
        lines = content.split('\n')
        in_fm = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "---":
                if not in_fm:
                    in_fm = True
                    continue
                else:
                    break # End of FM
            if in_fm:
                # Match "field:", "field :", or "field: value"
                if re.match(rf"^{re.escape(field_name)}\s*:", stripped):
                    return i
        return 0

    def _validate_state_matrix(self, meta: IssueMetadata, content: str) -> List[Diagnostic]:
        diagnostics = []
        
        # Check based on parsed metadata (now that auto-correction is disabled)
        if meta.status == IssueStatus.CLOSED and meta.stage != IssueStage.DONE:
            line = self._get_field_line(content, "status")
            diagnostics.append(self._create_diagnostic(
                f"State Mismatch: Closed issues must be in 'Done' stage (found: {meta.stage.value if meta.stage else 'None'})", 
                DiagnosticSeverity.Error,
                line=line
            ))
        
        if meta.status == IssueStatus.BACKLOG and meta.stage != IssueStage.FREEZED:
            line = self._get_field_line(content, "status")
            diagnostics.append(self._create_diagnostic(
                f"State Mismatch: Backlog issues must be in 'Freezed' stage (found: {meta.stage.value if meta.stage else 'None'})", 
                DiagnosticSeverity.Error,
                line=line
            ))

        return diagnostics

    def _validate_content_completeness(self, meta: IssueMetadata, content: str) -> List[Diagnostic]:
        diagnostics = []
        # Checkbox regex: - [ ] or - [x] or - [-] or - [/]
        checkboxes = re.findall(r"-\s*\[([ x\-/])\]", content)
        
        if len(checkboxes) < 2:
            diagnostics.append(self._create_diagnostic(
                "Content Incomplete: Ticket must contain at least 2 checkboxes (AC & Tasks).",
                DiagnosticSeverity.Warning
            ))
            
        if meta.stage in [IssueStage.REVIEW, IssueStage.DONE]:
            # No empty checkboxes allowed
            if ' ' in checkboxes:
                # Find the first occurrence line
                lines = content.split('\n')
                first_line = 0
                for i, line in enumerate(lines):
                    if re.search(r"-\s*\[ \]", line):
                        first_line = i
                        break
                        
                diagnostics.append(self._create_diagnostic(
                    f"Incomplete Tasks: Issue in {meta.stage} cannot have unchecked boxes.",
                    DiagnosticSeverity.Error,
                    line=first_line
                ))
        return diagnostics

    def _validate_structure(self, meta: IssueMetadata, content: str) -> List[Diagnostic]:
        diagnostics = []
        lines = content.split('\n')
        
        # 1. Heading check: ## {issue-id}: {issue-title}
        expected_header = f"## {meta.id}: {meta.title}"
        header_found = False
        
        # 2. Review Comments Check
        review_header_found = False
        review_content_found = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped == expected_header:
                header_found = True
            
            if line_stripped == "## Review Comments":
                review_header_found = True
                # Check near lines for content
                # This is a naive check (next line is not empty)
                if i + 1 < len(lines) and lines[i+1].strip():
                     review_content_found = True
                elif i + 2 < len(lines) and lines[i+2].strip():
                     review_content_found = True

        if not header_found:
             diagnostics.append(self._create_diagnostic(
                 f"Structure Error: Missing Level 2 Heading '{expected_header}'",
                 DiagnosticSeverity.Warning
             ))
             
        if meta.stage in [IssueStage.REVIEW, IssueStage.DONE]:
            if not review_header_found:
                diagnostics.append(self._create_diagnostic(
                    "Review Requirement: Missing '## Review Comments' section.",
                    DiagnosticSeverity.Error
                ))
            elif not review_content_found:
                diagnostics.append(self._create_diagnostic(
                    "Review Requirement: '## Review Comments' section is empty.",
                    DiagnosticSeverity.Error
                ))
        return diagnostics

    def _validate_integrity(self, meta: IssueMetadata, content: str) -> List[Diagnostic]:
        diagnostics = []
        if meta.status == IssueStatus.CLOSED and not meta.solution:
            line = self._get_field_line(content, "status")
            diagnostics.append(self._create_diagnostic(
                f"Data Integrity: Closed issue {meta.id} missing 'solution' field.",
                DiagnosticSeverity.Error,
                line=line
            ))
        return diagnostics
        
    def _validate_references(self, meta: IssueMetadata, content: str, all_ids: Set[str]) -> List[Diagnostic]:
        diagnostics = []
        if not all_ids:
            return diagnostics
            
        if meta.parent and meta.parent not in all_ids:
             line = self._get_field_line(content, "parent")
             diagnostics.append(self._create_diagnostic(
                f"Broken Reference: Parent '{meta.parent}' not found.",
                DiagnosticSeverity.Error,
                line=line
             ))
             
        for dep in meta.dependencies:
            if dep not in all_ids:
                line = self._get_field_line(content, "dependencies")
                diagnostics.append(self._create_diagnostic(
                    f"Broken Reference: Dependency '{dep}' not found.",
                    DiagnosticSeverity.Error,
                    line=line
                 ))
        return diagnostics

    def _validate_time_consistency(self, meta: IssueMetadata, content: str) -> List[Diagnostic]:
        diagnostics = []
        c = meta.created_at
        o = meta.opened_at
        u = meta.updated_at
        cl = meta.closed_at
        
        created_line = self._get_field_line(content, "created_at")
        opened_line = self._get_field_line(content, "opened_at")
        updated_line = self._get_field_line(content, "updated_at")
        closed_line = self._get_field_line(content, "closed_at")

        if o and c > o:
             diagnostics.append(self._create_diagnostic("Time Travel: created_at > opened_at", DiagnosticSeverity.Warning, line=created_line))
        
        if u and c > u:
             diagnostics.append(self._create_diagnostic("Time Travel: created_at > updated_at", DiagnosticSeverity.Warning, line=created_line))
             
        if cl:
            if c > cl:
                 diagnostics.append(self._create_diagnostic("Time Travel: created_at > closed_at", DiagnosticSeverity.Error, line=created_line))
            if o and o > cl:
                 diagnostics.append(self._create_diagnostic("Time Travel: opened_at > closed_at", DiagnosticSeverity.Error, line=opened_line))

        return diagnostics

    def _validate_checkbox_logic(self, content: str) -> List[Diagnostic]:
        diagnostics = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            
            # Syntax Check: - [?]
            if stripped.startswith("- ["):
                match = re.match(r"- \[([ x\-/])\]", stripped)
                if not match:
                    # Check for Common errors
                    if re.match(r"- \[.{2,}\]", stripped): # [xx] or [  ]
                         diagnostics.append(self._create_diagnostic("Invalid Checkbox: Use single character [ ], [x], [-], [/]", DiagnosticSeverity.Error, i))
                    elif re.match(r"- \[([^ x\-/])\]", stripped): # [v], [o]
                         diagnostics.append(self._create_diagnostic("Invalid Checkbox Status: Use [ ], [x], [-], [/]", DiagnosticSeverity.Error, i))
        
        return diagnostics
