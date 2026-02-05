"""Lint checks for .references directory structure and article front matter."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class LintIssue:
    """Represents a single lint issue."""
    rule: str
    message: str
    path: Optional[str] = None
    severity: str = "error"  # error, warning


@dataclass
class LintResult:
    """Result of a lint run."""
    issues: List[LintIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def add(self, rule: str, message: str, path: Optional[str] = None, severity: str = "error"):
        self.issues.append(LintIssue(rule, message, path, severity))


class SpikeLinter:
    """Linter for .references directory structure."""

    # Required fields for article front matter
    REQUIRED_FIELDS = {"id", "title", "source", "date", "type"}
    # Optional but known fields
    OPTIONAL_FIELDS = {"author", "language", "translations", "company", "domain", "tags",
                       "related_repos", "related_articles", "summary"}

    def __init__(self, references_dir: Path):
        self.references_dir = references_dir
        self.issues: List[LintIssue] = []

    def lint(self) -> LintResult:
        """Run all lint checks."""
        result = LintResult()

        # 1. Check directory structure
        self._check_structure(result)

        # 2. Check naming conventions
        self._check_naming(result)

        # 3. Check article front matter
        self._check_articles(result)

        # 4. Check ID uniqueness
        self._check_id_uniqueness(result)

        # 5. Check link validity
        self._check_links(result)

        # Collect stats
        result.stats = self._collect_stats()

        return result

    def _check_structure(self, result: LintResult):
        """Check that required directories and files exist."""
        # Check repos/ directory exists
        repos_dir = self.references_dir / "repos"
        if not repos_dir.exists():
            result.add("structure", "Missing required directory: repos/")

        # Check articles/ directory exists
        articles_dir = self.references_dir / "articles"
        if not articles_dir.exists():
            result.add("structure", "Missing required directory: articles/")
        else:
            # Check template.md exists in articles/
            template_file = articles_dir / "template.md"
            if not template_file.exists():
                result.add("structure", "Missing template.md in articles/")

        # Check that root only has repos/, articles/, and non-git directories
        if self.references_dir.exists():
            for item in self.references_dir.iterdir():
                if item.is_dir() and item.name not in {"repos", "articles"}:
                    # Check if it contains a .git directory (should be in repos/)
                    if (item / ".git").exists():
                        result.add(
                            "structure",
                            f"Git repo '{item.name}' should be in repos/ subdirectory",
                            str(item.relative_to(self.references_dir))
                        )

    def _check_naming(self, result: LintResult):
        """Check kebab-case naming for directories and files."""
        kebab_pattern = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

        articles_dir = self.references_dir / "articles"
        if articles_dir.exists():
            self._check_naming_recursive(articles_dir, result, kebab_pattern)

        repos_dir = self.references_dir / "repos"
        if repos_dir.exists():
            for item in repos_dir.iterdir():
                if item.is_dir():
                    # Repo names should be kebab-case
                    if not kebab_pattern.match(item.name):
                        result.add(
                            "naming",
                            f"Repo name '{item.name}' should be kebab-case (lowercase with hyphens)",
                            f"repos/{item.name}",
                            "warning"
                        )

    def _check_naming_recursive(self, dir_path: Path, result: LintResult, pattern: re.Pattern):
        """Recursively check naming in a directory."""
        for item in dir_path.iterdir():
            # Skip the template.md at root of articles
            if item.name == "template.md" and item.parent.name == "articles":
                continue

            # Check directory names (except language codes like 'zh')
            if item.is_dir():
                if item.name not in {"zh", "ja", "en"} and not pattern.match(item.name):
                    result.add(
                        "naming",
                        f"Directory name '{item.name}' should be kebab-case",
                        str(item.relative_to(self.references_dir)),
                        "warning"
                    )
                # Recurse into subdirectories
                self._check_naming_recursive(item, result, pattern)
            else:
                # Check file names
                name_without_ext = item.stem
                # Allow non-kebab-case for actual article files (they might have descriptive titles)
                # but recommend kebab-case for consistency

    def _check_articles(self, result: LintResult):
        """Check article front matter."""
        articles_dir = self.references_dir / "articles"
        if not articles_dir.exists():
            return

        for article_file in self._find_markdown_files(articles_dir):
            self._check_article_front_matter(article_file, result)

    def _find_markdown_files(self, dir_path: Path) -> List[Path]:
        """Find all markdown files recursively."""
        md_files = []
        for item in dir_path.rglob("*.md"):
            if item.name == "template.md" and item.parent.name == "articles":
                continue
            md_files.append(item)
        return md_files

    def _check_article_front_matter(self, file_path: Path, result: LintResult):
        """Check front matter of a single article."""
        rel_path = file_path.relative_to(self.references_dir)

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            result.add("front-matter", f"Failed to read file: {e}", str(rel_path))
            return

        # Check if file has front matter
        if not content.startswith('---'):
            result.add("front-matter", "Missing YAML front matter", str(rel_path))
            return

        # Extract front matter
        try:
            end_marker = content.find('---', 3)
            if end_marker == -1:
                result.add("front-matter", "Invalid front matter: missing closing ---", str(rel_path))
                return

            front_matter_text = content[3:end_marker].strip()
            if not front_matter_text:
                result.add("front-matter", "Empty front matter", str(rel_path))
                return

            front_matter = yaml.safe_load(front_matter_text)
            if not isinstance(front_matter, dict):
                result.add("front-matter", "Front matter must be a YAML object", str(rel_path))
                return

        except yaml.YAMLError as e:
            result.add("front-matter", f"Invalid YAML: {e}", str(rel_path))
            return
        except Exception as e:
            result.add("front-matter", f"Failed to parse front matter: {e}", str(rel_path))
            return

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in front_matter or front_matter[field] is None:
                result.add("required-field", f"Missing required field: {field}", str(rel_path))

        # Check for UNKNOWN values
        self._check_unknown_values(front_matter, str(rel_path), result)

    def _check_unknown_values(self, data: Any, path: str, result: LintResult, prefix: str = ""):
        """Recursively check for UNKNOWN values in front matter."""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str) and value == "UNKNOWN":
                    result.add("unknown-value", f"Field '{full_key}' has UNKNOWN value", path, "warning")
                elif isinstance(value, (dict, list)):
                    self._check_unknown_values(value, path, result, full_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                if isinstance(item, str) and item == "UNKNOWN":
                    result.add("unknown-value", f"Field '{full_key}' has UNKNOWN value", path, "warning")
                elif isinstance(item, (dict, list)):
                    self._check_unknown_values(item, path, result, full_key)

    def _check_id_uniqueness(self, result: LintResult):
        """Check that all article IDs are unique."""
        articles_dir = self.references_dir / "articles"
        if not articles_dir.exists():
            return

        ids: Dict[str, List[str]] = {}  # id -> list of files

        for article_file in self._find_markdown_files(articles_dir):
            rel_path = str(article_file.relative_to(self.references_dir))
            try:
                content = article_file.read_text(encoding='utf-8')
                if not content.startswith('---'):
                    continue

                end_marker = content.find('---', 3)
                if end_marker == -1:
                    continue

                front_matter = yaml.safe_load(content[3:end_marker].strip())
                if not isinstance(front_matter, dict):
                    continue

                article_id = front_matter.get('id')
                if article_id and article_id != "UNKNOWN":
                    if article_id not in ids:
                        ids[article_id] = []
                    ids[article_id].append(rel_path)

            except Exception:
                continue

        # Report duplicates
        for article_id, files in ids.items():
            if len(files) > 1:
                result.add(
                    "id-unique",
                    f"Duplicate ID '{article_id}' found in: {', '.join(files)}",
                    None
                )

    def _check_links(self, result: LintResult):
        """Check that related_repos and related_articles point to existing content."""
        articles_dir = self.references_dir / "articles"
        repos_dir = self.references_dir / "repos"

        if not articles_dir.exists():
            return

        # Get list of valid repos
        valid_repos = set()
        if repos_dir.exists():
            valid_repos = {d.name for d in repos_dir.iterdir() if d.is_dir()}

        # Get list of valid article IDs
        valid_article_ids = set()
        article_files = {}

        for article_file in self._find_markdown_files(articles_dir):
            rel_path = str(article_file.relative_to(self.references_dir))
            try:
                content = article_file.read_text(encoding='utf-8')
                if not content.startswith('---'):
                    continue

                end_marker = content.find('---', 3)
                if end_marker == -1:
                    continue

                front_matter = yaml.safe_load(content[3:end_marker].strip())
                if not isinstance(front_matter, dict):
                    continue

                article_id = front_matter.get('id')
                if article_id and article_id != "UNKNOWN":
                    valid_article_ids.add(article_id)
                    article_files[article_id] = rel_path

                # Check related_repos
                related_repos = front_matter.get('related_repos', [])
                if isinstance(related_repos, list):
                    for repo in related_repos:
                        if isinstance(repo, str) and repo != "UNKNOWN":
                            if repo not in valid_repos:
                                result.add(
                                    "link-valid",
                                    f"Related repo '{repo}' does not exist in repos/",
                                    rel_path,
                                    "warning"
                                )

                # Check related_articles (store for second pass)
                # We'll validate these after collecting all IDs

            except Exception:
                continue

        # Second pass: validate related_articles
        for article_file in self._find_markdown_files(articles_dir):
            rel_path = str(article_file.relative_to(self.references_dir))
            try:
                content = article_file.read_text(encoding='utf-8')
                if not content.startswith('---'):
                    continue

                end_marker = content.find('---', 3)
                if end_marker == -1:
                    continue

                front_matter = yaml.safe_load(content[3:end_marker].strip())
                if not isinstance(front_matter, dict):
                    continue

                related_articles = front_matter.get('related_articles', [])
                if isinstance(related_articles, list):
                    for related_id in related_articles:
                        if isinstance(related_id, str) and related_id != "UNKNOWN":
                            if related_id not in valid_article_ids:
                                result.add(
                                    "link-valid",
                                    f"Related article '{related_id}' does not exist",
                                    rel_path,
                                    "warning"
                                )

            except Exception:
                continue

    def _collect_stats(self) -> Dict[str, Any]:
        """Collect statistics about the references directory."""
        stats = {
            "repos_count": 0,
            "articles_count": 0,
            "unknown_fields": 0,
        }

        repos_dir = self.references_dir / "repos"
        if repos_dir.exists():
            stats["repos_count"] = sum(1 for d in repos_dir.iterdir() if d.is_dir())

        articles_dir = self.references_dir / "articles"
        if articles_dir.exists():
            stats["articles_count"] = len(self._find_markdown_files(articles_dir))

        return stats
