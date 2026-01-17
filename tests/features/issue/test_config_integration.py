import pytest
from monoco.core.config import IssueSchemaConfig, TransitionConfig
from monoco.features.issue.engine.machine import StateMachine

def test_config_merge():
    # Base config
    base = IssueSchemaConfig(
        types=[], # Empty for base
        statuses=["open", "closed"],
        solutions=["fixed"]
    )
    
    # Overlay config
    overlay = IssueSchemaConfig(
        types=[], 
        statuses=["open", "closed", "archived"], # Add archived
        solutions=["fixed", "wontfix"]           # Add wontfix
    )
    
    merged = base.merge(overlay)
    
    assert "archived" in merged.statuses
    assert "wontfix" in merged.solutions
    assert "open" in merged.statuses

def test_custom_workflow():
    # Test that we can define a custom transition
    custom_transition = TransitionConfig(
        name="archive",
        label="Archive",
        from_status="closed",
        to_status="archived"
    )
    
    config = IssueSchemaConfig(
        statuses=["closed", "archived"],
        workflows=[custom_transition]
    )
    
    # Simulate Engine using this config
    # We need to construct StateMachineConfig from IssueSchemaConfig
    # In reality, get_engine does this mapping.
    
    # Let's verify merge logic for workflows
    base_workflow = TransitionConfig(name="close", label="Close", to_status="closed")
    base = IssueSchemaConfig(workflows=[base_workflow])
    
    overlay_workflow = TransitionConfig(name="archive", label="Archive", to_status="archived")
    overlay = IssueSchemaConfig(workflows=[overlay_workflow])
    
    merged = base.merge(overlay)
    
    names = [w.name for w in merged.workflows]
    assert "close" in names
    assert "archive" in names
