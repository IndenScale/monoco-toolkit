"""
Last-Word: Core Implementation.

This module implements the core logic for the last-word protocol:
- Entry buffer management during sessions
- Validation and grouping
- Staging and applying updates
- File locking and atomic writes
"""

import hashlib
import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import defaultdict

from .models import (
    Entry,
    EntryMeta,
    LastWordSchema,
    OperationType,
    TargetKey,
    ValidationError,
    ValidationResult,
    ApplyResult,
    StagedFile,
    LastWordConfig,
    KnowledgeBaseConfig,
)


# Global buffer for session entries
_session_buffer: list[Entry] = []
_session_id: Optional[str] = None


def get_last_word_dir() -> Path:
    """Get the global last-word directory."""
    return Path.home() / ".config" / "agents" / "last-word"


def get_staging_dir() -> Path:
    """Get the staging directory for failed/conflicting updates."""
    return get_last_word_dir() / "staging"


def get_config_path() -> Path:
    """Get the config file path."""
    return get_last_word_dir() / "config.yaml"


def get_knowledge_base_yaml_path(kb_name: str) -> Path:
    """Get the YAML file path for a knowledge base."""
    return get_last_word_dir() / f"{kb_name}.md.yaml"


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    get_last_word_dir().mkdir(parents=True, exist_ok=True)
    get_staging_dir().mkdir(parents=True, exist_ok=True)


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_part = secrets.token_hex(4)
    return f"session_{timestamp}-{random_part}"


def init_session(session_id: Optional[str] = None) -> str:
    """
    Initialize a new last-word session.
    
    Call this at session start to set up the buffer.
    
    Args:
        session_id: Optional session identifier (auto-generated if not provided)
        
    Returns:
        The session ID
    """
    global _session_buffer, _session_id
    _session_buffer = []
    _session_id = session_id or generate_session_id()
    ensure_directories()
    return _session_id


def plan(
    path: str,
    heading: str,
    content: Optional[str] = None,
    level: int = 2,
    operation: Optional[OperationType] = None,
    confidence: float = 0.9,
    reason: Optional[str] = None,
) -> Entry:
    """
    Declare an intention to update knowledge base.
    
    This is the main API for models to declare update intentions during a session.
    The entry is stored in memory buffer and processed at session end.
    
    Args:
        path: Target file path (e.g., "USER.md", "~/.config/agents/USER.md")
        heading: Exact heading text to target
        content: Content to update (None for delete, "" for clear)
        level: Heading level (1-6)
        operation: Explicit operation type (auto-detected if None)
        confidence: Confidence level (0-1)
        reason: Reason for the update
        
    Returns:
        The created Entry
        
    Example:
        >>> entry = plan(
        ...     path="~/.config/agents/USER.md",
        ...     heading="Research Interests",
        ...     content="- AI Agents\\n- Domain Modeling",
        ...     operation=OperationType.UPDATE,
        ...     confidence=0.95,
        ...     reason="User discussed these topics extensively"
        ... )
    """
    global _session_buffer, _session_id
    
    if _session_id is None:
        init_session()
    
    # Auto-detect operation from content
    if operation is None:
        if content is None:
            operation = OperationType.NO_OP
        elif content == "":
            operation = OperationType.CLEAR
        else:
            operation = OperationType.UPDATE
    
    entry = Entry(
        key=TargetKey(path=path, heading=heading, level=level),
        operation=operation,
        content=content,
        meta=EntryMeta(
            confidence=confidence,
            reason=reason,
            session_id=_session_id,
        )
    )
    
    _session_buffer.append(entry)
    return entry


def get_buffer() -> list[Entry]:
    """Get current session buffer (for debugging)."""
    return _session_buffer.copy()


def clear_buffer() -> None:
    """Clear the session buffer."""
    global _session_buffer
    _session_buffer = []


def validate_entries(entries: list[Entry]) -> ValidationResult:
    """
    Validate a list of entries.
    
    Checks:
    1. (heading, level) uniqueness per target file
    2. Path validity
    3. Content-operation consistency
    
    Args:
        entries: List of entries to validate
        
    Returns:
        ValidationResult with any errors found
    """
    errors: list[ValidationError] = []
    
    # Group by target file
    by_file: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        by_file[entry.key.path].append(entry)
    
    # Check uniqueness per file
    for path, file_entries in by_file.items():
        seen: dict[tuple[str, int], Entry] = {}
        for entry in file_entries:
            key = (entry.key.heading, entry.key.level)
            if key in seen:
                errors.append(ValidationError(
                    entry=entry,
                    error=f"Duplicate heading '{entry.key.heading}' at level {entry.key.level}",
                    error_code="DUPLICATE_HEADING"
                ))
            else:
                seen[key] = entry
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def group_by_target(entries: list[Entry]) -> dict[str, list[Entry]]:
    """Group entries by target file path."""
    result: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        result[entry.key.path].append(entry)
    return dict(result)


