from monoco.features.issue.domain.parser import MarkdownParser
from monoco.features.issue.domain.models import TaskItem

content = """---
id: FEAT-0001
type: feature
title: Test Issue
---

## FEAT-0001: Test Issue

This is a paragraph with an issue ID FEAT-1234 and a [[Toolkit::EPIC-0016]].

- [ ] Task 1 with [[FIX-9999]]
- [/] Doing task
- [x] Done task
"""

issue = MarkdownParser.parse(content)

print(f"Issue ID: {issue.id}")
print(f"Blocks count: {len(issue.body.blocks)}")

for i, block in enumerate(issue.body.blocks):
    print(f"Block {i} ({block.type}): {block.content[:30]}...")
    for span in block.spans:
        print(f"  Span ({span.type}): '{span.content}' at {span.range}")
        if "issue_id" in span.metadata:
            print(f"    Metadata issue_id: {span.metadata['issue_id']}")
