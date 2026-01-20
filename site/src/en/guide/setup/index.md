# Monoco Initialization

`monoco init` is the bootstrap command for Monoco Toolkit, used to initialize the Monoco runtime environment. It is responsible for establishing global configuration, project-level configuration, and generating necessary directory structures and agent memory injection.

## Core Functions

1. **Bootstrap**: Check and create necessary configuration files.
2. **Context Injection**: Inject Toolkit capability descriptions (Skills & Prompts) into the project's `GEMINI.md` or `CLAUDE.md`, activating AI agent capabilities.
3. **Scaffolding**: Initialize standard directory structures such as `Issues/`, `.references/`, etc.

## Usage

```bash
monoco init [OPTIONS]
```

### Options

- `--global`: Configure only user global settings (such as author name).
- `--project`: Configure only current project settings (such as project name, Key).
- `--help`: Display help information.

Typically, when cloning a new repository or creating a new project, simply run `monoco init`.

## Initialization Process Details

### 1. Global Configuration

- **Location**: `~/.monoco/config.yaml`
- **Content**: Stores the user's global identity information.
- **Interaction**:
  - On first run, it will ask for "Your Name". This name will be used as the default Author for the Issue system.
  - Supports automatic reading from git config as the default value.

```yaml
core:
  author: 'Alice'
```

### 2. Project Configuration

- **Location**: `./.monoco/config.yaml`
- **Content**: Defines project metadata and path mappings.
- **Interaction**:
  - **Project Name**: Project name.
  - **Project Key**: 3-4 uppercase letters, used as the prefix for Issue IDs (e.g., `MON-123`). Monoco will automatically recommend a Key based on the project name.

Example generated configuration file:

```yaml
project:
  name: 'Monoco Main'
  key: 'MON'
paths:
  issues: 'Issues' # Issue storage path
  spikes: '.references' # Spike reference material storage path
  specs: 'SPECS' # Specification document path
```

### 3. Scaffolding & Injection

`monoco init` will call the `init` method of each feature module to perform the following operations:

- **Issues**: Ensure the storage directory exists (default `Issues/`).
- **Spikes**: Ensure the storage directory exists (default `.references/`).
- **I18n**: Initialize internationalization-related settings.
- **Skills**:
  - Generate `SKILL.md` for each module under `Toolkit/skills/` (such as `issues-management/SKILL.md`).
  - **Key Step**: Modify `GEMINI.md`, `CLAUDE.md`, `AGENTS.md` in the project root directory.
  - **Injected Content**: Insert or update the `## Monoco Toolkit` section in these files, containing prompts for all available commands.

## FAQ

### Q: If I modify the Prompt in `GEMINI.md`, will it be overwritten?

A: `monoco init` uses regex matching for the `## Monoco Toolkit` section.

- If the section exists, it will be **fully replaced**. Do not manually modify content within this section; instead, modify the corresponding Feature code (Generated Source).
- Content outside this section will not be affected.

### Q: How do I update the Toolkit's Prompt?

A: After Monoco Toolkit is upgraded, simply run `monoco init` again in the project root directory to inject the latest Prompt into `GEMINI.md`.
