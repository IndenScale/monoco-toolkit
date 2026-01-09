---
name: git-repo-spike
description: Manage external Git repositories as References in `.reference/`.
---

# Git Repo Spike (Reference Management)

This skill normalizes how we introduce external code repositories.

## Core Principles
1. **Read-Only**: Code in `.reference/` is for reference only.
2. **Isolation**: All external repos sit within `.reference/`.
3. **VCS Hygiene**: `.reference/` is gitignored. We track the intent to clone, not the files.

## Workflow
1. **Add**: `monoco spike add <url>`
2. **Sync**: `monoco spike sync` (Clones/Pulls all repos)
3. **Remove**: `monoco spike remove <name>`
