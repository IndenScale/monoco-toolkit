import fnmatch
from pathlib import Path
from typing import List, Optional
import re

DEFAULT_EXCLUDES = [
    ".git",
    ".reference",
    "dist",
    "build",
    "node_modules",
    "__pycache__",
    ".agent",
    ".mono",
    ".venv",
    "venv",
    "ENV",
    # Agent Integration Directories
    ".claude",
    ".gemini",
    ".qwen",
    ".openai",
    ".cursor",
    ".vscode",
    ".idea",
    ".fleet",
    # System Prompts & Agent Configs
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "QWEN.md",
    "SKILL.md",
]


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


def is_excluded(
    path: Path, root: Path, patterns: List[str], excludes: Optional[List[str]] = None
) -> bool:
    """Check if a path should be excluded based on patterns and defaults."""
    rel_path = str(path.relative_to(root))

    final_excludes = excludes if excludes is not None else DEFAULT_EXCLUDES

    # 1. Check default excludes (exact match for any path component, case-insensitive)
    for part in path.parts:
        if part.lower() in [e.lower() for e in final_excludes]:
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


def discover_markdown_files(root: Path, include_issues: bool = False) -> List[Path]:
    """Recursively find markdown files while respecting exclusion rules."""
    patterns = load_gitignore_patterns(root)
    all_md_files = []

    excludes = list(DEFAULT_EXCLUDES)
    if not include_issues:
        excludes.append("Issues")

    # We walk to ensure we can skip directories early if needed,
    # but for now rglob + filter is simpler.
    for p in root.rglob("*.md"):
        if p.is_file() and not is_excluded(p, root, patterns, excludes=excludes):
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

    # Generic Suffix Check: Detect any _XX suffix where XX is 2-3 letters
    # This prevents files like README_ZH.md from being treated as source files
    # even if 'zh' is not in target_langs (e.g. when scanning for 'en' gaps).
    if re.search(r"_[A-Z]{2,3}$", stem_upper):
        return True

    # Subdir check (case-insensitive)
    path_parts_lower = [p.lower() for p in path.parts]
    for lang in normalized_langs:
        if lang in path_parts_lower:
            return True

    return False


def get_target_translation_path(
    path: Path, root: Path, lang: str, source_lang: str = "en"
) -> Path:
    """Calculate the expected translation path for a specific language."""
    lang = lang.lower()

    # Parallel Directory Mode: docs/en/... -> docs/zh/...
    path_parts = list(path.parts)
    # Search for source_lang component to replace
    for i, part in enumerate(path_parts):
        if part.lower() == source_lang.lower():
            path_parts[i] = lang
            return Path(*path_parts)

    # Suffix Mode:
    # If stem ends with _{SOURCE_LANG}, strip it.
    stem = path.stem
    source_suffix = f"_{source_lang.upper()}"
    if stem.upper().endswith(source_suffix):
        stem = stem[: -len(source_suffix)]

    if path.parent == root:
        return path.with_name(f"{stem}_{lang.upper()}{path.suffix}")

    # Subdir Mode: for documentation directories (fallback)
    return path.parent / lang / path.name


def check_translation_exists(
    path: Path, root: Path, target_langs: List[str], source_lang: str = "en"
) -> List[str]:
    """
    Verify which target languages have translations.
    Returns a list of missing language codes.
    """
    if is_translation_file(path, target_langs):
        return []  # Already a translation, skip

    # Special handling for standard files: always treat as EN source
    effective_source_lang = source_lang
    if path.name.upper() in [
        "README.MD",
        "CHANGELOG.MD",
        "CODE_OF_CONDUCT.MD",
        "CONTRIBUTING.MD",
        "LICENSE.MD",
        "SECURITY.MD",
    ]:
        effective_source_lang = "en"

    missing = []
    for lang in target_langs:
        # Skip if target language matches the effective source language
        if lang.lower() == effective_source_lang.lower():
            continue

        target = get_target_translation_path(path, root, lang, effective_source_lang)
        if not target.exists():
            missing.append(lang)
    return missing


def detect_language(content: str) -> str:
    """
    Detect the language of the content using simple heuristics.
    Returns: 'zh', 'en', or 'unknown'
    """
    if not content:
        return "unknown"

    # Strip YAML Frontmatter if present
    # Matches --- at start, followed by anything, followed by ---
    frontmatter_pattern = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
    content = frontmatter_pattern.sub("", content)

    if not content.strip():
        return "unknown"

    # 1. Check for CJK characters (Chinese/Japanese/Korean)
    # Range: \u4e00-\u9fff (Common CJK Unified Ideographs)
    # Heuristic: If CJK count > threshold, it's likely Asian (we assume ZH for now in this context)
    total_chars = len(content)
    cjk_count = sum(1 for c in content if "\u4e00" <= c <= "\u9fff")

    # If > 5% chars are CJK, highly likely to be Chinese document
    if total_chars > 0 and cjk_count / total_chars > 0.05:
        return "zh"

    # 2. Check for English
    # Heuristic: High ASCII ratio and low CJK
    non_ascii = sum(1 for c in content if ord(c) > 127)

    # If < 10% non-ASCII, likely English (or code)
    if total_chars > 0 and non_ascii / total_chars < 0.1:
        return "en"

    return "unknown"


def is_content_source_language(path: Path, source_lang: str = "en") -> bool:
    """
    Check if file content appears to be in the source language.
    """
    try:
        # Special handling for README/CHANGELOG
        if path.name.upper() in ["README.MD", "CHANGELOG.MD"]:
            source_lang = "en"

        content = path.read_text(encoding="utf-8")
        detected = detect_language(content)

        # 'unknown' is leniently accepted as valid to avoid false positives on code-heavy files
        if detected == "unknown":
            return True

        # Normalize source_lang
        expected = source_lang.lower()
        if expected == "zh" or expected == "cn":
            return detected == "zh"
        elif expected == "en":
            return detected == "en"

        # For other languages, we don't have detectors yet
        return True
    except Exception:
        return True  # Assume valid on error


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


def init(root: Path):
    """Initialize I18n environment (No-op currently as it relies on config)."""
    # In future, could generate i18n config section if missing.
    pass

    return {
        "skills": {"i18n": SKILL_CONTENT},
        "prompts": {},  # Handled by adapter via resource files
    }
