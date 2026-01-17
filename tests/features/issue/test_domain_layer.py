import pytest
from datetime import datetime
from monoco.features.issue.domain.models import Issue, IssueFrontmatter, IssueBody, ContentBlock
from monoco.features.issue.domain.parser import MarkdownParser
from monoco.features.issue.domain.lifecycle import TransitionService
from monoco.features.issue.models import IssueType, IssueStatus, IssueStage, IssueSolution
from monoco.features.issue.validator import IssueValidator

# Use explicit string concatenation to avoid leading newlines from triple quotes if any
SAMPLE_ISSUE_CONTENT = (
    "---\n"
    "id: FEAT-1234\n"
    "title: Test Feature\n"
    "type: feature\n"
    "status: open\n"
    "stage: doing\n"
    "created_at: 2023-01-01 10:00:00\n"
    "---\n\n"
    "## FEAT-1234: Test Feature\n\n"
    "## Objective\n\n"
    "This is a test.\n\n"
    "## Technical Tasks\n\n"
    "- [ ] Task 1\n"
    "- [x] Task 2\n"
)

def test_parser():
    issue = MarkdownParser.parse(SAMPLE_ISSUE_CONTENT)
    
    assert issue.frontmatter.id == "FEAT-1234"
    assert issue.frontmatter.status == IssueStatus.OPEN
    assert len(issue.body.blocks) > 0
    
    # Check Blocks
    blocks = issue.body.blocks
    
    task_blocks = [b for b in blocks if b.type == 'task_item']
    assert len(task_blocks) == 2
    assert task_blocks[0].metadata['checked'] is False
    assert task_blocks[1].metadata['checked'] is True
    # Line numbers should be roughly correct
    # Frontmatter is 8 lines (0-7)
    # Body starts at line 8
    assert task_blocks[0].line_start >= 8

def test_lifecycle():
    issue = MarkdownParser.parse(SAMPLE_ISSUE_CONTENT)
    service = TransitionService()
    
    # Current: Open/Doing
    # Allow: Submit (Review)
    transitions = service.get_available_transitions(issue)
    txn_names = [t.name for t in transitions]
    assert "submit" in txn_names
    assert "start" not in txn_names # Already doing
    
    # Apply submit
    issue = service.apply_transition(issue, "submit")
    assert issue.frontmatter.stage == IssueStage.REVIEW

def test_validator_refactor():
    validator = IssueValidator()
    
    issue = MarkdownParser.parse(SAMPLE_ISSUE_CONTENT)
    from monoco.features.issue.models import IssueMetadata
    meta = IssueMetadata(**issue.frontmatter.model_dump(exclude_none=True))
    
    diagnostics = validator.validate(meta, SAMPLE_ISSUE_CONTENT)
    
    error_diags = [d for d in diagnostics if d.severity == 1] # Error
    assert len(error_diags) == 0

def test_validator_incomplete_tasks():
    content = SAMPLE_ISSUE_CONTENT.replace("- [ ] Task 1", "- [ ] Task 1")
    # Change stage to REVIEW
    content = content.replace("stage: doing", "stage: review")
    content += "\n## Review Comments\n\n- [ ] Review" # Add review section to satisfy structure check
    
    issue = MarkdownParser.parse(content)
    from monoco.features.issue.models import IssueMetadata
    meta = IssueMetadata(**issue.frontmatter.model_dump(exclude_none=True))
    
    validator = IssueValidator()
    diagnostics = validator.validate(meta, content)
    
    # Should fail because of unchecked box in Review stage
    # "Technical Tasks must be resolved."
    
    errors = [d for d in diagnostics if "Technical Tasks must be resolved" in d.message]
    assert len(errors) > 0