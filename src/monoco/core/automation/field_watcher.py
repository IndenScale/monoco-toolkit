"""
Field Watcher - YAML Front Matter field change detection.

Part of the Event Automation Framework.
Provides field-level change detection for Markdown files with YAML Front Matter.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml

from monoco.core.watcher.base import FieldChange, ChangeType

logger = logging.getLogger(__name__)


@dataclass
class FieldCondition:
    """
    Condition for field value matching.
    
    Attributes:
        field: Field name to check
        operator: Comparison operator (eq, ne, gt, lt, gte, lte, in, contains)
        value: Expected value
    """
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains
    value: Any
    
    OPERATORS = {
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "gt": lambda a, b: a is not None and b is not None and a > b,
        "lt": lambda a, b: a is not None and b is not None and a < b,
        "gte": lambda a, b: a is not None and b is not None and a >= b,
        "lte": lambda a, b: a is not None and b is not None and a <= b,
        "in": lambda a, b: a in b if b is not None else False,
        "contains": lambda a, b: b in a if a is not None else False,
        "exists": lambda a, b: a is not None,
    }
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition against data."""
        actual_value = data.get(self.field)
        
        op_func = self.OPERATORS.get(self.operator)
        if not op_func:
            logger.warning(f"Unknown operator: {self.operator}")
            return False
        
        try:
            return op_func(actual_value, self.value)
        except Exception as e:
            logger.debug(f"Condition evaluation failed: {e}")
            return False


class YAMLFrontMatterExtractor:
    """
    Extracts YAML Front Matter from Markdown files.
    
    Provides methods to:
    - Parse YAML Front Matter from content
    - Extract specific fields
    - Detect field changes between versions
    """
    
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n',
        re.MULTILINE | re.DOTALL,
    )
    
    @classmethod
    def extract(cls, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract YAML Front Matter from markdown content.
        
        Args:
            content: Markdown file content
            
        Returns:
            Dict of front matter fields, or None if not found
        """
        match = cls.FRONTMATTER_PATTERN.match(content)
        if not match:
            return None
        
        yaml_content = match.group(1)
        
        try:
            return yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML front matter: {e}")
            return None
    
    @classmethod
    def extract_from_file(cls, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract YAML Front Matter from a file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            return cls.extract(content)
        except Exception as e:
            logger.debug(f"Could not read {file_path}: {e}")
            return None
    
    @classmethod
    def get_field(cls, content: str, field_name: str) -> Any:
        """Get a specific field from front matter."""
        frontmatter = cls.extract(content)
        if frontmatter is None:
            return None
        return frontmatter.get(field_name)
    
    @classmethod
    def detect_changes(
        cls,
        old_content: str,
        new_content: str,
        tracked_fields: Optional[List[str]] = None,
    ) -> List[FieldChange]:
        """
        Detect changes in front matter fields.
        
        Args:
            old_content: Previous file content
            new_content: Current file content
            tracked_fields: List of fields to track (None = all)
            
        Returns:
            List of FieldChange objects
        """
        old_fm = cls.extract(old_content) or {}
        new_fm = cls.extract(new_content) or {}
        
        changes = []
        
        # Determine which fields to check
        if tracked_fields:
            fields_to_check = tracked_fields
        else:
            fields_to_check = list(set(old_fm.keys()) | set(new_fm.keys()))
        
        for field_name in fields_to_check:
            old_value = old_fm.get(field_name)
            new_value = new_fm.get(field_name)
            
            if old_value != new_value:
                # Determine change type
                if old_value is None and new_value is not None:
                    change_type = ChangeType.CREATED
                elif old_value is not None and new_value is None:
                    change_type = ChangeType.DELETED
                else:
                    change_type = ChangeType.MODIFIED
                
                changes.append(FieldChange(
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    change_type=change_type,
                ))
        
        return changes


class FieldWatcher:
    """
    Watches specific fields for changes and triggers conditions.
    
    Maintains a cache of field values and emits events when:
    - Fields change
    - Conditions are met
    
    Example:
        >>> watcher = FieldWatcher(
        ...     tracked_fields=["status", "stage"],
        ... )
        >>> 
        >>> # Add a condition
        >>> watcher.add_condition(FieldCondition(
        ...     field="stage",
        ...     operator="eq",
        ...     value="doing",
        ... ))
        >>> 
        >>> # Check file
        >>> changes = watcher.check_file(path, content)
    """
    
    def __init__(
        self,
        tracked_fields: Optional[List[str]] = None,
    ):
        self.tracked_fields = tracked_fields
        self._field_cache: Dict[str, Dict[str, Any]] = {}  # file_path -> field_values
        self._conditions: List[FieldCondition] = []
        self._condition_callbacks: List[Callable[[str, FieldCondition, Dict[str, Any]], None]] = []
    
    def add_condition(self, condition: FieldCondition) -> None:
        """Add a condition to watch for."""
        self._conditions.append(condition)
    
    def add_callback(
        self,
        callback: Callable[[str, FieldCondition, Dict[str, Any]], None],
    ) -> None:
        """Add a callback for when conditions are met."""
        self._condition_callbacks.append(callback)
    
    def check_file(
        self,
        file_path: Union[str, Path],
        content: str,
    ) -> List[FieldChange]:
        """
        Check a file for field changes.
        
        Args:
            file_path: Path to the file
            content: Current file content
            
        Returns:
            List of field changes
        """
        path_key = str(file_path)
        
        # Extract current fields
        current_fm = YAMLFrontMatterExtractor.extract(content) or {}
        
        if self.tracked_fields:
            current_fields = {
                f: current_fm.get(f)
                for f in self.tracked_fields
            }
        else:
            current_fields = current_fm
        
        # Get cached fields
        cached_fields = self._field_cache.get(path_key, {})
        
        # Detect changes
        changes = []
        for field_name, new_value in current_fields.items():
            old_value = cached_fields.get(field_name)
            if old_value != new_value:
                changes.append(FieldChange(
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    change_type=ChangeType.MODIFIED if old_value is not None else ChangeType.CREATED,
                ))
        
        # Update cache
        self._field_cache[path_key] = current_fields
        
        # Check conditions
        if changes:
            self._check_conditions(path_key, current_fields)
        
        return changes
    
    def _check_conditions(self, file_path: str, fields: Dict[str, Any]) -> None:
        """Check if any conditions are met."""
        for condition in self._conditions:
            if condition.evaluate(fields):
                for callback in self._condition_callbacks:
                    try:
                        callback(file_path, condition, fields)
                    except Exception as e:
                        logger.error(f"Condition callback error: {e}")
    
    def get_cached_fields(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Get cached fields for a file."""
        return self._field_cache.get(str(file_path))
    
    def clear_cache(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """Clear the field cache."""
        if file_path:
            self._field_cache.pop(str(file_path), None)
        else:
            self._field_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        return {
            "tracked_files": len(self._field_cache),
            "tracked_fields": self.tracked_fields,
            "conditions": len(self._conditions),
        }
