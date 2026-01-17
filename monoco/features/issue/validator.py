import re
import yaml
from typing import List, Set, Optional, Dict
from pathlib import Path

from monoco.core.lsp import Diagnostic, DiagnosticSeverity, Range, Position
from monoco.core.config import get_config
from monoco.features.i18n.core import detect_language
from .models import IssueMetadata, IssueType
from .domain.parser import MarkdownParser
from .domain.models import ContentBlock

class IssueValidator:
    """
    Centralized validation logic for Issue Tickets.
    Returns LSP-compatible Diagnostics.
    """
    
    def __init__(self, issue_root: Optional[Path] = None):
        self.issue_root = issue_root

    def validate(self, meta: IssueMetadata, content: str, all_issue_ids: Set[str] = set()) -> List[Diagnostic]:
        diagnostics = []
        
        # Parse Content into Blocks (Domain Layer)
        # Handle case where content might be just body (from update_issue) or full file
        if content.startswith("---"):
            try:
                issue_domain = MarkdownParser.parse(content)
                blocks = issue_domain.body.blocks
                has_frontmatter = True
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
                blocks = MarkdownParser._parse_blocks(lines[start_line:], start_line_offset=start_line)
                has_frontmatter = True
        else:
            # Assume content is just body
            lines = content.splitlines()
            blocks = MarkdownParser._parse_blocks(lines, start_line_offset=0)
            has_frontmatter = False

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

        # 6. Time Consistency
        diagnostics.extend(self._validate_time_consistency(meta, content))

        # 7. Checkbox Syntax - Using Blocks
        diagnostics.extend(self._validate_checkbox_logic_blocks(blocks))
        
        # 8. Language Consistency
        diagnostics.extend(self._validate_language_consistency(meta, content))

        return diagnostics

    def _validate_language_consistency(self, meta: IssueMetadata, content: str) -> List[Diagnostic]:
        diagnostics = []
        try:
            config = get_config()
            source_lang = config.i18n.source_lang
            
            # Check for language mismatch (specifically zh vs en)
            if source_lang.lower() == 'zh':
                detected = detect_language(content)
                if detected == 'en':
                     diagnostics.append(self._create_diagnostic(
                         "Language Mismatch: Project source language is 'zh' but content appears to be 'en'.",
                         DiagnosticSeverity.Warning
                     ))
        except Exception:
            pass
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
        if meta.status == "closed" and meta.stage != "done":
            line = self._get_field_line(content, "status")
            diagnostics.append(self._create_diagnostic(
                f"State Mismatch: Closed issues must be in 'Done' stage (found: {meta.stage if meta.stage else 'None'})", 
                DiagnosticSeverity.Error,
                line=line
            ))
        
        if meta.status == "backlog" and meta.stage != "freezed":
            line = self._get_field_line(content, "status")
            diagnostics.append(self._create_diagnostic(
                f"State Mismatch: Backlog issues must be in 'Freezed' stage (found: {meta.stage if meta.stage else 'None'})", 
                DiagnosticSeverity.Error,
                line=line
            ))

        return diagnostics

    def _validate_state_requirements(self, meta: IssueMetadata, blocks: List[ContentBlock]) -> List[Diagnostic]:
        diagnostics = []
        
        # 1. Map Blocks to Sections
        sections = {"tasks": [], "ac": [], "review": []}
        current_section = None
        
        for block in blocks:
            if block.type == "heading":
                title = block.content.strip().lower()
                if "technical tasks" in title:
                    current_section = "tasks"
                elif "acceptance criteria" in title:
                    current_section = "ac"
                elif "review comments" in title:
                    current_section = "review"
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
                 diagnostics.append(self._create_diagnostic(
                     "State Requirement (DOING+): Must define 'Technical Tasks' (at least 1 checkbox).",
                     DiagnosticSeverity.Warning
                 ))

        # 3. Logic: REVIEW -> Tasks must be Completed ([x]) or Cancelled ([~], [+])
        # No [ ] (ToDo) or [-]/[/] (Doing) allowed.
        if meta.stage in ["review", "done"]:
            for block in sections["tasks"]:
                 content = block.content.strip()
                 # Check for explicit illegal states
                 if re.search(r"-\s*\[\s+\]", content):
                      diagnostics.append(self._create_diagnostic(
                          f"State Requirement ({meta.stage.upper()}): Technical Tasks must be resolved. Found Todo [ ]: '{content}'",
                          DiagnosticSeverity.Error,
                          line=block.line_start
                      ))
                 elif re.search(r"-\s*\[[-\/]]", content):
                      diagnostics.append(self._create_diagnostic(
                          f"State Requirement ({meta.stage.upper()}): Technical Tasks must be finished (not Doing). Found Doing [-]: '{content}'",
                          DiagnosticSeverity.Error,
                          line=block.line_start
                      ))

        # 4. Logic: DONE -> AC must be Verified ([x])
        if meta.stage == "done":
             for block in sections["ac"]:
                 content = block.content.strip()
                 if not re.search(r"-\s*\[[xX]\]", content):
                      diagnostics.append(self._create_diagnostic(
                          f"State Requirement (DONE): Acceptance Criteria must be passed ([x]). Found: '{content}'",
                          DiagnosticSeverity.Error,
                          line=block.line_start
                      ))
             
             # 5. Logic: DONE -> Review Checkboxes (if any) must be Resolved ([x] or [~])
             for block in sections["review"]:
                 content = block.content.strip()
                 # Must be [x], [X], [~], [+]
                 # Therefore [ ], [-], [/] are invalid blocking states
                 if re.search(r"-\s*\[[\s\-\/]\]", content):
                      diagnostics.append(self._create_diagnostic(
                          f"State Requirement (DONE): Actionable Review Comments must be resolved ([x] or [~]). Found: '{content}'",
                          DiagnosticSeverity.Error,
                          line=block.line_start
                      ))
                      
        return diagnostics

    def _validate_structure_blocks(self, meta: IssueMetadata, blocks: List[ContentBlock]) -> List[Diagnostic]:
        diagnostics = []
        
        # 1. Heading check: ## {issue-id}: {issue-title}
        expected_header = f"## {meta.id}: {meta.title}"
        header_found = False
        
        # 2. Review Comments Check
        review_header_found = False
        review_content_found = False
        
        review_header_index = -1
        
        for i, block in enumerate(blocks):
            if block.type == 'heading':
                stripped = block.content.strip()
                if stripped == expected_header:
                    header_found = True
                
                if stripped == "## Review Comments":
                    review_header_found = True
                    review_header_index = i
        
        # Check content after review header
        if review_header_found:
            # Check if there are blocks after review_header_index that are NOT empty
            for j in range(review_header_index + 1, len(blocks)):
                if blocks[j].type != 'empty':
                    review_content_found = True
                    break

        if not header_found:
             diagnostics.append(self._create_diagnostic(
                 f"Structure Error: Missing Level 2 Heading '{expected_header}'",
                 DiagnosticSeverity.Warning
             ))
             
        if meta.stage in ["review", "done"]:
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
        if meta.status == "closed" and not meta.solution:
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
                 
        # Body Reference Check
        # Regex for generic issue ID: (EPIC|FEAT|CHORE|FIX)-\d{4}
        # We scan line by line to get line numbers
        lines = content.split('\n')
        # Skip frontmatter for body check to avoid double counting (handled above)
        in_fm = False
        fm_end = 0
        for i, line in enumerate(lines):
            if line.strip() == '---':
                if not in_fm: in_fm = True
                else: 
                    fm_end = i
                    break
        
        for i, line in enumerate(lines):
            if i <= fm_end: continue # Skip frontmatter
            
            # Find all matches
            matches = re.finditer(r"\b((?:EPIC|FEAT|CHORE|FIX)-\d{4})\b", line)
            for match in matches:
                ref_id = match.group(1)
                if ref_id != meta.id and ref_id not in all_ids:
                     # Check if it's a namespaced ID? The regex only catches local IDs.
                     # If users use MON::FEAT-0001, the regex might catch FEAT-0001.
                     # But all_ids contains full IDs (potentially namespaced).
                     # Simple logic: if ref_id isn't in all_ids, check if any id ENDS with ref_id
                     
                     found_namespaced = any(known.endswith(f"::{ref_id}") for known in all_ids)
                     
                     if not found_namespaced:
                        diagnostics.append(self._create_diagnostic(
                            f"Broken Reference: Issue '{ref_id}' not found.",
                            DiagnosticSeverity.Warning,
                            line=i
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

    def _validate_checkbox_logic_blocks(self, blocks: List[ContentBlock]) -> List[Diagnostic]:
        diagnostics = []
        
        for block in blocks:
            if block.type == 'task_item':
                content = block.content.strip()
                # Syntax Check: - [?]
                # Added supported chars: /, ~, +
                match = re.match(r"- \[([ x\-/~+])\]", content)
                if not match:
                    # Check for Common errors
                    if re.match(r"- \[.{2,}\]", content): # [xx] or [  ]
                         diagnostics.append(self._create_diagnostic("Invalid Checkbox: Use single character [ ], [x], [-], [/]", DiagnosticSeverity.Error, block.line_start))
                    elif re.match(r"- \[([^ x\-/~+])\]", content): # [v], [o]
                         diagnostics.append(self._create_diagnostic("Invalid Checkbox Status: Use [ ], [x], [/], [~]", DiagnosticSeverity.Error, block.line_start))
        
        return diagnostics
