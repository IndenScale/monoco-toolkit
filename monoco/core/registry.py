from typing import Dict, List, Optional
from monoco.core.feature import MonocoFeature
from monoco.core.loader import FeatureLoader, FeatureRegistry as LoaderFeatureRegistry


class FeatureRegistry:
    """
    Feature registry that wraps the new unified FeatureLoader.
    
    This class provides backward compatibility while delegating to the
    new FeatureLoader for dynamic discovery and lifecycle management.
    """

    _loader: Optional[FeatureLoader] = None

    @classmethod
    def _get_loader(cls) -> FeatureLoader:
        """Get or create the default feature loader."""
        if cls._loader is None:
            cls._loader = FeatureLoader()
            # Discover and load all features
            cls._loader.discover()
            cls._loader.load_all()
        return cls._loader

    @classmethod
    def register(cls, feature: MonocoFeature):
        """Register a feature instance."""
        loader = cls._get_loader()
        loader.registry.register(feature)  # type: ignore

    @classmethod
    def get_features(cls) -> List[MonocoFeature]:
        """Get all registered features."""
        loader = cls._get_loader()
        return loader.registry.get_all()  # type: ignore

    @classmethod
    def get_feature(cls, name: str) -> Optional[MonocoFeature]:
        """Get a specific feature by name."""
        loader = cls._get_loader()
        return loader.registry.get(name)  # type: ignore

    @classmethod
    def load_defaults(cls):
        """
        Load default core features using the unified FeatureLoader.
        
        This method discovers and loads all features from monoco/features/
        automatically, replacing the manual registration approach.
        """
        loader = cls._get_loader()
        # Features are already discovered and loaded in _get_loader
        # This method is kept for backward compatibility
