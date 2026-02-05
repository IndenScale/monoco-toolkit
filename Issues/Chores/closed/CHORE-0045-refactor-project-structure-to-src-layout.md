---
id: CHORE-0045
uid: 1c6018
type: chore
status: closed
stage: done
title: Refactor project structure to src layout
created_at: '2026-02-06T05:40:25'
updated_at: '2026-02-06T05:50:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0045'
- '#EPIC-0000'
files:
- pyproject.toml
- monoco.spec
- scripts/build_cli.sh
- src/monoco/main.py
- Issues/Chores/open/CHORE-0045-refactor-project-structure-to-src-layout.md
criticality: low
solution: implemented
opened_at: '2026-02-06T05:40:25'
---

## CHORE-0045: Refactor project structure to src layout

## Objective
Refactor project structure from flat layout to src layout (src/monoco/) for better Python packaging practices.

## Acceptance Criteria
- [x] Code directory moved to src/monoco/
- [x] pyproject.toml updated with packages = ["src/monoco"]
- [x] monoco.spec updated with src/monoco/main.py
- [x] build_cli.sh updated with correct paths
- [x] main.py updated to find pyproject.toml at correct relative path
- [x] Build passes successfully

## Technical Tasks
- [x] Create src/ directory and move monoco/ into it
- [x] Update pyproject.toml packages path
- [x] Update monoco.spec Analysis entry point
- [x] Update scripts/build_cli.sh SRC_DIR and pyinstaller path
- [x] Update src/monoco/main.py pyproject.toml lookup (add one more parent level)
- [x] Run build verification
- [x] Update issue status to closed

## Review Comments
Completed successfully. Build verified and all core tests pass.
