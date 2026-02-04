"""
Universal Hooks: Manager

Core manager class for discovering, validating, and organizing
Universal Hooks across Git, IDE, and Agent contexts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .models import (
    GitEvent,
    AgentEvent,
    IDEEvent,
    HookGroup,
    HookMetadata,
    HookType,
    ParsedHook,
)
from .parser import HookParser, ParseError


@dataclass
class ValidationResult:
    """Result of validating a hook."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)


class HookDispatcher(ABC):
    """
    Abstract base class for hook type dispatchers.

    Dispatchers are responsible for executing hooks of a specific type.
    They are registered with UniversalHookManager to handle hooks
    for their respective types.
    """

    def __init__(self, hook_type: HookType, provider: Optional[str] = None):
        """
        Initialize the dispatcher.

        Args:
            hook_type: The type of hooks this dispatcher handles
            provider: Optional provider name (for agent/ide types)
        """
        self.hook_type = hook_type
        self.provider = provider

    @property
    def key(self) -> str:
        """Get the unique key for this dispatcher."""
        if self.hook_type == HookType.GIT:
            return self.hook_type.value
        return f"{self.hook_type.value}:{self.provider}"

    @abstractmethod
    def can_execute(self, hook: ParsedHook) -> bool:
        """
        Check if this dispatcher can execute the given hook.

        Args:
            hook: The parsed hook to check

        Returns:
            True if this dispatcher can execute the hook
        """
        pass

    @abstractmethod
    def execute(self, hook: ParsedHook, context: Optional[dict] = None) -> bool:
        """
        Execute a hook.

        Args:
            hook: The parsed hook to execute
            context: Optional execution context

        Returns:
            True if execution succeeded
        """
        pass


