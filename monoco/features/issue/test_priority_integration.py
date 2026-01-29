from monoco.features.issue.validator import IssueValidator
from monoco.features.issue.models import IssueMetadata
from datetime import datetime


def test_validator_namespaced_reference_in_body():
    validator = IssueValidator()
    meta = IssueMetadata(
        id="FEAT-0001",
        uid="123456",
        type="feature",
        status="open",
        stage="draft",
        title="Test Issue",
        created_at=datetime.now(),
        opened_at=datetime.now(),
        updated_at=datetime.now(),
        domains=["intelligence"],
        parent="EPIC-0000",
    )

    # Context: toolkit project, monoco workspace
    # Available IDs include namespaced versions
    all_ids = {"monoco::EPIC-0001", "toolkit::FEAT-0002"}

    # 1. Test namespaced reference in body
    content = """---
id: FEAT-0001
title: Test Issue
---

## FEAT-0001: Test Issue

This depends on monoco::EPIC-0001 and toolkit::FEAT-0002.
Broken one: other::FIX-9999.
"""

    diagnostics = validator.validate(
        meta, content, all_ids, current_project="toolkit", workspace_root="monoco"
    )

    # Should have 1 warning for other::FIX-9999
    warnings = [d for d in diagnostics if "Broken Reference" in d.message]
    assert len(warnings) == 1
    assert "other::FIX-9999" in warnings[0].message

    # 2. Test proximity resolution in body
    content_proximity = """---
id: FEAT-0001
title: Test Issue
---

## FEAT-0001: Test Issue

Referencing EPIC-0001 (should resolve to monoco::EPIC-0001 via root fallback).
Referencing FEAT-0002 (should resolve to toolkit::FEAT-0002 via proximity).
"""

    diagnostics = validator.validate(
        meta,
        content_proximity,
        all_ids,
        current_project="toolkit",
        workspace_root="monoco",
    )

    warnings = [d for d in diagnostics if "Broken Reference" in d.message]
    assert len(warnings) == 0  # Both should be resolved


def test_validator_parent_resolution():
    validator = IssueValidator()
    # Epic in toolkit
    meta = IssueMetadata(
        id="EPIC-0100",
        uid="111",
        type="epic",
        status="open",
        stage="draft",
        title="Sub Epic",
        parent="EPIC-0000",  # Root Epic in workspace root
        created_at=datetime.now(),
        opened_at=datetime.now(),
        updated_at=datetime.now(),
        domains=["intelligence"],
    )

    all_ids = {"monoco::EPIC-0000", "toolkit::EPIC-0100"}

    content = """---
id: EPIC-0100
parent: EPIC-0000
---
"""

    # Context: current=toolkit, root=monoco
    diagnostics = validator.validate(
        meta, content, all_ids, current_project="toolkit", workspace_root="monoco"
    )

    # Should be valid via root fallback
    errors = [d for d in diagnostics if d.severity == 1]  # DiagnosticSeverity.Error
    assert len(errors) == 0
