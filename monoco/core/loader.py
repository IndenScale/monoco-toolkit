"""
Unified Module Loader and Lifecycle Management for Monoco Features.

This module provides dynamic discovery, loading, and lifecycle management
for Monoco feature modules. It implements the FeatureModule protocol with
standard lifecycle hooks (mount/unmount) and supports dependency injection
and lazy loading for improved startup performance.
"""

import importlib
import importlib.util
import inspect
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

from monoco.core.feature import IntegrationData, MonocoFeature


T = TypeVar("T")


class LifecycleState:
    """Lifecycle states for a feature module."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    MOUNTING = "mounting"
    MOUNTED = "mounted"
    UNMOUNTING = "unmounting"
    ERROR = "error"


@dataclass
class FeatureMetadata:
    """Metadata for a feature module."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    lazy: bool = False  # Whether this feature supports lazy loading
    priority: int = 100  # Lower values = higher priority for loading order


class FeatureModule(MonocoFeature, ABC):
    """
    Abstract base class for all Monoco feature modules.

    Features must implement this protocol to participate in the unified
    module loading system with full lifecycle management.

    Lifecycle:
        1. Discovery: Feature is discovered in monoco/features/
        2. Load: Module is imported and class instantiated
        3. Mount: Feature is mounted (initialized) with workspace context
        4. Runtime: Feature is active and responding to commands
        5. Unmount: Feature is gracefully shut down

    Example:
        class MyFeature(FeatureModule):
            @property
            def metadata(self) -> FeatureMetadata:
                return FeatureMetadata(
                    name="myfeature",
                    version="1.0.0",
                    dependencies=["core"]
                )

            def mount(self, context: FeatureContext) -> None:
                # Initialize feature with workspace context
                pass

            def unmount(self) -> None:
                # Cleanup resources
                pass
    """

    _state: str = LifecycleState.UNLOADED
    _context: Optional["FeatureContext"] = None
    _instance_id: Optional[str] = None

    @property
    @abstractmethod
    def metadata(self) -> FeatureMetadata:
        """Return feature metadata including dependencies."""
        pass

    @property
    def name(self) -> str:
        """Unique identifier for the feature (from metadata)."""
        return self.metadata.name

    @property
    def state(self) -> str:
        """Current lifecycle state of the feature."""
        return self._state

    @property
    def context(self) -> Optional["FeatureContext"]:
        """The feature context if mounted."""
        return self._context

    def mount(self, context: "FeatureContext") -> None:
        """
        Lifecycle hook: Mount the feature with workspace context.

        Called when the feature is being activated. The feature should
        initialize any resources needed for operation.

        Args:
            context: The feature context containing workspace and config.

        Raises:
            FeatureMountError: If mounting fails.
        """
        self._context = context
        self._state = LifecycleState.MOUNTING
        try:
            self._on_mount(context)
            self._state = LifecycleState.MOUNTED
        except Exception as e:
            self._state = LifecycleState.ERROR
            raise FeatureMountError(f"Failed to mount feature '{self.name}': {e}") from e

    def unmount(self) -> None:
        """
        Lifecycle hook: Unmount the feature and cleanup resources.

        Called when the feature is being deactivated or the application
        is shutting down. The feature should release all resources.

        Raises:
            FeatureUnmountError: If unmounting fails.
        """
        self._state = LifecycleState.UNMOUNTING
        try:
            self._on_unmount()
            self._state = LifecycleState.UNLOADED
        except Exception as e:
            self._state = LifecycleState.ERROR
            raise FeatureUnmountError(f"Failed to unmount feature '{self.name}': {e}") from e
        finally:
            self._context = None

    def _on_mount(self, context: "FeatureContext") -> None:
        """
        Override this method to implement mount logic.
        Default implementation delegates to legacy initialize().
        """
        if hasattr(self, "initialize"):
            # Legacy support: call initialize if defined
            root = context.root if context else Path.cwd()
            config = context.config if context else {}
            self.initialize(root, config)  # type: ignore

    def _on_unmount(self) -> None:
        """
        Override this method to implement unmount logic.
        """
        pass

    def initialize(self, root: Path, config: Dict) -> None:
        """
        Legacy lifecycle hook: Physical Structure Initialization.

        New features should override _on_mount() instead.
        """
        pass

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """
        Lifecycle hook: Agent Environment Integration.

        Called during sync to provide prompts and skills.
        """
        return IntegrationData()