class UniversalHookManager:
    """
    Core manager for Universal Hooks system.

    This class provides:
    - Scanning directories for hook scripts with Front Matter metadata
    - Validating hook metadata integrity
    - Organizing hooks by type and provider
    - Registering dispatchers for different hook types

    Example usage:
        manager = UniversalHookManager()

        # Scan for hooks
        groups = manager.scan("./hooks")

        # Validate a hook
        result = manager.validate(hook)

        # Register a dispatcher
        manager.register_dispatcher(HookType.GIT, GitHookDispatcher())
    """

    def __init__(self):
        """Initialize the Universal Hook Manager."""
        self.parser = HookParser()
        self._dispatchers: dict[str, HookDispatcher] = {}
        self._validation_hooks: list[Callable[[HookMetadata], Optional[str]]] = []

    def scan(
        self,
        directory: Path | str,
        pattern: str = "*",
    ) -> dict[str, HookGroup]:
        """
        Recursively scan a directory for hook scripts.

        Discovers all hook scripts with valid Front Matter metadata and
        organizes them into groups by type and provider.

        Args:
            directory: Directory to scan
            pattern: Glob pattern for matching files (default: "*")

        Returns:
            Dictionary mapping group keys to HookGroup objects
        """
        dir_path = Path(directory)
        groups: dict[str, HookGroup] = {}

        # Parse all hooks in the directory
        parsed_hooks = self.parser.parse_directory(dir_path, pattern)

        # Organize hooks into groups
        for hook in parsed_hooks:
            key = hook.metadata.get_key()

            if key not in groups:
                groups[key] = HookGroup(
                    key=key,
                    hook_type=hook.metadata.type,
                    provider=hook.metadata.provider,
                )

            groups[key].add_hook(hook)

        return groups

    def validate(self, hook: ParsedHook | HookMetadata) -> ValidationResult:
        """
        Validate hook metadata integrity.

        Performs both Pydantic model validation and additional
        semantic checks (e.g., provider required for agent/ide types).

        Args:
            hook: The hook or metadata to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)

        # Get metadata from hook if needed
        if isinstance(hook, ParsedHook):
            metadata = hook.metadata
            script_path = hook.script_path
        else:
            metadata = hook
            script_path = None

        # Basic Pydantic validation already happened during parsing
        # but we can add additional semantic checks here

        # Check for valid event types
        self._validate_event(metadata, result)

        # Check for script executability (if we have a path)
        if script_path:
            self._validate_script_executable(script_path, result)

        # Check matcher patterns are valid
        if metadata.matcher:
            self._validate_matchers(metadata.matcher, result)

        # Run custom validation hooks
        for validator in self._validation_hooks:
            error = validator(metadata)
            if error:
                result.add_error(error)

        return result

    def _validate_event(self, metadata: HookMetadata, result: ValidationResult) -> None:
        """Validate that the event is appropriate for the hook type."""
        event_validators = {
            HookType.GIT: lambda e: e in {e.value for e in GitEvent},
            HookType.AGENT: lambda e: e in {e.value for e in AgentEvent},
            HookType.IDE: lambda e: e in {e.value for e in IDEEvent},
        }

        validator = event_validators.get(metadata.type)
        if validator and not validator(metadata.event):
            valid_events = {
                HookType.GIT: GitEvent,
                HookType.AGENT: AgentEvent,
                HookType.IDE: IDEEvent,
            }.get(metadata.type)

            if valid_events:
                valid_list = ", ".join(e.value for e in valid_events)
                result.add_error(
                    f"Invalid event '{metadata.event}' for type '{metadata.type.value}'. "
                    f"Valid events: {valid_list}"
                )

    def _validate_script_executable(
        self, path: Path, result: ValidationResult
    ) -> None:
        """Validate that the script file is executable."""
        if not path.exists():
            result.add_error(f"Script file does not exist: {path}")
            return

        # Check if file is executable (on Unix systems)
        import stat

        try:
            mode = path.stat().st_mode
            if not (mode & stat.S_IXUSR):
                result.add_warning(
                    f"Script may not be executable (missing execute permission): {path}"
                )
        except Exception:
            # If we can't stat the file, just skip this check
            pass

    def _validate_matchers(self, matchers: list[str], result: ValidationResult) -> None:
        """Validate glob patterns in matchers."""
        import fnmatch

        for pattern in matchers:
            # Basic pattern validation - fnmatch doesn't raise errors
            # but we can check for obviously invalid patterns
            if not pattern:
                result.add_warning("Empty matcher pattern found")
            elif pattern.startswith("!") and len(pattern) == 1:
                result.add_warning("Negation pattern '!' without actual pattern")

    def register_dispatcher(
        self,
        hook_type: HookType,
        dispatcher: HookDispatcher,
    ) -> None:
        """
        Register a dispatcher for a hook type.

        Args:
            hook_type: The type of hooks this dispatcher handles
            dispatcher: The dispatcher instance
        """
        key = dispatcher.key
        self._dispatchers[key] = dispatcher

    def unregister_dispatcher(
        self,
        hook_type: HookType,
        provider: Optional[str] = None,
    ) -> bool:
        """
        Unregister a dispatcher.

        Args:
            hook_type: The type of hooks
            provider: Optional provider name

        Returns:
            True if a dispatcher was removed
        """
        if hook_type == HookType.GIT:
            key = hook_type.value
        else:
            key = f"{hook_type.value}:{provider}"

        if key in self._dispatchers:
            del self._dispatchers[key]
            return True
        return False

    def get_dispatcher(
        self,
        hook_type: HookType,
        provider: Optional[str] = None,
    ) -> Optional[HookDispatcher]:
        """
        Get a registered dispatcher.

        Args:
            hook_type: The type of hooks
            provider: Optional provider name

        Returns:
            The dispatcher if registered, None otherwise
        """
        if hook_type == HookType.GIT:
            key = hook_type.value
        else:
            key = f"{hook_type.value}:{provider}"

        return self._dispatchers.get(key)

    def list_dispatchers(self) -> dict[str, HookDispatcher]:
        """
        List all registered dispatchers.

        Returns:
            Dictionary mapping keys to dispatcher instances
        """
        return self._dispatchers.copy()

    def add_validation_hook(
        self,
        validator: Callable[[HookMetadata], Optional[str]],
    ) -> None:
        """
        Add a custom validation function.

        Args:
            validator: Function that takes HookMetadata and returns error message
                      or None if valid
        """
        self._validation_hooks.append(validator)

    def get_parsing_errors(self) -> list[ParseError]:
        """Get all parsing errors from the last scan operation."""
        return self.parser.get_errors()

    def clear_parsing_errors(self) -> None:
        """Clear parsing errors."""
        self.parser.clear_errors()
