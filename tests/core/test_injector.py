import pytest
from monoco.core.injection import PromptInjector


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "TEST.md"
    f.touch()
    return f


def test_inject_new_file(temp_file):
    injector = PromptInjector(temp_file)
    prompts = {"Test Feature": "This is test content."}

    assert injector.inject(prompts) is True

    content = temp_file.read_text(encoding="utf-8")
    assert "## Monoco" in content
    # New design uses bold instead of sub-headings
    assert "**Test Feature**" in content
    assert "This is test content." in content


def test_inject_idempotence(temp_file):
    injector = PromptInjector(temp_file)
    prompts = {"Test Feature": "This is test content."}

    injector.inject(prompts)
    first_content = temp_file.read_text(encoding="utf-8")

    # Run again - should be idempotent (no changes)
    result = injector.inject(prompts)
    second_content = temp_file.read_text(encoding="utf-8")

    assert first_content == second_content


def test_inject_update(temp_file):
    injector = PromptInjector(temp_file)
    injector.inject({"Feature A": "Old Content"})

    assert injector.inject({"Feature A": "New Content"}) is True

    content = temp_file.read_text(encoding="utf-8")
    assert "New Content" in content
    assert "Old Content" not in content


def test_remove(temp_file):
    injector = PromptInjector(temp_file)
    prompts = {"Test Feature": "To be removed"}

    injector.inject(prompts)
    assert "## Monoco" in temp_file.read_text(encoding="utf-8")

    assert injector.remove() is True
    content = temp_file.read_text(encoding="utf-8")
    # Check that the ## Monoco heading (not in comments) is removed
    import re
    assert not re.search(r"^## Monoco\s*$", content, re.MULTILINE)
    assert "To be removed" not in content
    # Root heading is preserved
    assert "# TEST" in content


def test_remove_preserves_surrounding(temp_file):
    content = """# My Document

Some intro text.

## Monoco
> Managed
Content here.

## Other Section
Some other text.
"""
    temp_file.write_text(content, encoding="utf-8")

    injector = PromptInjector(temp_file)
    injector.remove()

    new_content = temp_file.read_text(encoding="utf-8")
    assert "# My Document" in new_content
    assert "Some intro text." in new_content
    assert "## Other Section" in new_content
    assert "## Monoco" not in new_content
    assert "Content here." not in new_content


def test_remove_nonexistent(temp_file):
    injector = PromptInjector(temp_file)  # Empty file
    assert injector.remove() is False


def test_idempotence_multiple_runs(temp_file):
    """Test that running inject multiple times produces the same result."""
    injector = PromptInjector(temp_file, verbose=False)
    prompts = {"Feature A": "Content A", "Feature B": "Content B"}

    # First run
    injector.inject(prompts)
    content1 = temp_file.read_text(encoding="utf-8")

    # Second run
    injector.inject(prompts)
    content2 = temp_file.read_text(encoding="utf-8")

    # Third run
    injector.inject(prompts)
    content3 = temp_file.read_text(encoding="utf-8")

    assert content1 == content2 == content3


def test_file_header_comment_added(temp_file):
    """Test that file header comment is added to new files."""
    injector = PromptInjector(temp_file, verbose=False)
    injector.inject({"Feature": "Content"})

    content = temp_file.read_text(encoding="utf-8")
    assert "This file is partially managed by Monoco" in content


def test_file_header_not_duplicated(temp_file):
    """Test that file header comment is not duplicated on subsequent injections."""
    injector = PromptInjector(temp_file, verbose=False)
    prompts = {"Feature": "Content"}

    injector.inject(prompts)
    content1 = temp_file.read_text(encoding="utf-8")

    injector.inject(prompts)
    content2 = temp_file.read_text(encoding="utf-8")

    # Header should appear exactly once
    assert content1.count("This file is partially managed by Monoco") == 1
    assert content2.count("This file is partially managed by Monoco") == 1


def test_legacy_marker_migration(temp_file):
    """Test that old HTML markers are migrated to new format."""
    content = """# My Document

<!-- MONOCO_GENERATED_START -->

## Monoco

> **Auto-Generated**: Old content.

<!-- MONOCO_GENERATED_END -->
"""
    temp_file.write_text(content, encoding="utf-8")

    injector = PromptInjector(temp_file)
    injector.inject({"New Feature": "New content"})

    new_content = temp_file.read_text(encoding="utf-8")
    # Old markers should be removed
    assert "<!-- MONOCO_GENERATED_START -->" not in new_content
    assert "<!-- MONOCO_GENERATED_END -->" not in new_content
    # New content should be present
    assert "New content" in new_content
