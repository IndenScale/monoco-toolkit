# Monoco Spike System User Manual

The Monoco Spike System is a tool for managing temporary, research-oriented code (Git Repo Spikes). It allows developers to easily import external open-source projects as references while keeping the main codebase clean.

## 1. Core Concepts

### 1.1 What is a Spike?

In agile development, a "Spike" refers to a quick, temporary experiment or investigation conducted to reduce technical risk or uncertainty.

### 1.2 Why is the Spike System Needed?

Monoco encourages "standing on the shoulders of giants" (referencing excellent open-source implementations), but directly mixing external codebases into the project can lead to:

- **Bloated Repository**: Committing irrelevant history.
- **Licensing Risks**: Accidental confusion of licenses.
- **Search Noise**: Global searches returning a large amount of irrelevant results.

The Spike System addresses these issues through **Physical Isolation** and **Automated Management**:

- **Store in `.reference/`**: Defaults to downloading all reference repositories to a directory excluded by `.gitignore`.
- **Configuration Management**: Records the list of repositories in `monoco.yaml` (or configuration system) instead of committing code directly.
- **On-Demand Sync**: New members only need to run `sync` to pull all reference materials.

---

## 2. Command Reference

### 2.1 Init

Initialize the Spike environment, primarily ensuring that the reference code directory is added to `.gitignore` in the project root.

```bash
monoco spike init
```

### 2.2 Add

Add a new external repository to the reference list and record it in the configuration.

```bash
monoco spike add <url>
```

- `<url>`: Git repository address (supports HTTPS or SSH).
- The system automatically infers the repository name (e.g., `https://github.com/foo/bar.git` -> `bar`).
- **Note**: After adding, you must run `monoco spike sync` to actually download the code.

### 2.3 Sync

Download or update all configured reference repositories.

```bash
monoco spike sync
```

- If the repository does not exist, it executes `git clone`.
- If the repository already exists, it executes `git pull` (auto-pull not yet implemented; currently ensures existence).
- This command is idempotent.

### 2.4 List

List all configured reference repositories.

```bash
monoco spike list
```

### 2.5 Remove

Remove a repository from the configuration, with an option to delete the physical files.

```bash
monoco spike remove <name> [--force]
```

- `<name>`: Repository name (e.g., `bar`).
- `--force, -f`: Force delete the physical directory without asking.

---

## 3. Best Practices

1. **Read-Only**: Code under `.reference/` is for reading only. **Strictly prohibited** to modify directly, and **strictly prohibited** to import these paths directly in production code.
2. **Clean Up**: When the investigation is over, if it is no longer needed, use the `remove` command to remove it to reduce disk usage.
3. **Licensing Awareness**: When implementing new features by referencing external code, be sure to comply with the open-source license of the original project.
