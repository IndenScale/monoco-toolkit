import pytest
from pathlib import Path
from monoco.core.loader import FeatureLoader, FeatureModule, FeatureMetadata, FeatureContext, LifecycleState

def test_loader_discovery():
    loader = FeatureLoader()
    discovered = loader.discover()
    assert "issue" in discovered
    assert "memo" in discovered
    assert "agent" in discovered

def test_loader_load_and_mount():
    loader = FeatureLoader()
    # Discover and load issue feature
    loader.discover()
    feature = loader.load("issue")
    assert feature is not None
    assert feature.name == "issue"
    assert feature.state == LifecycleState.LOADED

    # Mount the feature
    context = FeatureContext(
        root=Path.cwd(),
        config={},
        registry=loader.registry
    )
    loader.mount("issue", context)
    assert feature.state == LifecycleState.MOUNTED

    # Unmount the feature
    loader.unmount("issue")
    assert feature.state == LifecycleState.UNLOADED

def test_registry_delegation():
    from monoco.core.registry import FeatureRegistry
    features = FeatureRegistry.get_features()
    # Should have at least the core features
    names = [f.name for f in features]
    assert "issue" in names
    assert "agent" in names
    assert "memo" in names
