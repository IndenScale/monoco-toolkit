---
name: monoco-spike
description: Manage external reference repositories for research and learning. Provides read-only access to curated codebases.
---

# Spike (Research)

Manage external reference repositories in Monoco projects.

## Overview

The Spike feature allows you to:

- **Add external repositories** as read-only references
- **Sync repository content** to local `.references/` directory
- **Access curated knowledge** without modifying source code

## Key Commands

### Add Repository

```bash
monoco spike add <url>
```

Adds an external repository as a reference. The repository will be cloned to `.references/<name>/` where `<name>` is derived from the repository URL.

**Example**:

```bash
monoco spike add https://github.com/example/awesome-project
# Available at: .references/awesome-project/
```

### Sync Repositories

```bash
monoco spike sync
```

Downloads or updates all configured spike repositories from `.monoco/config.yaml`.

### List Spikes

```bash
monoco spike list
```

Shows all configured spike repositories and their sync status.

## Configuration

Spike repositories are configured in `.monoco/config.yaml`:

```yaml
project:
  spike_repos:
    awesome-project: https://github.com/example/awesome-project
    another-ref: https://github.com/example/another-ref
```

## Best Practices

1. **Read-Only Access**: Never edit files in `.references/`. Treat them as external knowledge.
2. **Curated Selection**: Only add high-quality, relevant repositories.
3. **Regular Sync**: Run `monoco spike sync` periodically to get updates.
4. **Commit Configuration**: Add spike repo URLs to version control for team consistency.

## Use Cases

- **Learning from Examples**: Study well-architected codebases
- **API Reference**: Keep framework documentation locally
- **Pattern Library**: Maintain a collection of design patterns
- **Competitive Analysis**: Reference similar projects
