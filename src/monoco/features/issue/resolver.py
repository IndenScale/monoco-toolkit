"""
Reference Resolution Engine for Multi-Project Environments.

This module implements a priority-based resolution strategy for Issue ID references
in multi-project environments.

Resolution Priority:
1. Explicit Namespace (namespace::ID) - Highest priority
2. Proximity Rule (Current Project Context)
3. Root Fallback (Project Root)
"""

from typing import Optional, Set, Dict
from dataclasses import dataclass


@dataclass
class ResolutionContext:
    """Context information for reference resolution."""

    current_project: str
    """Name of the current project (e.g., 'toolkit', 'typedown')."""

    project_root: Optional[str] = None
    """Name of the project root (e.g., 'monoco')."""

    available_ids: Set[str] = None
    """Set of all available Issue IDs (both local and namespaced)."""

    def __post_init__(self):
        if self.available_ids is None:
            self.available_ids = set()


class ReferenceResolver:
    """
    Resolves Issue ID references with multi-project awareness.

    Supports:
    - Explicit namespace syntax: `namespace::ID`
    - Proximity-based resolution
    - Root fallback for global issues
    """

    def __init__(self, context: ResolutionContext):
        self.context = context

        # Build index for fast lookup
        self._local_ids: Set[str] = set()
        self._namespaced_ids: Dict[str, Set[str]] = {}

        for issue_id in context.available_ids:
            if "::" in issue_id:
                # Namespaced ID
                namespace, local_id = issue_id.split("::", 1)
                if namespace not in self._namespaced_ids:
                    self._namespaced_ids[namespace] = set()
                self._namespaced_ids[namespace].add(local_id)
            else:
                # Local ID
                self._local_ids.add(issue_id)

    def resolve(self, reference: str) -> Optional[str]:
        """
        Resolve an Issue ID reference to its canonical form.

        Args:
            reference: The reference to resolve (e.g., "FEAT-0001" or "toolkit::FEAT-0001")

        Returns:
            The canonical ID if found, None otherwise.
            For namespaced IDs, returns the full form (e.g., "toolkit::FEAT-0001").
            For local IDs, returns the short form (e.g., "FEAT-0001").

        Resolution Strategy:
        1. If reference contains "::", treat as explicit namespace
        2. Otherwise, apply proximity rule:
           a. Check current project context
           b. Check project root (if different from current)
           c. Check if exists as local ID
        """
        # Strategy 1: Explicit Namespace
        if "::" in reference:
            return self._resolve_explicit(reference)

        # Strategy 2: Proximity Rule
        return self._resolve_proximity(reference)

    def _resolve_explicit(self, reference: str) -> Optional[str]:
        """Resolve explicitly namespaced reference."""
        if reference in self.context.available_ids:
            return reference
        return None

    def _resolve_proximity(self, reference: str) -> Optional[str]:
        """
        Resolve reference using proximity rule.

        Priority:
        1. Current project namespace
        2. Project root namespace
        3. Local (unnamespaced) ID
        """
        # Priority 1: Current project
        current_namespaced = f"{self.context.current_project}::{reference}"
        if current_namespaced in self.context.available_ids:
            return current_namespaced

        # Priority 2: Workspace root (if different from current)
        if (
            self.context.workspace_root
            and self.context.workspace_root != self.context.current_project
        ):
            root_namespaced = f"{self.context.workspace_root}::{reference}"
            if root_namespaced in self.context.available_ids:
                return root_namespaced

        # Priority 3: Local ID
        if reference in self._local_ids:
            return reference

        return None

    def is_valid_reference(self, reference: str) -> bool:
        """Check if a reference can be resolved."""
        return self.resolve(reference) is not None

    def get_resolution_chain(self, reference: str) -> list[str]:
        """
        Get the resolution chain for debugging purposes.

        Returns a list of candidate IDs that were checked in order.
        """
        chain = []

        if "::" in reference:
            chain.append(reference)
        else:
            # Proximity chain
            chain.append(f"{self.context.current_project}::{reference}")

            if (
                self.context.project_root
                and self.context.project_root != self.context.current_project
            ):
                chain.append(f"{self.context.project_root}::{reference}")

            chain.append(reference)

        return chain


def resolve_reference(
    reference: str,
    context_project: str,
    available_ids: Set[str],
    workspace_root: Optional[str] = None,
) -> Optional[str]:
    """
    Convenience function for resolving a single reference.

    Args:
        reference: The Issue ID to resolve
        context_project: Current project name
        available_ids: Set of all available Issue IDs
        project_root: Optional project root name

    Returns:
        Resolved canonical ID or None if not found
    """
    context = ResolutionContext(
        current_project=context_project,
        project_root=project_root,
        available_ids=available_ids,
    )
    resolver = ReferenceResolver(context)
    return resolver.resolve(reference)
