---
id: FIX-0001
type: fix
status: closed
title: Fix monoco issue formatting errors
created_at: "2026-01-09"
dependencies: []
related: ["FEAT-0009"]
solution: implemented
tags: []
---

## Objective

Fix format errors in `monoco issue` command output to ensure clean, valid markdown and filenames.

Recent usage (e.g., `FEAT-0009`) has produced files with:

1. **Duplicated hyphens** in filenames (e.g., `FEAT-0009--spike-.md`).
2. **Missing heading content** in the generated body.
3. **Incorrect escape sequences**, inserting `\n` literals instead of actual newlines.
4. **Date quoting issues** in frontmatter (e.g., inconsistent or incorrect quote usage).

## Acceptance Criteria

- [ ] Issue filenames are cleanly slugified (no double hyphens, no trailing hyphens).
- [ ] Generated Markdown content has proper formatting (headings, spacing).
- [ ] Newlines in templates or user input are rendered correctly, not as escaped literals.
- [ ] Date fields in frontmatter are formatted consistently (standardize on single/double quotes or none).

## Technical Tasks

- [x] Debug the `monoco issue create` command implementation in `Toolkit`.
- [x] Fix title processing/slugification logic.
- [x] Fix template rendering engine to handle escape sequences correctly.
- [x] Verify fix by creating a test issue with special characters and spacing.
- [x] Date fields in frontmatter are formatted consistently (standardize on single/double quotes or none).
