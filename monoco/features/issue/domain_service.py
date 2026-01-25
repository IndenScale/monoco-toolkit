from typing import Dict, Optional, Set
from monoco.core.config import get_config, DomainConfig


class DomainService:
    """
    Service for managing domain ontology, aliases, and validation.
    """

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or get_config().domains
        self._alias_map: Dict[str, str] = {}
        self._canonical_domains: Set[str] = set()
        self._build_index()

    def _build_index(self):
        self._alias_map.clear()
        self._canonical_domains.clear()

        for item in self.config.items:
            self._canonical_domains.add(item.name)
            for alias in item.aliases:
                self._alias_map[alias] = item.name

    def reload(self):
        """Reload configuration (if get_config returns new instance referenced)"""
        # Usually get_config() returns the singleton. If singleton updates, we might see it?
        # But we stored self.config.
        # Ideally we fetch fresh config if we want reload.
        self.config = get_config().domains
        self._build_index()

    def is_defined(self, domain: str) -> bool:
        """Check if domain is known (canonical or alias)."""
        return domain in self._canonical_domains or domain in self._alias_map

    def is_canonical(self, domain: str) -> bool:
        """Check if domain is a canonical name."""
        return domain in self._canonical_domains

    def is_alias(self, domain: str) -> bool:
        """Check if domain is a known alias."""
        return domain in self._alias_map

    def get_canonical(self, domain: str) -> Optional[str]:
        """
        Resolve alias to canonical name.
        Returns Canonical Name if found.
        Returns None if it is not an alias (could be canonical or unknown).
        """
        return self._alias_map.get(domain)

    def normalize(self, domain: str) -> str:
        """
        Normalize domain: return canonical if it's an alias, else return original.
        """
        return self._alias_map.get(domain, domain)

    def suggest_correction(self, domain: str) -> Optional[str]:
        """
        Suggest a correction for an unknown domain (Fuzzy matching).
        """
        # Simple fuzzy match implementation (optional)
        # Using simple containment or levenshtein if available?
        # Let's keep it simple: check if domain is substring of canonical?
        # Or simple typo check loop.

        # For now, just return None as fuzzy match is optional and requires dependency or complex logic
        return None
