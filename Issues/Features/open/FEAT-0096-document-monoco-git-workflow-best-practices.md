---
id: FEAT-0096
uid: 382b6b
type: feature
status: open
stage: doing
title: Document Monoco Git Workflow Best Practices
created_at: "2026-01-19T15:46:24"
opened_at: "2026-01-19T15:46:24"
updated_at: "2026-01-19T15:48:08"
isolation:
  type: branch
  ref: feat/feat-0096-document-monoco-git-workflow-best-practices
  created_at: "2026-01-19T15:46:28"
dependencies: []
related: []
domains: []
tags:
  - "#FEAT-0096"
files:
  - '"Issues/Epics/closed/EPIC-0002-\346\231\272\350\203\275\344\273\273\345\212\241\345\206\205\346\240\270\344\270\216\347\212\266\346\200\201\346\234\272.md"'
  - '"Issues/Epics/closed/EPIC-0006-Monoco\347\234\213\346\235\277Web\345\272\224\347\224\250.md"'
  - '"Issues/Epics/closed/EPIC-0017-\345\216\237\347\224\237-Git-Hooks-\351\233\206\346\210\220.md"'
  - '"Issues/Features/closed/FEAT-0043-toolkit-\345\210\206\345\217\221\346\270\240\351\201\223\345\273\272\350\256\276.md"'
  - '"Issues/Fixes/open/FIX-0011-\344\277\256\345\244\215-documentation-i18n-\347\273\223\346\236\204\344\270\215\344\270\200\350\207\264\344\270\216\346\200\247\350\203\275\351\227\256\351\242\230.md"'
  - .github/workflows/deploy-docs.yml
  - .gitignore
  - CHANGELOG.md
  - Issues/Chores/closed/CHORE-0010-document-governance-maturity-and-changelog.md
  - Issues/Chores/closed/CHORE-0011-site-deployment-configuration.md
  - Issues/Chores/open/CHORE-0012-refactor-documentation-structure-and-unify-source.md
  - Issues/Epics/closed/EPIC-0011-vscode-extension-integration.md
  - Issues/Epics/closed/EPIC-0012-enable-agent-execution-in-vs-code-extension.md
  - Issues/Epics/closed/EPIC-0016-lsp-cross-project-navigation-architecture.md
  - Issues/Epics/closed/EPIC-0018-monoco-toolkit-documentation-site.md
  - Issues/Epics/open/EPIC-0012-enable-agent-execution-in-vs-code-extension.md
  - Issues/Features/closed/FEAT-0061-interactive-goto-definition.md
  - Issues/Features/closed/FEAT-0062-drag-and-drop-text.md
  - Issues/Features/closed/FEAT-0084-refine-issue-lifecycle-actions-and-agent-integrati.md
  - Issues/Features/closed/FEAT-0085-update-vs-code-extension-for-refined-action-system.md
  - Issues/Features/closed/FEAT-0092-governance-maturity-checks.md
  - Issues/Features/closed/FEAT-0093-initialize-vitepress-site-infrastructure.md
  - Issues/Features/closed/FEAT-0094-configure-documentation-content-pipeline.md
  - Issues/Features/closed/FEAT-0095-populate-core-documentation-manifesto.md
  - Issues/Features/open/FEAT-0061-interactive-goto-definition.md
  - Issues/Features/open/FEAT-0062-drag-and-drop-text.md
  - Issues/Features/open/FEAT-0092-governance-maturity-checks.md
  - Issues/Features/open/FEAT-0096-document-monoco-git-workflow-best-practices.md
  - Issues/Fixes/closed/FIX-0012-fix-site-light-mode-color-scheme.md
  - Kanban/apps/webui/package.json
  - Kanban/apps/webui/src/app/components/KanbanCard.tsx
  - Kanban/apps/webui/src/app/types.ts
  - Kanban/packages/core/package.json
  - Kanban/packages/core/src/types.ts
  - Kanban/packages/monoco-kanban/package.json
  - docs/en/index.md
  - docs/en/issue/concepts.md
  - docs/en/issue/configuration.md
  - docs/en/issue/manual.md
  - docs/en/issue/query_syntax.md
  - extensions/vscode/client/src/webview/KanbanProvider.ts
  - extensions/vscode/en/NATIVE_TREEVIEW_IMPLEMENTATION.md
  - extensions/vscode/package.json
  - extensions/vscode/shared/constants/MessageTypes.ts
  - extensions/vscode/shared/types/Message.ts
  - extensions/vscode/zh/NATIVE_TREEVIEW_IMPLEMENTATION.md
  - monoco/features/i18n/core.py
  - pyproject.toml
  - scripts/generate_changelog.py
  - scripts/sync-site-content.js
  - site/.vitepress/config.mts
  - site/.vitepress/theme/index.ts
  - site/.vitepress/theme/style.css
  - site/package-lock.json
  - site/package.json
  - site/postcss.config.js
  - site/src/en/guide/index.md
  - site/src/en/guide/setup/index.md
  - site/src/en/index.md
  - site/src/en/meta/Manifesto.md
  - site/src/en/meta/design/agent-native-design-pattern.md
  - site/src/en/meta/process/pypi-implementation-summary.md
  - site/src/en/meta/process/pypi-trusted-publishing.md
  - site/src/en/meta/process/release_audit.md
  - site/src/en/reference/architecture.md
  - site/src/en/reference/core-integration-registry.md
  - site/src/en/reference/extensions/features/architecture.md
  - site/src/en/reference/extensions/features/commands.md
  - site/src/en/reference/extensions/features/configuration.md
  - site/src/en/reference/extensions/features/index.md
  - site/src/en/reference/extensions/features/issue_management.md
  - site/src/en/reference/extensions/index.md
  - site/src/en/reference/i18n/index.md
  - site/src/en/reference/i18n/manual.md
  - site/src/en/reference/issue/00_overview.md
  - site/src/en/reference/issue/01_structure.md
  - site/src/en/reference/issue/02_lifecycle.md
  - site/src/en/reference/issue/03_workflow.md
  - site/src/en/reference/issue/04_agent_protocol.md
  - site/src/en/reference/issue/05_configuration.md
  - site/src/en/reference/issue/06_query_syntax.md
  - site/src/en/reference/issue/07_governance.md
  - site/src/en/reference/issue/index.md
  - site/src/en/reference/spike/index.md
  - site/src/en/reference/spike/manual.md
  - site/src/en/reference/tools/cli.md
  - site/src/en/reference/tools/vscode.md
  - site/src/zh/guide/index.md
  - site/src/zh/guide/setup/index.md
  - site/src/zh/index.md
  - site/src/zh/meta/Manifesto.md
  - site/src/zh/meta/design/agent-native-design-pattern.md
  - site/src/zh/meta/process/pypi-implementation-summary.md
  - site/src/zh/meta/process/pypi-trusted-publishing.md
  - site/src/zh/meta/process/release_audit.md
  - site/src/zh/reference/architecture.md
  - site/src/zh/reference/core-integration-registry.md
  - site/src/zh/reference/extensions/features/architecture.md
  - site/src/zh/reference/extensions/features/commands.md
  - site/src/zh/reference/extensions/features/configuration.md
  - site/src/zh/reference/extensions/features/index.md
  - site/src/zh/reference/extensions/features/issue_management.md
  - site/src/zh/reference/extensions/index.md
  - site/src/zh/reference/i18n/index.md
  - site/src/zh/reference/i18n/manual.md
  - site/src/zh/reference/issue/00_overview.md
  - site/src/zh/reference/issue/01_structure.md
  - site/src/zh/reference/issue/02_lifecycle.md
  - site/src/zh/reference/issue/03_workflow.md
  - site/src/zh/reference/issue/04_agent_protocol.md
  - site/src/zh/reference/issue/05_configuration.md
  - site/src/zh/reference/issue/06_query_syntax.md
  - site/src/zh/reference/issue/07_governance.md
  - site/src/zh/reference/issue/index.md
  - site/src/zh/reference/spike/index.md
  - site/src/zh/reference/spike/manual.md
  - site/src/zh/reference/tools/cli.md
  - site/src/zh/reference/tools/vscode.md
  - site/tailwind.config.js
  - site/vercel.json
  - uv.lock
---

## FEAT-0096: Document Monoco Git Workflow Best Practices

## Objective

Establish a standard operating procedure (SOP) for integrating Monoco Issue Tracking with Git Workflows. This guide will define the canonical lifecycle: Creation -> Branching -> Implementation -> Validation -> Merging -> Release.

## Acceptance Criteria

- [x] A new guide `site/src/zh/guide/workflow.md` (and en) is created.
- [x] The guide covers:
  - Branching strategy (Feature Branch Workflow).
  - Lifecycle mapping (Open -> Doing -> Review -> Closed).
  - Quality Gates (Linting, Tests before commit/push).
- [x] `site/src/zh/guide/index.md` links to this new workflow guide.

## Technical Tasks

- [x] Draft `site/src/zh/guide/workflow.md` with "Best Practices" content.
- [x] Translate to `site/src/en/guide/workflow.md`.
- [x] Update `site/.vitepress/config.mts` sidebar to include the new page.
- [x] Add navigation links in `guide/index.md`.

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
