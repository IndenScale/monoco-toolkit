---
name: monoco-i18n
description: Internationalization quality control for documentation. Ensures multi-language documentation stays synchronized.
type: standard
version: 1.0.0
---

# Documentation I18n

Manage internationalization for Monoco project documentation.

## Overview

The I18n feature provides:

- **Automatic scanning** for missing translations
- **Standardized structure** for multi-language documentation
- **Quality control** to maintain documentation parity

## Key Commands

### Scan for Missing Translations

```bash
monoco i18n scan
```

Scans the project for markdown files and reports missing translations.

**Output**:

- Lists source files without corresponding translations
- Shows which target languages are missing
- Respects `.gitignore` and default exclusions

## Configuration

I18n settings are configured in `.monoco/config.yaml`:

```yaml
i18n:
  source_lang: en # Source language code
  target_langs: # Target language codes
    - zh
    - ja
```

## Documentation Structure

### Root Files (Suffix Pattern)

For files in the project root:

- Source: `README.md`
- Chinese: `README_ZH.md`
- Japanese: `README_JA.md`

### Subdirectory Files (Directory Pattern)

For files in `docs/` or other directories:

```
docs/
├── en/
│   ├── guide.md
│   └── api.md
├── zh/
│   ├── guide.md
│   └── api.md
└── ja/
    ├── guide.md
    └── api.md
```

## Exclusion Rules

The following are automatically excluded from i18n scanning:

- `.gitignore` patterns (respected automatically)
- `.references/` directory
- Build artifacts (`dist/`, `build/`, `node_modules/`)
- `Issues/` directory

## Best Practices

1. **Create English First**: Write documentation in the source language first
2. **Follow Naming Convention**: Use the appropriate pattern (suffix or directory)
3. **Run Scan Regularly**: Use `monoco i18n scan` to verify coverage
4. **Commit All Languages**: Keep translations in version control

## Workflow

1. Write documentation in source language (e.g., English)
2. Create translation files following the naming convention
3. Run `monoco i18n scan` to verify all translations exist
4. Fix any missing translations reported by the scan