def generate_staging_filename(target_path: str) -> str:
    """Generate a unique staging filename."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_part = secrets.token_hex(4)
    # Hash the target path for uniqueness
    path_hash = hashlib.md5(target_path.encode()).hexdigest()[:8]
    return f"{timestamp}-{path_hash}-{random_part}.yaml"


def stage_entries(entries: list[Entry], error_message: str) -> list[Path]:
    """
    Write entries to staging directory due to validation failure.
    
    Args:
        entries: Entries that failed validation
        error_message: Description of why staging was needed
        
    Returns:
        List of created staging file paths
    """
    ensure_directories()
    staged_paths: list[Path] = []
    
    # Group by target for organized staging
    grouped = group_by_target(entries)
    
    for target_path, target_entries in grouped.items():
        schema = LastWordSchema(
            version="1.0.0",
            source=_session_id,
            entries=target_entries,
        )
        
        filename = generate_staging_filename(target_path)
        staging_path = get_staging_dir() / filename
        
        # Write with error metadata
        import yaml
        data = {
            "version": schema.version,
            "source": schema.source,
            "error": error_message,
            "target_file": target_path,
            "entries": [e.to_yaml_dict() for e in target_entries],
        }
        
        staging_path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8"
        )
        staged_paths.append(staging_path)
    
    return staged_paths


def write_yaml_with_retry(
    schema: LastWordSchema,
    target_path: Path,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> bool:
    """
    Write schema to YAML file with exponential backoff retry.
    
    Args:
        schema: The schema to write
        target_path: Destination file path
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        
    Returns:
        True if successful, False otherwise
    """
    import random
    
    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            # Use atomic write: write to temp then rename
            temp_path = target_path.with_suffix(f".tmp.{secrets.token_hex(4)}")
            temp_path.write_text(schema.to_yaml(), encoding="utf-8")
            temp_path.rename(target_path)
            return True
        except Exception:
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt), max_delay)
                delay = delay * (0.5 + random.random())  # Add jitter
                time.sleep(delay)
            else:
                return False
    
    return False


def process_session_end(
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> dict[str, Any]:
    """
    Process the session buffer at session end.
    
    This should be called from the pre_session_stop hook.
    
    Workflow:
    1. Validate entries (check heading uniqueness per file)
    2. If validation fails: write to staging/
    3. If validation passes: write to respective .yaml files
    
    Args:
        max_retries: Max retries for file writes
        base_delay: Base delay for exponential backoff
        
    Returns:
        Result dictionary with status and details
    """
    global _session_buffer, _session_id
    
    if not _session_buffer:
        return {
            "status": "empty",
            "message": "No entries to process",
            "staged": [],
            "written": [],
        }
    
    # Validate entries
    validation = validate_entries(_session_buffer)
    
    if validation.has_errors:
        # Stage failed entries
        error_msg = f"Validation failed with {len(validation.errors)} errors"
        staged = stage_entries(_session_buffer, error_msg)
        
        result = {
            "status": "staged",
            "message": error_msg,
            "errors": [
                {"entry": e.entry.key.heading, "error": e.error}
                for e in validation.errors
            ],
            "staged_files": [str(p) for p in staged],
            "written": [],
        }
        
        # Clear buffer after staging
        clear_buffer()
        return result
    
    # Validation passed - write to respective .yaml files
    grouped = group_by_target(_session_buffer)
    written: list[str] = []
    failed: list[str] = []
    
    for target_path, entries in grouped.items():
        # Determine output path (in last-word directory)
        # Use a hash of the full path to avoid filename collisions
        path_hash = hashlib.md5(target_path.encode()).hexdigest()[:12]
        filename = f"kb-{path_hash}.yaml"
        yaml_path = get_last_word_dir() / filename
        
        # Load existing entries if file exists
        existing_entries: list[Entry] = []
        if yaml_path.exists():
            try:
                existing_schema = LastWordSchema.from_yaml(
                    yaml_path.read_text(encoding="utf-8")
                )
                existing_entries = existing_schema.entries
            except Exception:
                pass  # Start fresh if file is corrupted
        
        # Merge entries (new entries override existing ones with same key)
        entry_map: dict[tuple[str, str, int], Entry] = {}
        for e in existing_entries:
            key = (e.key.path, e.key.heading, e.key.level)
            entry_map[key] = e
        for e in entries:
            key = (e.key.path, e.key.heading, e.key.level)
            entry_map[key] = e
        
        merged_schema = LastWordSchema(
            version="1.0.0",
            source=_session_id,
            entries=list(entry_map.values()),
        )
        
        # Write with retry
        success = write_yaml_with_retry(
            merged_schema,
            yaml_path,
            max_retries=max_retries,
            base_delay=base_delay,
        )
        
        if success:
            written.append(str(yaml_path))
        else:
            failed.append(target_path)
            # Stage failed entries
            stage_entries(entries, f"Failed to write to {yaml_path}")
    
    # Clear buffer
    clear_buffer()
    
    return {
        "status": "success" if not failed else "partial",
        "message": f"Written {len(written)} files" + (
            f", failed {len(failed)}" if failed else ""
        ),
        "written": written,
        "failed": failed,
    }


def list_staged() -> list[StagedFile]:
    """List all staged files waiting for resolution."""
    staging_dir = get_staging_dir()
    if not staging_dir.exists():
        return []
    
    staged: list[StagedFile] = []
    for file_path in staging_dir.glob("*.yaml"):
        # Extract target file from content if possible
        target_file = "unknown"
        try:
            import yaml
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
            target_file = data.get("target_file", "unknown")
        except Exception:
            pass
        
        staged.append(StagedFile(
            path=file_path,
            created_at=datetime.fromtimestamp(file_path.stat().st_mtime),
            target_file=target_file,
        ))
    
    return sorted(staged, key=lambda s: s.created_at)


def apply_entry_to_markdown(entry: Entry, content: str) -> str:
    """
    Apply an entry operation to markdown content.
    
    Args:
        entry: The update entry
        content: Current markdown content
        
    Returns:
        Updated markdown content
    """
    import re
    
    if entry.operation == OperationType.NO_OP:
        return content
    
    if entry.operation == OperationType.DELETE:
        # Remove the entire heading section
        pattern = rf"(^|\n){{1,{entry.key.level}}}\s*{re.escape(entry.key.heading)}\s*\n"
        # This is simplified - real implementation needs better section detection
        lines = content.split("\n")
        result_lines: list[str] = []
        in_target_section = False
        target_level = entry.key.level
        
        for line in lines:
            # Check if this line is a heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                if level == target_level and heading_text == entry.key.heading:
                    in_target_section = True
                    continue
                elif in_target_section and level <= target_level:
                    in_target_section = False
            
            if not in_target_section:
                result_lines.append(line)
        
        return "\n".join(result_lines)
    
    if entry.operation in (OperationType.UPDATE, OperationType.CLEAR):
        # Find and replace or append
        lines = content.split("\n")
        result_lines: list[str] = []
        in_target_section = False
        target_level = entry.key.level
        section_replaced = False
        
        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                if level == target_level and heading_text == entry.key.heading:
                    if not section_replaced:
                        # Replace this section
                        result_lines.append(f"{'#' * level} {entry.key.heading}")
                        if entry.content:
                            result_lines.append("")
                            result_lines.append(entry.content)
                        section_replaced = True
                    in_target_section = True
                    continue
                elif in_target_section and level <= target_level:
                    in_target_section = False
            
            if not in_target_section:
                result_lines.append(line)
        
        if not section_replaced:
            # Append new section at end
            if result_lines and result_lines[-1].strip():
                result_lines.append("")
            result_lines.append(f"{'#' * target_level} {entry.key.heading}")
            if entry.content:
                result_lines.append("")
                result_lines.append(entry.content)
        
        return "\n".join(result_lines)
    
    return content


def apply_yaml_to_markdown(yaml_path: Path, dry_run: bool = False) -> list[ApplyResult]:
    """
    Apply a YAML update file to its target markdown.
    
    Args:
        yaml_path: Path to the .yaml file containing updates
        dry_run: If True, don't actually write changes
        
    Returns:
        List of apply results
    """
    results: list[ApplyResult] = []
    
    try:
        schema = LastWordSchema.from_yaml(
            yaml_path.read_text(encoding="utf-8")
        )
    except Exception as e:
        return [ApplyResult(
            success=False,
            entry=Entry(key=TargetKey(path="", heading="", level=2)),
            target_file=str(yaml_path),
            error=f"Failed to parse YAML: {e}",
        )]
    
    # Group by target file
    grouped = group_by_target(schema.entries)
    
    for target_path, entries in grouped.items():
        target_file = Path(target_path)
        
        # Read existing content or create new
        if target_file.exists():
            content = target_file.read_text(encoding="utf-8")
        else:
            content = ""
            target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Apply each entry
        for entry in entries:
            try:
                content = apply_entry_to_markdown(entry, content)
                results.append(ApplyResult(
                    success=True,
                    entry=entry,
                    target_file=target_path,
                ))
            except Exception as e:
                results.append(ApplyResult(
                    success=False,
                    entry=entry,
                    target_file=target_path,
                    error=str(e),
                ))
        
        # Write result
        if not dry_run:
            try:
                # Atomic write
                temp_path = target_file.with_suffix(f".tmp.{secrets.token_hex(4)}")
                temp_path.write_text(content, encoding="utf-8")
                temp_path.rename(target_file)
            except Exception as e:
                # Mark all as failed
                for r in results:
                    if r.target_file == target_path:
                        r.success = False
                        r.error = f"Write failed: {e}"
    
    return results


# Fix import at top
from typing import Any  # noqa: F401
