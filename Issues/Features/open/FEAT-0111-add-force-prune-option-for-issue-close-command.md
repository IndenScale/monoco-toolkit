---
id: FEAT-0111
uid: d2df83
type: feature
status: open
stage: draft
title: Add force-prune option for issue close command
created_at: '2026-01-29T18:41:05'
updated_at: '2026-01-29T18:41:05'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0111'
files: []
opened_at: '2026-01-29T18:41:05'
---

## FEAT-0111: Add force-prune option for issue close command

## Objective

When using squash merge workflow, Git cannot automatically detect that a feature branch has been merged into main. This causes `monoco issue close` to fail when trying to prune the branch, as Git's safety check prevents deletion of "unmerged" branches.

We need a `--force-prune` option that allows users to override Git's merge detection and forcefully delete the branch after confirming the issue is truly closed.

## Acceptance Criteria

- [ ] `monoco issue close <id> --force-prune` successfully deletes squash-merged branches
- [ ] Command shows clear warning before force deletion
- [ ] Without `--force-prune`, behavior remains unchanged (safe default)
- [ ] Documentation updated to explain when to use this option

## Technical Tasks

- [ ] Add `--force-prune` flag to `issue close` command
- [ ] Implement force deletion logic using `git branch -D` instead of `git branch -d`
- [ ] Add confirmation prompt warning users about force deletion
- [ ] Update command help text and documentation
- [ ] Add test cases for squash-merge scenarios

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
