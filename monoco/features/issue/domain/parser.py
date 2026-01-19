import yaml
import re
from typing import List, Optional, Tuple
from .models import Issue, IssueFrontmatter, IssueBody, ContentBlock, Span
from monoco.core.lsp import Range, Position


class MarkdownParser:
    """
    Parses markdown content into Domain Models.
    """

    # Regex for standard Issue IDs and cross-project IDs
    ISSUE_ID_PATTERN = r"\b((?:[a-zA-Z0-9_]+::)?(?:EPIC|FEAT|CHORE|FIX)-\d{4})\b"
    # Regex for Wikilinks [[Project::IssueID]] or [[IssueID]]
    WIKILINK_PATTERN = r"\[\[((?:[a-zA-Z0-9_]+::)?(?:EPIC|FEAT|CHORE|FIX)-\d{4})\]\]"

    @staticmethod
    def parse(content: str, path: Optional[str] = None) -> Issue:
        lines = content.splitlines()

        # 1. Parse Frontmatter
        frontmatter_dict, body_start_line = MarkdownParser._extract_frontmatter(lines)

        # 2. Create Frontmatter Object
        # Handle cases where frontmatter might be empty or invalid
        if not frontmatter_dict:
            # Fallback or error? For now, assume valid issues have frontmatter.
            # But during creation/drafting it might be partial.
            # We'll assume the input content *should* be a valid issue file.
            pass

        frontmatter = IssueFrontmatter(**frontmatter_dict)

        # 3. Parse Body
        body_lines = lines[body_start_line:]
        # Adjust line numbers relative to the original file
        blocks = MarkdownParser._parse_blocks(
            body_lines, start_line_offset=body_start_line
        )

        body = IssueBody(blocks=blocks)

        return Issue(path=path, frontmatter=frontmatter, body=body)

    @staticmethod
    def _extract_frontmatter(lines: List[str]) -> Tuple[dict, int]:
        """
        Extracts YAML frontmatter. Returns (dict, body_start_line_index).
        """
        if not lines or lines[0].strip() != "---":
            return {}, 0

        fm_lines = []
        i = 1
        while i < len(lines):
            line = lines[i]
            if line.strip() == "---":
                return yaml.safe_load("\n".join(fm_lines)), i + 1
            fm_lines.append(line)
            i += 1

        return {}, 0  # malformed

    @staticmethod
    def _parse_blocks(lines: List[str], start_line_offset: int) -> List[ContentBlock]:
        blocks = []
        current_block_lines = []
        current_block_type = "paragraph"
        current_start_line = start_line_offset

        def flush_block():
            nonlocal current_block_lines, current_start_line
            if current_block_lines:
                content = "\n".join(current_block_lines)
                block = ContentBlock(
                    type=current_block_type,
                    content=content,
                    line_start=current_start_line,
                    line_end=current_start_line + len(current_block_lines),
                )
                block.spans = MarkdownParser._parse_spans(
                    current_block_lines, current_start_line
                )
                blocks.append(block)
                current_block_lines = []

        for i, line in enumerate(lines):
            abs_line_idx = start_line_offset + i

            # Simple heuristic for block detection
            # 1. Heading
            if re.match(r"^#{1,6}\s", line):
                flush_block()

                # Add heading as its own block
                block = ContentBlock(
                    type="heading",
                    content=line,
                    line_start=abs_line_idx,
                    line_end=abs_line_idx + 1,
                )
                block.spans = MarkdownParser._parse_spans([line], abs_line_idx)
                blocks.append(block)
                current_start_line = abs_line_idx + 1
                current_block_type = "paragraph"  # reset
                continue

            # 2. Task List Item
            # Regex to capture indent, state char
            task_match = re.match(r"^(\s*)-\s*\[([ xX\-\+~/])\]", line)
            if task_match:
                flush_block()

                indent_str = task_match.group(1)
                state_char = task_match.group(2).lower()

                # Calculate level (assuming 2 spaces per level)
                level = len(indent_str) // 2

                # Determine state
                from .models import TaskState, TaskItem

                state_map = {
                    " ": TaskState.TODO,
                    "x": TaskState.DONE,
                    "-": TaskState.DOING,  # Legacy
                    "/": TaskState.DOING,  # New Standard
                    "+": TaskState.CANCELLED,  # Legacy
                    "~": TaskState.CANCELLED,  # New Standard
                }

                # Fallback for 'X' -> 'x'
                if state_char not in state_map and state_char == "x":
                    state_char = "x"

                block = TaskItem(
                    content=line,
                    line_start=abs_line_idx,
                    line_end=abs_line_idx + 1,
                    state=state_map.get(state_char, TaskState.TODO),
                    level=level,
                    metadata={"checked": state_char in ["x", "+"]},
                )
                block.spans = MarkdownParser._parse_spans([line], abs_line_idx)
                blocks.append(block)
                current_start_line = abs_line_idx + 1
                current_block_type = "paragraph"
                continue

            # 3. Empty lines (separators)
            if not line.strip():
                flush_block()

                blocks.append(
                    ContentBlock(
                        type="empty",
                        content="",
                        line_start=abs_line_idx,
                        line_end=abs_line_idx + 1,
                    )
                )
                current_start_line = abs_line_idx + 1
                current_block_type = "paragraph"
                continue

            # Default: accumulate lines into paragraph
            if not current_block_lines:
                current_start_line = abs_line_idx

            current_block_lines.append(line)

        # Flush remaining
        flush_block()

        return blocks

    @staticmethod
    def _parse_spans(lines: List[str], line_offset: int) -> List[Span]:
        """
        Parses a list of lines into Spans.
        """
        spans = []
        for i, line in enumerate(lines):
            abs_line_idx = line_offset + i

            # 1. Parse Checkboxes (only at start of line)
            checkbox_match = re.match(r"^(\s*-\s*\[)([ xX\-\+~/])(\])", line)
            if checkbox_match:
                start_char = len(checkbox_match.group(1))
                end_char = start_char + 1
                spans.append(
                    Span(
                        type="checkbox",
                        range=Range(
                            start=Position(line=abs_line_idx, character=start_char),
                            end=Position(line=abs_line_idx, character=end_char),
                        ),
                        content=checkbox_match.group(2),
                        metadata={"state": checkbox_match.group(2)},
                    )
                )

            # 2. Parse Wikilinks
            for match in re.finditer(MarkdownParser.WIKILINK_PATTERN, line):
                spans.append(
                    Span(
                        type="wikilink",
                        range=Range(
                            start=Position(line=abs_line_idx, character=match.start()),
                            end=Position(line=abs_line_idx, character=match.end()),
                        ),
                        content=match.group(0),
                        metadata={"issue_id": match.group(1)},
                    )
                )

            # 3. Parse Raw Issue IDs (not inside wikilinks)
            # We use a simple exclusion logic: if a match is inside a wikilink, skip it.
            wikilink_ranges = [
                (s.range.start.character, s.range.end.character)
                for s in spans
                if s.type == "wikilink" and s.range.start.line == abs_line_idx
            ]

            for match in re.finditer(MarkdownParser.ISSUE_ID_PATTERN, line):
                is_inside = any(
                    r[0] <= match.start() and match.end() <= r[1]
                    for r in wikilink_ranges
                )
                if not is_inside:
                    spans.append(
                        Span(
                            type="issue_id",
                            range=Range(
                                start=Position(
                                    line=abs_line_idx, character=match.start()
                                ),
                                end=Position(line=abs_line_idx, character=match.end()),
                            ),
                            content=match.group(0),
                            metadata={"issue_id": match.group(1)},
                        )
                    )

        return spans
