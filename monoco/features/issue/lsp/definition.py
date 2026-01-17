from pathlib import Path
from typing import Optional, List
from monoco.core.lsp import Location, Position, Range
from ..domain.parser import MarkdownParser
from ..domain.workspace import WorkspaceSymbolIndex, IssueLocation

class DefinitionProvider:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.index = WorkspaceSymbolIndex(workspace_root)
        # Lazy indexing handled by the index class itself

    def provide_definition(self, file_path: Path, position: Position) -> List[Location]:
        """
        Resolve definition at the given position in the file.
        """
        if not file_path.exists():
            return []

        content = file_path.read_text()
        
        # 1. Parse the document to find spans
        # We only need to find the span at the specific line
        issue = MarkdownParser.parse(content, path=str(file_path))
        
        target_span = None
        for block in issue.body.blocks:
            # Check if position is within block
             # Note: block.line_start is inclusive, line_end is exclusive for content
            if block.line_start <= position.line < block.line_end:
                 for span in block.spans:
                     if span.range.start.line == position.line:
                         # Check character range
                         if span.range.start.character <= position.character <= span.range.end.character:
                             target_span = span
                             break
            if target_span:
                break
        
        if not target_span:
            return []

        # 2. Resolve based on span type
        if target_span.type in ["wikilink", "issue_id"]:
            issue_id = target_span.metadata.get("issue_id")
            if issue_id:
                # Resolve using Workspace Index
                location = self.index.resolve(issue_id, context_project=self._get_context_project(file_path))
                if location:
                    return [
                        Location(
                            uri=f"file://{location.file_path}",
                            range=Range(
                                start=Position(line=0, character=0),
                                end=Position(line=0, character=0)
                            )
                        )
                    ]
        
        return []

    def _get_context_project(self, file_path: Path) -> Optional[str]:
        # Simple heuristic: look for parent directory name if it's a known project structure?
        # Or rely on configuration. 
        # For now, let's assume the index handles context if passed, or we pass None.
        # Actually resolving context project from file path is tricky without config loaded for that specific root.
        # Let's try to deduce from path relative to workspace root.
        try:
             rel = file_path.relative_to(self.workspace_root)
             return rel.parts[0] # First dir is likely project name in a workspace
        except ValueError:
             return "local"