@dataclass
class FeatureContext:
    """
    Context provided to features during mount/unmount operations.
    """

    root: Path
    config: Dict[str, Any]
    registry: "FeatureRegistry"
    services: "ServiceContainer" = field(default_factory=lambda: ServiceContainer())

    def get_service(self, interface: Type[T]) -> Optional[T]:
        """Get a service from the service container."""
        return self.services.get(interface)


class ServiceContainer:
    """
    Simple IoC container for dependency injection.

    Supports registration of services by interface and implementation.
    """

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}

    def register(self, interface: Type[T], implementation: T) -> None:
        """Register a service instance for an interface."""
        self._services[interface] = implementation

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for lazy instantiation."""
        self._factories[interface] = factory

    def get(self, interface: Type[T]) -> Optional[T]:
        """Get a service implementation by interface."""
        if interface in self._services:
            return self._services[interface]
        if interface in self._factories:
            instance = self._factories[interface]()
            self._services[interface] = instance
            return instance
        return None

    def has(self, interface: Type) -> bool:
        """Check if a service is registered."""
        return interface in self._services or interface in self._factories


class FeatureError(Exception):
    """Base exception for feature-related errors."""
    pass


class FeatureMountError(FeatureError):
    """Raised when feature mounting fails."""
    pass


class FeatureUnmountError(FeatureError):
    """Raised when feature unmounting fails."""
    pass


class FeatureLoadError(FeatureError):
    """Raised when feature loading fails."""
    pass


class FeatureDependencyError(FeatureError):
    """Raised when feature dependencies cannot be resolved."""
    pass


class FeatureRegistry:
    """
    Registry for managing feature modules.

    Maintains a collection of registered features and provides
    lifecycle management operations.
    """

    def __init__(self):
        self._features: Dict[str, FeatureModule] = {}
        self._states: Dict[str, str] = {}
        self._context: Optional[FeatureContext] = None

    def register(self, feature: FeatureModule) -> None:
        """Register a feature instance."""
        self._features[feature.name] = feature
        self._states[feature.name] = feature.state

    def unregister(self, name: str) -> None:
        """Unregister a feature by name."""
        if name in self._features:
            del self._features[name]
            del self._states[name]

    def get(self, name: str) -> Optional[FeatureModule]:
        """Get a feature by name."""
        return self._features.get(name)

    def get_all(self) -> List[FeatureModule]:
        """Get all registered features."""
        return list(self._features.values())

    def get_mounted(self) -> List[FeatureModule]:
        """Get all mounted features."""
        return [f for f in self._features.values() if f.state == LifecycleState.MOUNTED]

    def is_registered(self, name: str) -> bool:
        """Check if a feature is registered."""
        return name in self._features

    def is_mounted(self, name: str) -> bool:
        """Check if a feature is mounted."""
        return self._states.get(name) == LifecycleState.MOUNTED

    def mount_all(self, context: FeatureContext) -> Dict[str, Exception]:
        """
        Mount all registered features.

        Returns a dictionary of errors keyed by feature name.
        """
        self._context = context
        errors = {}

        # Sort features by priority (lower = higher priority)
        sorted_features = sorted(
            self._features.values(),
            key=lambda f: f.metadata.priority if hasattr(f, "metadata") else 100
        )

        for feature in sorted_features:
            try:
                feature.mount(context)
                self._states[feature.name] = LifecycleState.MOUNTED
            except Exception as e:
                errors[feature.name] = e
                self._states[feature.name] = LifecycleState.ERROR

        return errors

    def unmount_all(self) -> Dict[str, Exception]:
        """
        Unmount all mounted features.

        Returns a dictionary of errors keyed by feature name.
        """
        errors = {}

        # Unmount in reverse priority order
        sorted_features = sorted(
            self._features.values(),
            key=lambda f: f.metadata.priority if hasattr(f, "metadata") else 100,
            reverse=True
        )

        for feature in sorted_features:
            if feature.state == LifecycleState.MOUNTED:
                try:
                    feature.unmount()
                    self._states[feature.name] = LifecycleState.UNLOADED
                except Exception as e:
                    errors[feature.name] = e

        self._context = None
        return errors


class FeatureLoader:
    """
    Dynamic feature loader with discovery and lifecycle management.

    Discovers features in the monoco.features package and provides
    lazy loading capabilities for improved startup performance.
    """

    FEATURES_PACKAGE = "monoco.features"
    ADAPTER_MODULE = "adapter"
    FEATURE_CLASS_NAME = "Feature"

    def __init__(
        self,
        registry: Optional[FeatureRegistry] = None,
        service_container: Optional[ServiceContainer] = None,
    ):
        self.registry = registry or FeatureRegistry()
        self.services = service_container or ServiceContainer()
        self._discovered: Dict[str, Type[FeatureModule]] = {}
        self._loaded: Dict[str, FeatureModule] = {}
        self._lazy_queue: Set[str] = set()
        self._load_hooks: List[Callable[[FeatureModule], None]] = []
        self._mount_hooks: List[Callable[[FeatureModule], None]] = []

    def add_load_hook(self, hook: Callable[[FeatureModule], None]) -> None:
        """Add a hook to be called after a feature is loaded."""
        self._load_hooks.append(hook)

    def add_mount_hook(self, hook: Callable[[FeatureModule], None]) -> None:
        """Add a hook to be called after a feature is mounted."""
        self._mount_hooks.append(hook)

    def discover(self, package: Optional[str] = None) -> List[str]:
        """
        Discover available features in the features package.

        Scans subpackages of monoco.features for adapter modules
        containing FeatureModule implementations.

        Args:
            package: Package to scan (defaults to monoco.features).

        Returns:
            List of discovered feature names.
        """
        package = package or self.FEATURES_PACKAGE
        discovered = []

        try:
            import monoco.features as features_pkg

            package_path = Path(features_pkg.__file__).parent

            for item in package_path.iterdir():
                if not item.is_dir() or item.name.startswith("_"):
                    continue

                feature_name = item.name
                adapter_path = item / f"{self.ADAPTER_MODULE}.py"

                if adapter_path.exists():
                    self._discovered[feature_name] = None  # Mark as discovered, not loaded
                    discovered.append(feature_name)

        except ImportError:
            pass

        return discovered

    def load(self, name: str, lazy: bool = False) -> Optional[FeatureModule]:
        """
        Load a feature by name.

        Args:
            name: Feature name (subpackage name in monoco.features).
            lazy: If True, defer actual instantiation until mount.

        Returns:
            Loaded FeatureModule instance or None if loading failed.

        Raises:
            FeatureLoadError: If the feature cannot be loaded.
        """
        if name in self._loaded:
            return self._loaded[name]

        if lazy:
            self._lazy_queue.add(name)
            return None

        try:
            module_path = f"{self.FEATURES_PACKAGE}.{name}.{self.ADAPTER_MODULE}"
            module = importlib.import_module(module_path)

            # Find FeatureModule subclass in the module
            feature_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    inspect.isclass(attr)
                    and issubclass(attr, FeatureModule)
                    and attr is not FeatureModule
                ):
                    feature_class = attr
                    break

            # Fallback: Check for legacy MonocoFeature implementations
            if feature_class is None:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, MonocoFeature)
                        and attr is not MonocoFeature
                        and attr is not FeatureModule
                    ):
                        # Wrap legacy feature in adapter
                        feature_class = self._wrap_legacy_feature(attr)
                        break

            if feature_class is None:
                raise FeatureLoadError(f"No FeatureModule found in {module_path}")

            # Instantiate the feature
            instance = feature_class()
            instance._state = LifecycleState.LOADED
            self._loaded[name] = instance
            self.registry.register(instance)

            # Call load hooks
            for hook in self._load_hooks:
                hook(instance)

            return instance

        except ImportError as e:
            raise FeatureLoadError(f"Failed to import feature '{name}': {e}") from e
        except Exception as e:
            raise FeatureLoadError(f"Failed to load feature '{name}': {e}") from e

    def load_all(self, lazy: bool = False) -> Dict[str, Optional[FeatureModule]]:
        """
        Load all discovered features.

        Args:
            lazy: If True, defer non-critical feature loading.

        Returns:
            Dictionary mapping feature names to instances (or None for lazy).
        """
        if not self._discovered:
            self.discover()

        results = {}
        for name in self._discovered:
            # Check if feature supports lazy loading
            should_lazy = lazy and self._is_lazy_feature(name)
            try:
                results[name] = self.load(name, lazy=should_lazy)
            except FeatureLoadError as e:
                results[name] = None
                # Log error but continue loading other features
                print(f"Warning: {e}")

        return results

    def mount(self, name: str, context: FeatureContext) -> None:
        """
        Mount a specific feature.

        Args:
            name: Feature name.
            context: Feature context for mounting.

        Raises:
            FeatureError: If the feature is not loaded or cannot be mounted.
        """
        if name in self._lazy_queue:
            # Load now if it was deferred
            self._lazy_queue.discard(name)
            self.load(name, lazy=False)

        feature = self.registry.get(name)
        if feature is None:
            raise FeatureError(f"Feature '{name}' is not loaded")

        feature.mount(context)

        for hook in self._mount_hooks:
            hook(feature)

    def mount_all(self, context: FeatureContext) -> Dict[str, Exception]:
        """
        Mount all loaded features.

        Args:
            context: Feature context for mounting.

        Returns:
            Dictionary of errors keyed by feature name.
        """
        # Load any remaining lazy features first
        for name in list(self._lazy_queue):
            self.load(name, lazy=False)
        self._lazy_queue.clear()

        return self.registry.mount_all(context)

    def unmount(self, name: str) -> None:
        """Unmount a specific feature."""
        feature = self.registry.get(name)
        if feature:
            feature.unmount()

    def unmount_all(self) -> Dict[str, Exception]:
        """Unmount all mounted features."""
        return self.registry.unmount_all()

    def _is_lazy_feature(self, name: str) -> bool:
        """Check if a feature supports lazy loading."""
        # For now, use a simple heuristic based on known non-critical features
        # In the future, this could be determined from metadata
        lazy_features = {"glossary", "i18n"}
        return name in lazy_features

    def _wrap_legacy_feature(self, legacy_class: Type[MonocoFeature]) -> Type[FeatureModule]:
        """
        Wrap a legacy MonocoFeature class to support the new FeatureModule protocol.

        This allows gradual migration of existing features.
        """

        class LegacyFeatureAdapter(FeatureModule):
            def __init__(self):
                self._legacy = legacy_class()
                self._state = LifecycleState.UNLOADED

            @property
            def metadata(self) -> FeatureMetadata:
                return FeatureMetadata(
                    name=self._legacy.name,
                    version="1.0.0",
                    description=f"Legacy feature: {self._legacy.name}",
                )

            @property
            def name(self) -> str:
                return self._legacy.name

            def _on_mount(self, context: FeatureContext) -> None:
                self._legacy.initialize(context.root, context.config)

            def integrate(self, root: Path, config: Dict) -> IntegrationData:
                return self._legacy.integrate(root, config)

        # Preserve the original class name
        LegacyFeatureAdapter.__name__ = f"{legacy_class.__name__}Adapter"
        return LegacyFeatureAdapter


# Global loader instance for convenience
_default_loader: Optional[FeatureLoader] = None


def get_loader() -> FeatureLoader:
    """Get the default feature loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = FeatureLoader()
    return _default_loader


def set_loader(loader: FeatureLoader) -> None:
    """Set the default feature loader instance."""
    global _default_loader
    _default_loader = loader
