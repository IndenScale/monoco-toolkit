# Monoco i18n System User Manual

Monoco treats internationalization (i18n) as a "first-class citizen" of the project. This manual introduces the design philosophy of the Monoco i18n system, file organization conventions, and how to use the maintenance tools.

## Core Philosophy

To ensure the universality of knowledge assets, Monoco requires core documentation to have multi-language support. Our i18n system aims to help developers maintain multi-language synchronization of documentation through lightweight conventions and automation tools.

## File Organization Conventions

Monoco adopts a hybrid file organization strategy to accommodate the needs of documentation at different levels.

### 1. Suffix Pattern

Applicable to key files in the project root directory. Language versions are distinguished by filename suffixes.

- **Scope**: `Root Directory`
- **Naming Rule**: `{Filename}_{LANG}.{ext}` (where `{LANG}` must be uppercase)
- **Examples**:
  - `README.md` (source file, defaults to English)
  - `README_ZH.md` (Chinese version)

### 2. Subdirectory Pattern

Applicable to structured documentation in documentation directories. Translations are managed through language subfolders at the same level.

- **Scope**: `docs/`, `arch/`, and other documentation directories
- **Naming Rule**: `{dir}/{LANG}/{filename}` (where `{LANG}` is a lowercase directory name)
- **Examples**:
  - Source file: `docs/guide/intro.md`
  - Chinese version: `docs/guide/zh/intro.md`

## Command-Line Tools

Monoco Toolkit provides out-of-the-box i18n maintenance commands.

### Coverage Scan (`scan`)

The `scan` command is used to check the translation coverage of project documentation. It scans all source files and looks for corresponding translation files according to the above conventions.

**Basic Usage**:

```bash
monoco i18n scan
```

**Parameter Description**:

- `--root {path}`: Specifies the root directory to scan. Defaults to the project root directory.
- `--limit {number}`: Limits the number of missing files to display. Defaults to 10. Set to 0 to show all.

**Output Interpretation**:

After scanning, the console will output a detailed report:

- **Source File**: Path to source files for which no corresponding translation was found.
- **Missing Languages**: Specific language versions that are missing (e.g., `zh`).
- **Expected Paths**: According to the conventions, the paths where the system expects to find translation files.

When the number of missing files exceeds the display limit, the table title will show "Showing X / Y missing files", and a tip will be displayed after the table suggesting to use `--limit 0` to view all.

**Example Output**:

```text
Scanning i18n coverage in /path/to/project...
Target Languages: zh (Source: en)

i18n Availability Report (Showing 10 / 432 missing files)
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Source File      ┃ Missing Languages ┃ Expected Paths               ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ README.md        │ zh                │ README_ZH.md                 │
│ docs/foo.md      │ zh                │ docs/zh/foo.md               │
└──────────────────┴───────────────────┴──────────────────────────────┘

💡 Tip: Use --limit 0 to show all 432 missing files.

I18N STATUS
Total Source Files: 514
Target Languages: 1
Total Checks: 514
Found Translations: 82
Missing Files: 432
  - Partial Missing: 0
  - Complete Missing: 432
Coverage: 16.0%
```

**Usage Tips**:

```bash
# Default: show up to 10 missing records
monoco i18n scan

# Show up to 5 missing records
monoco i18n scan --limit 5

# Show all missing records
monoco i18n scan --limit 0

# Scan a specific directory
monoco i18n scan --root ./docs
```

## Configuration

The behavior of i18n can be fine-tuned through the project configuration file `monoco.yaml` (if available) or global configuration.

(Note: The system defaults to EN as the source language and includes ZH as a target language)

## FAQ

### Q: Why is my translation file not recognized?

A: Please check that the filename case strictly conforms to the conventions.

- The root directory suffix pattern requires uppercase (e.g., `_ZH`).
- The subdirectory pattern requires lowercase directory names (e.g., `/zh/`).

### Q: How do I ignore certain files that don't need translation?

A: The system automatically follows `.gitignore` rules. In addition, build artifact directories (such as `dist/`) and non-documentation directories are automatically excluded.
