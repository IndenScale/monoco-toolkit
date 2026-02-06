# PyPI Trusted Publishing Configuration Guide

This document explains how to configure PyPI Trusted Publishing for Monoco to achieve secure automated publishing.

## What is Trusted Publishing?

Trusted Publishing is an authentication mechanism provided by PyPI based on OpenID Connect (OIDC), allowing GitHub Actions to publish packages directly to PyPI without manually managing API Tokens.

**Advantages**:

- ✅ **More Secure**: No need to store long-lived API Tokens in GitHub Secrets
- ✅ **Automated**: GitHub Actions automatically acquires temporary credentials
- ✅ **Traceable**: Each publish is associated with a specific Git Commit and Workflow Run

## Configuration Steps

### 1. Create Project on PyPI (First Publish)

If the project has not yet been published on PyPI, you need to manually create a placeholder version first:

```bash
# Build package
uv build

# Manual upload (requires PyPI API Token)
uv publish
```

Alternatively, you can configure a Trusted Publisher directly on PyPI, and the project will be automatically created upon the first publish.

### 2. Configure Trusted Publisher

1. Log in to [PyPI](https://pypi.org/)
2. Go to project page: `https://pypi.org/project/monoco-toolkit/`
3. Click **Manage** → **Publishing**
4. In the **Trusted Publishers** section, click **Add a new publisher**
5. Fill in the following information:

   | Field                 | Value              |
   | --------------------- | ------------------ |
   | **PyPI Project Name** | `monoco-toolkit`   |
   | **Owner**             | `IndenScale`       |
   | **Repository**        | `Monoco`           |
   | **Workflow name**     | `publish-pypi.yml` |
   | **Environment name**  | (Leave blank)      |

6. Click **Add**

### 3. Verify Configuration
