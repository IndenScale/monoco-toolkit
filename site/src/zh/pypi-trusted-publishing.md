# PyPI Trusted Publishing 配置指南

本文档说明如何为 Monoco Toolkit 配置 PyPI Trusted Publishing，以实现安全的自动化发布。

## 什么是 Trusted Publishing？

Trusted Publishing 是 PyPI 提供的一种基于 OpenID Connect (OIDC) 的身份验证机制，允许 GitHub Actions 直接发布包到 PyPI，无需手动管理 API Token。

**优势**:

- ✅ **更安全**: 无需在 GitHub Secrets 中存储长期有效的 API Token
- ✅ **自动化**: GitHub Actions 自动获取临时凭证
- ✅ **可追溯**: 每次发布都与特定的 Git Commit 和 Workflow Run 关联

## 配置步骤

### 1. 在 PyPI 创建项目（首次发布）

如果项目尚未在 PyPI 上发布，需要先手动创建一个占位版本:

```bash
# 构建包
uv build

# 手动上传（需要 PyPI API Token）
uv publish
```

或者，可以直接在 PyPI 上配置 Trusted Publisher，然后首次发布会自动创建项目。

### 2. 配置 Trusted Publisher

1. 登录 [PyPI](https://pypi.org/)
2. 进入项目页面: `https://pypi.org/project/monoco-toolkit/`
3. 点击 **Manage** → **Publishing**
4. 在 **Trusted Publishers** 部分，点击 **Add a new publisher**
5. 填写以下信息:

   | 字段                  | 值                 |
   | --------------------- | ------------------ |
   | **PyPI Project Name** | `monoco-toolkit`   |
   | **Owner**             | `IndenScale`       |
   | **Repository**        | `Monoco`           |
   | **Workflow name**     | `publish-pypi.yml` |
   | **Environment name**  | (留空)             |

6. 点击 **Add**

### 3. 验证配置

配置完成后，可以通过以下方式验证:

1. 创建一个测试 Tag:

   ```bash
   git tag v0.1.0-test
   git push origin v0.1.0-test
   ```

2. 观察 GitHub Actions 的执行情况:
   - 访问 `https://github.com/IndenScale/Monoco/actions`
   - 查看 "Publish to PyPI" 工作流的运行日志

3. 检查 PyPI 项目页面是否有新版本发布

### 4. 正式发布流程

一旦配置完成，后续发布只需:

```bash
# 1. 更新 pyproject.toml 中的版本号
# 2. 创建并推送 Tag
git tag v0.1.0
git push origin v0.1.0

# GitHub Actions 会自动:
# - 运行测试
# - 构建包
# - 发布到 PyPI
```

## 复用 Typedown 的凭证

由于 Monoco Toolkit 和 Typedown 都属于 IndenScale 组织，可以复用相同的 PyPI 账号:

- **PyPI 账号**: 使用 IndenScale 团队账号
- **Trusted Publishing**: 每个项目单独配置（不同的 `workflow name`）

## 故障排查

### 问题: 发布失败，提示 "Trusted publishing exchange failure"

**原因**: PyPI 上的 Trusted Publisher 配置与 GitHub Actions 工作流不匹配。

**解决方案**:

1. 检查 PyPI 配置中的 `Workflow name` 是否为 `publish-pypi.yml`
2. 确认 GitHub Actions 的 `permissions` 包含 `id-token: write`

### 问题: 首次发布失败，提示 "Project does not exist"

**原因**: 项目尚未在 PyPI 上创建。

**解决方案**:

1. 先在 PyPI 上配置 Trusted Publisher（即使项目不存在）
2. 或者手动上传首个版本后再配置 Trusted Publisher

## 参考资料

- [PyPI Trusted Publishers 官方文档](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OIDC 文档](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Typedown 的 publish-pypi.yml](../../../Typedown/.github/workflows/publish-pypi.yml)
