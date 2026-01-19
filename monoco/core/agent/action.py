import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ActionContext(BaseModel):
    """Context information for matching actions."""

    id: Optional[str] = None
    type: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    file_path: Optional[str] = None
    project_id: Optional[str] = None


class ActionWhen(BaseModel):
    """Conditions under which an action should be displayed/active."""

    idMatch: Optional[str] = None
    typeMatch: Optional[str] = None
    stageMatch: Optional[str] = None
    statusMatch: Optional[str] = None
    fileMatch: Optional[str] = None

    def matches(self, context: ActionContext) -> bool:
        """Evaluate if the context matches these criteria."""
        if self.idMatch and context.id and not re.match(self.idMatch, context.id):
            return False
        if (
            self.typeMatch
            and context.type
            and not re.match(self.typeMatch, context.type)
        ):
            return False
        if (
            self.stageMatch
            and context.stage
            and not re.match(self.stageMatch, context.stage)
        ):
            return False
        if (
            self.statusMatch
            and context.status
            and not re.match(self.statusMatch, context.status)
        ):
            return False
        if (
            self.fileMatch
            and context.file_path
            and not re.match(self.fileMatch, context.file_path)
        ):
            return False
        return True


class PromptyAction(BaseModel):
    name: str
    description: str
    version: Optional[str] = "1.0.0"
    authors: List[str] = []
    model: Dict[str, Any] = {}
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    template: str
    when: Optional[ActionWhen] = None

    # Monoco specific metadata
    path: Optional[str] = None
    provider: Optional[str] = None  # Derived from model.api or explicitly set


class ActionRegistry:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root
        self._actions: List[PromptyAction] = []

    def scan(self) -> List[PromptyAction]:
        """Scan user global and project local directories for .prompty files."""
        self._actions = []

        # 1. User Global: ~/.monoco/actions/
        user_dir = Path.home() / ".monoco" / "actions"
        self._scan_dir(user_dir)

        # 2. Project Local: {project_root}/.monoco/actions/
        if self.project_root:
            project_dir = self.project_root / ".monoco" / "actions"
            self._scan_dir(project_dir)

        return self._actions

    def _scan_dir(self, directory: Path):
        if not directory.exists():
            return

        for prompty_file in directory.glob("*.prompty"):
            try:
                action = self._load_action(prompty_file)
                if action:
                    self._actions.append(action)
            except Exception as e:
                print(f"Failed to load action {prompty_file}: {e}")

    def _load_action(self, file_path: Path) -> Optional[PromptyAction]:
        content = file_path.read_text(encoding="utf-8")

        # Prompty Parser (Standard YAML Frontmatter + Body)
        # We look for the first --- and the second ---
        parts = re.split(r"^---\s*$", content, maxsplit=2, flags=re.MULTILINE)

        if len(parts) < 3:
            return None

        frontmatter_raw = parts[1]
        body = parts[2].strip()

        try:
            meta = yaml.safe_load(frontmatter_raw)
            if not meta or "name" not in meta:
                # Use filename as fallback name if missing? Prompty usually requires name.
                if not meta:
                    meta = {}
                meta["name"] = meta.get("name", file_path.stem)

            # Map Prompty 'when' if present
            when_data = meta.get("when")
            when = ActionWhen(**when_data) if when_data else None

            action = PromptyAction(
                name=meta["name"],
                description=meta.get("description", ""),
                version=meta.get("version"),
                authors=meta.get("authors", []),
                model=meta.get("model", {}),
                inputs=meta.get("inputs", {}),
                outputs=meta.get("outputs", {}),
                template=body,
                when=when,
                path=str(file_path.absolute()),
                provider=meta.get("provider") or meta.get("model", {}).get("api"),
            )
            return action

        except Exception as e:
            print(f"Invalid Prompty in {file_path}: {e}")
            return None

    def list_available(
        self, context: Optional[ActionContext] = None
    ) -> List[PromptyAction]:
        if not self._actions:
            self.scan()

        if not context:
            return self._actions

        return [a for a in self._actions if not a.when or a.when.matches(context)]

    def get(self, name: str) -> Optional[PromptyAction]:
        if not self._actions:
            self.scan()
        for a in self._actions:
            if a.name == name:
                return a
        return None
