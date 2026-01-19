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
    assert "## Monoco Toolkit" in content
    assert "### Test Feature" in content
    assert "This is test content." in content


def test_inject_idempotence(temp_file):
    injector = PromptInjector(temp_file)
    prompts = {"Test Feature": "This is test content."}

    injector.inject(prompts)
    first_content = temp_file.read_text(encoding="utf-8")

    # Run again
    assert injector.inject(prompts) is False
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
    assert "## Monoco Toolkit" in temp_file.read_text(encoding="utf-8")

    assert injector.remove() is True
    content = temp_file.read_text(encoding="utf-8")
    assert "## Monoco Toolkit" not in content
    assert "To be removed" not in content
    assert content.strip() == ""


def test_remove_preserves_surrounding(temp_file):
    content = """# My Document

Some intro text.

## Monoco Toolkit
> Managed

### Feature
Content

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
    assert "## Monoco Toolkit" not in new_content
    assert "Content" not in new_content


def test_remove_nonexistent(temp_file):
    injector = PromptInjector(temp_file)  # Empty file
    assert injector.remove() is False
