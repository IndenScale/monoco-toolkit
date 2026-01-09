---
name: i18n-scan
description: Internationalization quality control skill.
---

# i18n Maintenance Standard

i18n is a "first-class citizen" in Monoco.

## Core Standards

### 1. i18n Structure
- **Root Files**: Suffix pattern (e.g. `README_ZH.md`).
- **Docs Directories**: Subdirectory pattern (`docs/guide/zh/intro.md`).

### 2. Exclusion Rules
- `.gitignore` (respected automatically)
- `.references/`
- Build artifacts

## Automated Checklist
1. **Coverage Scan**: `monoco i18n scan` - Checks missing translations.
2. **Integrity Check**: Planned.

## Working with I18n
- Create English docs first.
- Create translations following the naming convention.
- Run `monoco i18n scan` to verify coverage.
