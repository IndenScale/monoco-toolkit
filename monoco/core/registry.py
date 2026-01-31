from typing import Dict, List
from monoco.core.feature import MonocoFeature


class FeatureRegistry:
    _features: Dict[str, MonocoFeature] = {}

    @classmethod
    def register(cls, feature: MonocoFeature):
        """Register a feature instance."""
        cls._features[feature.name] = feature

    @classmethod
    def get_features(cls) -> List[MonocoFeature]:
        """Get all registered features."""
        return list(cls._features.values())

    @classmethod
    def get_feature(cls, name: str) -> MonocoFeature:
        """Get a specific feature by name."""
        return cls._features.get(name)

    @classmethod
    def load_defaults(cls):
        """
        Load default core features.
        TODO: In the future, this could be dynamic via entry points.
        """
        # Import here to avoid circular dependencies at module level
        from monoco.features.issue.adapter import IssueFeature
        from monoco.features.spike.adapter import SpikeFeature
        from monoco.features.i18n.adapter import I18nFeature
        from monoco.features.memo.adapter import MemoFeature

        cls.register(IssueFeature())
        cls.register(SpikeFeature())
        cls.register(I18nFeature())
        cls.register(MemoFeature())

        
        from monoco.features.glossary.adapter import GlossaryFeature
        cls.register(GlossaryFeature())
        pass
