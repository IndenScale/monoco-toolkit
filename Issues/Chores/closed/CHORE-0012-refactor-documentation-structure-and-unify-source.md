---
id: CHORE-0012
uid: 6ab718
type: chore
status: closed
stage: done
title: 重构文档结构并统一源文件
created_at: '2026-01-19T15:35:15'
opened_at: '2026-01-19T15:35:15'
updated_at: '2026-01-19T15:51:11'
closed_at: '2026-01-19T15:51:11'
solution: implemented
isolation:
  type: branch
  ref: feat/chore-0012-refactor-documentation-structure-and-unify-source
  created_at: '2026-01-19T15:35:22'
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0012'
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

## CHORE-0012: 重构文档结构并统一源文件

## Objective

解决 `docs/` 和 `site/` 目录之间的“分裂问题”，通过将内容重新组织为指南（Guide）、参考（Reference）和元数据（Meta）三个部分，使信息架构更加专业。

## Acceptance Criteria

- [x] 删除 `docs/` 目录并将所有独特内容合并到 `site/`。
- [x] `site/src` 布局重组为 `guide/`、`reference/` 和 `meta/`。
- [x] 更新 VitePress 配置 `config.mts` 以反映新的路径。

## Technical Tasks

- [x] 删除 `docs/` 文件夹
- [x] 在 `site/src/`（中英文）中创建新的目录结构
- [x] 将文件移动到 `guide/`、`reference/` 和 `meta/`
- [x] 更新 `site/.vitepress/config.mts` 的侧边栏和常规导航

## Review Comments

任务已顺利完成并经过全面验证。通过本次重构，我们成功消除了 `docs/` 和 `site/` 目录并存导致的“双头”问题。所有的文档源文件现在都统一存放于 `site/src/` 下，并按照“指南”、“参考”和“元数据”三个维度进行了科学分类。此外，VitePress 的配置文件也同步进行了更新，确保所有导航和侧边栏链接在重组后依然准确无误。中英文版本的内容已经完全对称，为后续的多语言维护打下了坚实基础。

## Delivery
<!-- Monoco Auto Generated -->
**Commits (2)**:
- `934bd7f` docs: update CHORE-0012 definition
- `c664b3e` chore: refactor documentation structure and unify source

