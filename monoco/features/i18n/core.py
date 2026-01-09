import os
import fnmatch
from pathlib import Path
from typing import List, Set, Dict, Any

DEFAULT_EXCLUDES = [".git", ".reference", "dist", "build", "node_modules", "__pycache__", ".agent", ".mono", ".venv", "venv", "ENV", "ISSUES"]

def load_gitignore_patterns(root: Path) -> List[str]:
    """Load patterns from .gitignore file."""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return []
    
    patterns = []
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Basic normalization for fnmatch
                    if line.startswith("/"):
                        line = line[1:]
                    patterns.append(line)
    except Exception:
        pass
    return patterns

def is_excluded(path: Path, root: Path, patterns: List[str]) -> bool:
    """Check if a path should be excluded based on patterns and defaults."""
    rel_path = str(path.relative_to(root))
    
    # 1. Check default excludes (exact match for any path component, case-insensitive)
    for part in path.parts:
        if part.lower() in [e.lower() for e in DEFAULT_EXCLUDES]:
            return True
            
    # 2. Check gitignore patterns
    for pattern in patterns:
        # Check against relative path
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Check against filename
        if fnmatch.fnmatch(path.name, pattern):
            return True
        # Check if the pattern matches a parent directory
        # e.g. pattern "dist/" should match "dist/info.md"
        if pattern.endswith("/"):
            clean_pattern = pattern[:-1]
            if rel_path.startswith(clean_pattern + "/") or rel_path == clean_pattern:
                return True
        elif "/" in pattern:
            # If pattern has a slash, it might be a subpath match
            if rel_path.startswith(pattern + "/"):
                return True

    return False

def discover_markdown_files(root: Path) -> List[Path]:
    """Recursively find markdown files while respecting exclusion rules."""
    patterns = load_gitignore_patterns(root)
    all_md_files = []
    
    # We walk to ensure we can skip directories early if needed, 
    # but for now rglob + filter is simpler.
    for p in root.rglob("*.md"):
        if p.is_file() and not is_excluded(p, root, patterns):
            all_md_files.append(p)
            
    return sorted(all_md_files)

def is_translation_file(path: Path, target_langs: List[str]) -> bool:
    """Check if the given path is a translation file (target)."""
    normalized_langs = [lang.lower() for lang in target_langs]
    
    # Suffix check (case-insensitive)
    stem_upper = path.stem.upper()
    for lang in normalized_langs:
        if stem_upper.endswith(f"_{lang.upper()}"):
            return True
            
    # Subdir check (case-insensitive)
    path_parts_lower = [p.lower() for p in path.parts]
    for lang in normalized_langs:
        if lang in path_parts_lower:
            return True
            
    return False

def get_target_translation_path(path: Path, root: Path, lang: str) -> Path:
    """Calculate the expected translation path for a specific language."""
    lang = lang.lower()
    
    # Parallel Directory Mode: docs/en/... -> docs/zh/...
    # We assume 'en' is the source language for now.
    path_parts = list(path.parts)
    # Search for 'en' component to replace
    # We iterate from root relative parts to be safe, but simple replacement of the first 'en' 
    # component (if not part of filename) is a good heuristic for docs structure.
    for i, part in enumerate(path_parts):
        if part.lower() == 'en':
            path_parts[i] = lang
            return Path(*path_parts)

    # Suffix Mode: for root files
    if path.parent == root:
        return path.with_name(f"{path.stem}_{lang.upper()}{path.suffix}")
    
    # Subdir Mode: for documentation directories (fallback)
    return path.parent / lang / path.name

def check_translation_exists(path: Path, root: Path, target_langs: List[str]) -> List[str]:
    """
    Verify which target languages have translations.
    Returns a list of missing language codes.
    """
    if is_translation_file(path, target_langs):
        return [] # Already a translation, skip
    
    missing = []
    for lang in target_langs:
        target = get_target_translation_path(path, root, lang)
        if not target.exists():
            missing.append(lang)
    return missing
# ... (Existing code) ...

SKILL_CONTENT = """---
name: i18n-scan
description: Internationalization quality control skill.
---

# i18n Maintenance Standard

i18n is a "first-class citizen" in Monoco.

## Core Standards

### 1. i18n Structure
- **Root Files**: Suffix pattern (e.g. `README_ZH.md`).
- **Docs Directories**: Subdirectory pattern (`docs/guide/zh/intro.md`).

### 2. Exclusion Rules
- `.gitignore` (respected automatically)
- `.references/`
- Build artifacts

## Automated Checklist
1. **Coverage Scan**: `monoco i18n scan` - Checks missing translations.
2. **Integrity Check**: Planned.

## Working with I18n
- Create English docs first.
- Create translations following the naming convention.
- Run `monoco i18n scan` to verify coverage.
"""

PROMPT_CONTENT = """### Documentation I18n
Manage internationalization.
- **Scan**: `monoco i18n scan` (Check for missing translations)
- **Structure**:
  - Root files: `FILE_ZH.md`
  - Subdirs: `folder/zh/file.md`"""

def init(root: Path):
    """Initialize I18n environment (No-op currently as it relies on config)."""
    # In future, could generate i18n config section if missing.
    pass

def get_resources() -> Dict[str, Any]:
    return {
        "skills": {
            "i18n": SKILL_CONTENT
        },
        "prompts": {
            "i18n": PROMPT_CONTENT
        }
    }

