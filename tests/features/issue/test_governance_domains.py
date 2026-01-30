import pytest
from pathlib import Path
import tempfile
import shutil
from monoco.features.issue import linter
from monoco.features.issue.validator import IssueValidator


@pytest.fixture
def temp_issues_root():
    temp_dir = tempfile.mkdtemp()
    root = Path(temp_dir)
    (root / "Epics/open").mkdir(parents=True)
    (root / "Features/open").mkdir(parents=True)
    (root / "Domains").mkdir(parents=True)
    yield root
    shutil.rmtree(temp_dir)


def test_domain_validation_success(temp_issues_root):
    # Setup valid domain
    domain_file = temp_issues_root / "Domains" / "Test Domain.md"
    domain_file.write_text("# Test Domain\n\nContent here.", encoding="utf-8")

    diagnostics = linter.check_integrity(temp_issues_root)

    # Filter DomainValidator errors
    domain_errors = [d for d in diagnostics if d.source == "DomainValidator"]
    assert len(domain_errors) == 0


def test_domain_validation_h1_mismatch(temp_issues_root):
    # Filename is 'A.md', but H1 is '# B'
    domain_file = temp_issues_root / "Domains" / "Alpha.md"
    domain_file.write_text("# Beta\n\nContent.", encoding="utf-8")

    diagnostics = linter.check_integrity(temp_issues_root)

    errors = [d for d in diagnostics if "does not match filename" in d.message]
    assert len(errors) == 1


def test_domain_validation_missing_h1(temp_issues_root):
    domain_file = temp_issues_root / "Domains" / "Empty.md"
    domain_file.write_text("No header at all.", encoding="utf-8")

    diagnostics = linter.check_integrity(temp_issues_root)

    errors = [d for d in diagnostics if "missing H1 title" in d.message]
    assert len(errors) == 1


def test_domain_validation_forbidden_prefix(temp_issues_root):
    domain_file = temp_issues_root / "Domains" / "Forbidden.md"
    domain_file.write_text("# Domain: Forbidden\n\nBad prefix.", encoding="utf-8")

    diagnostics = linter.check_integrity(temp_issues_root)

    errors = [d for d in diagnostics if "must not use 'Domain:' prefix" in d.message]
    assert len(errors) == 1


def test_issue_to_domain_reference_validation(temp_issues_root):
    # 1. Create a valid domain
    (temp_issues_root / "Domains" / "UX").write_text(
        "# UX\n\nUser Experience.", encoding="utf-8"
    )

    # 2. Create an issue referencing both valid and invalid domains
    content = """---
id: FEAT-0001
title: Test
type: feature
status: open
parent: EPIC-0000
domains: ["UX", "UnknownDomain"]
tags: ["#FEAT-0001", "#EPIC-0000"]
---
## FEAT-0001: Test
"""
    validator = IssueValidator(temp_issues_root)
    from monoco.features.issue.domain.parser import MarkdownParser
    from monoco.features.issue.models import IssueMetadata

    issue = MarkdownParser.parse(content)
    meta = IssueMetadata(**issue.frontmatter.model_dump(exclude_none=True))

    # We simulate the linter's workflow: collect then validate
    # Instead of running full linter, we just pass the valid_domains to validator
    valid_domains = {"UX"}

    diagnostics = validator.validate(meta, content, valid_domains=valid_domains)

    errors = [d for d in diagnostics if "Unknown Domain: 'UnknownDomain'" in d.message]
    assert len(errors) == 1

    # Check that 'UX' didn't trigger an error
    ux_errors = [
        d for d in diagnostics if "'UX'" in d.message and "Unknown Domain" in d.message
    ]
    assert len(ux_errors) == 0


def test_domain_language_check_warning(temp_issues_root, monkeypatch):
    # Mock config to force source_lang to 'zh'
    class MockI18n:
        source_lang = "zh"

    class MockConfig:
        i18n = MockI18n()
        project = None

    monkeypatch.setattr(
        "monoco.features.issue.linter.get_config", lambda p=None: MockConfig()
    )

    # Domain in English
    domain_file = temp_issues_root / "Domains" / "English.md"
    domain_file.write_text(
        "# English\n\nThis is strictly English content.", encoding="utf-8"
    )

    diagnostics = linter.check_integrity(temp_issues_root)

    warnings = [d for d in diagnostics if "Language Mismatch" in d.message]
    assert len(warnings) == 1