**Touched Files (118)**:
- `Issues/Chores/open/CHORE-0012-refactor-documentation-structure-and-unify-source.md`
- `docs/en/i18n/README.md`
- `docs/en/index.md`
- `docs/en/issue/README.md`
- `docs/en/spike/README.md`
- `docs/zh/i18n/README.md`
- `docs/zh/index.md`
- `docs/zh/issue/README.md`
- `docs/zh/spike/README.md`
- `site/.vitepress/config.mts`
- `site/src/en/Manifesto.md`
- `site/src/en/agent-native-design-pattern.md`
- `site/src/en/architecture.md`
- `site/src/en/core-integration-registry.md`
- `site/src/en/extensions/features/architecture.md`
- `site/src/en/extensions/features/commands.md`
- `site/src/en/extensions/features/configuration.md`
- `site/src/en/extensions/features/index.md`
- `site/src/en/extensions/features/issue_management.md`
- `site/src/en/guide.md`
- `site/src/en/guide/index.md`
- `site/src/en/guide/setup/manual.md`
- `site/src/en/i18n/manual.md`
- `site/src/en/issue/00_overview.md`
- `site/src/en/issue/01_structure.md`
- `site/src/en/issue/02_lifecycle.md`
- `site/src/en/issue/03_workflow.md`
- `site/src/en/issue/04_agent_protocol.md`
- `site/src/en/issue/05_configuration.md`
- `site/src/en/issue/06_query_syntax.md`
- `site/src/en/issue/07_governance.md`
- `site/src/en/meta/Manifesto.md`
- `site/src/en/meta/design/agent-native-design-pattern.md`
- `site/src/en/meta/process/pypi-implementation-summary.md`
- `site/src/en/meta/process/pypi-trusted-publishing.md`
- `site/src/en/meta/process/release_audit.md`
- `site/src/en/pypi-implementation-summary.md`
- `site/src/en/pypi-trusted-publishing.md`
- `site/src/en/reference/architecture.md`
- `site/src/en/reference/core-integration-registry.md`
- `site/src/en/reference/extensions/features/architecture.md`
- `site/src/en/reference/extensions/features/commands.md`
- `site/src/en/reference/extensions/features/configuration.md`
- `site/src/en/reference/extensions/features/index.md`
- `site/src/en/reference/extensions/features/issue_management.md`
- `site/src/en/reference/i18n/index.md`
- `site/src/en/reference/i18n/manual.md`
- `site/src/en/reference/issue/00_overview.md`
- `site/src/en/reference/issue/01_structure.md`
- `site/src/en/reference/issue/02_lifecycle.md`
- `site/src/en/reference/issue/03_workflow.md`
- `site/src/en/reference/issue/04_agent_protocol.md`
- `site/src/en/reference/issue/05_configuration.md`
- `site/src/en/reference/issue/06_query_syntax.md`
- `site/src/en/reference/issue/07_governance.md`
- `site/src/en/reference/issue/index.md`
- `site/src/en/reference/spike/index.md`
- `site/src/en/reference/spike/manual.md`
- `site/src/en/reference/tools/cli.md`
- `site/src/en/reference/tools/vscode.md`
- `site/src/en/release_audit.md`
- `site/src/en/setup/manual.md`
- `site/src/en/spike/manual.md`
- `site/src/en/tools/cli.md`
- `site/src/en/tools/vscode.md`
- `site/src/zh/Manifesto.md`
- `site/src/zh/agent-native-design-pattern.md`
- `site/src/zh/architecture.md`
- `site/src/zh/core-integration-registry.md`
- `site/src/zh/extensions/features/architecture.md`
- `site/src/zh/extensions/features/commands.md`
- `site/src/zh/extensions/features/configuration.md`
- `site/src/zh/extensions/features/index.md`
- `site/src/zh/extensions/features/issue_management.md`
- `site/src/zh/guide/index.md`
- `site/src/zh/guide/setup/manual.md`
- `site/src/zh/i18n/manual.md`
- `site/src/zh/issue/00_overview.md`
- `site/src/zh/issue/01_structure.md`
- `site/src/zh/issue/02_lifecycle.md`
- `site/src/zh/issue/03_workflow.md`
- `site/src/zh/issue/04_agent_protocol.md`
- `site/src/zh/issue/05_configuration.md`
- `site/src/zh/issue/06_query_syntax.md`
- `site/src/zh/issue/07_governance.md`
- `site/src/zh/meta/Manifesto.md`
- `site/src/zh/meta/design/agent-native-design-pattern.md`
- `site/src/zh/meta/process/pypi-implementation-summary.md`
- `site/src/zh/meta/process/pypi-trusted-publishing.md`
- `site/src/zh/meta/process/release_audit.md`
- `site/src/zh/pypi-implementation-summary.md`
- `site/src/zh/pypi-trusted-publishing.md`
- `site/src/zh/reference/architecture.md`
- `site/src/zh/reference/core-integration-registry.md`
- `site/src/zh/reference/extensions/features/architecture.md`
- `site/src/zh/reference/extensions/features/commands.md`
- `site/src/zh/reference/extensions/features/configuration.md`
- `site/src/zh/reference/extensions/features/index.md`
- `site/src/zh/reference/extensions/features/issue_management.md`
- `site/src/zh/reference/i18n/index.md`
- `site/src/zh/reference/i18n/manual.md`
- `site/src/zh/reference/issue/00_overview.md`
- `site/src/zh/reference/issue/01_structure.md`
- `site/src/zh/reference/issue/02_lifecycle.md`
- `site/src/zh/reference/issue/03_workflow.md`
- `site/src/zh/reference/issue/04_agent_protocol.md`
- `site/src/zh/reference/issue/05_configuration.md`
- `site/src/zh/reference/issue/06_query_syntax.md`
- `site/src/zh/reference/issue/07_governance.md`
- `site/src/zh/reference/issue/index.md`
- `site/src/zh/reference/spike/index.md`
- `site/src/zh/reference/spike/manual.md`
- `site/src/zh/reference/tools/cli.md`
- `site/src/zh/reference/tools/vscode.md`
- `site/src/zh/setup/manual.md`
- `site/src/zh/spike/manual.md`
- `site/src/zh/tools/cli.md`
- `site/src/zh/tools/vscode.md`
