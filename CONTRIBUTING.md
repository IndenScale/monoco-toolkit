# Contributing to Monoco

Thank you for your interest in contributing to Monoco! We welcome contributions from everyone.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally.
3. **Install** dependencies: `pip install -e .`

## Development Workflow

Monoco follows an **Issue-Driven Development** process.

1.  **Find or Create an Issue**:
    - Use the CLI: `monoco issue create feature -t "My Feature"`
    - Or browse existing issues in `Issues/`.
2.  **Create a Branch**:
    - `git checkout -b feat/my-feature`
3.  **Implement**:
    - Follow the "Task as Code" philosophy.
    - Keep changes atomic.
4.  **Verify**:
    - Run tests: `pytest`
    - Lint issues: `monoco issue lint`
5.  **Submit a Pull Request**:
    - Reference the Issue ID (e.g., `Fixes FEAT-0123`) in your PR description.

## Code Style

- **Python**: Follow PEP 8. Use `ruff` or `black` if available.
- **Commit Messages**: Clear and concise. Prefer "Why" over "What".

## Community

- Join our discussions on GitHub.
- Be respectful and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Release Process

### For Maintainers

Monoco uses **automated publishing** to PyPI via GitHub Actions.

#### 1. Update Version

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Bump version
```

#### 2. Commit and Tag

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"
git push

# Create and push tag
git tag v0.2.0
git push origin v0.2.0
```

#### 3. Automated Workflow

GitHub Actions will automatically:

- ✅ Run tests (`pytest`)
- ✅ Lint issues (`monoco issue lint --recursive`)
- ✅ Build distribution (`uv build`)
- ✅ Publish to PyPI (via Trusted Publishing)

#### 4. Verify Release

```bash
pip install --upgrade monoco-toolkit
monoco --version
```

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Pre-releases

For alpha/beta releases:

```bash
# Update version to "0.2.0-alpha.1"
git tag v0.2.0-alpha.1
git push origin v0.2.0-alpha.1
```

### Troubleshooting

If the release fails, check:

1. PyPI Trusted Publisher is configured correctly (see `docs/pypi-trusted-publishing.md`)
2. All tests pass locally
3. GitHub Actions has `id-token: write` permission
