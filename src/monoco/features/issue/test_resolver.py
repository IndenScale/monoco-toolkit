from monoco.features.issue.resolver import ReferenceResolver, ResolutionContext


def test_resolve_explicit_namespace():
    context = ResolutionContext(
        current_project="toolkit",
        workspace_root="monoco",
        available_ids={"toolkit::FEAT-0001", "monoco::FEAT-0001", "EPIC-0001"},
    )
    resolver = ReferenceResolver(context)

    # Explicitly project reference
    assert resolver.resolve("toolkit::FEAT-0001") == "toolkit::FEAT-0001"
    assert resolver.resolve("monoco::FEAT-0001") == "monoco::FEAT-0001"

    # Non-existent namespace
    assert resolver.resolve("other::FEAT-0001") is None


def test_resolve_proximity_current_project():
    context = ResolutionContext(
        current_project="toolkit",
        workspace_root="monoco",
        available_ids={
            "toolkit::FEAT-0001",
            "monoco::FEAT-0001",
        },
    )
    resolver = ReferenceResolver(context)

    # Should prefer current project
    assert resolver.resolve("FEAT-0001") == "toolkit::FEAT-0001"


def test_resolve_root_fallback():
    context = ResolutionContext(
        current_project="toolkit",
        workspace_root="monoco",
        available_ids={
            "monoco::EPIC-0000",
            "toolkit::FEAT-0001",
        },
    )
    resolver = ReferenceResolver(context)

    # Should fallback to root if not in current
    assert resolver.resolve("EPIC-0000") == "monoco::EPIC-0000"


def test_resolve_local_ids():
    context = ResolutionContext(
        current_project="toolkit",
        workspace_root="monoco",
        available_ids={
            "EPIC-9999",
        },
    )
    resolver = ReferenceResolver(context)

    # Should resolve plain local IDs
    assert resolver.resolve("EPIC-9999") == "EPIC-9999"


def test_priority_order():
    context = ResolutionContext(
        current_project="toolkit",
        workspace_root="monoco",
        available_ids={"toolkit::FEAT-0001", "monoco::FEAT-0001", "FEAT-0001"},
    )
    resolver = ReferenceResolver(context)

    # Order: toolkit::FEAT-0001 > monoco::FEAT-0001 > FEAT-0001
    assert resolver.resolve("FEAT-0001") == "toolkit::FEAT-0001"

    # If removed from toolkit context
    context.available_ids.remove("toolkit::FEAT-0001")
    resolver = ReferenceResolver(context)
    assert resolver.resolve("FEAT-0001") == "monoco::FEAT-0001"

    # If removed from root context
    context.available_ids.remove("monoco::FEAT-0001")
    resolver = ReferenceResolver(context)
    assert resolver.resolve("FEAT-0001") == "FEAT-0001"
