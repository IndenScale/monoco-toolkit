# Monoco Toolkit PyPI 分发渠道实施总结

## 实施概览

已成功为 Monoco Toolkit 建立 PyPI 自动发布流水线，复用 Typedown 的 Trusted Publishing 机制。

## 已完成的工作

### 1. GitHub Actions 工作流 ✅

**文件**: `.github/workflows/publish-pypi.yml`

**特性**:

- ✅ Git Tag (`v*`) 触发自动发布
- ✅ 使用 `uv` 进行依赖管理和构建
- ✅ 发布前自动运行测试套件
- ✅ 发布前自动运行 Issue Lint 校验
- ✅ 使用 Trusted Publishing (OIDC) 进行身份验证
- ✅ 跳过已存在的版本 (`skip-existing: true`)

**关键步骤**:

```yaml
- Install uv
- Set up Python
- Install Dependencies
- Run Tests
- Lint Issues
- Build distribution
- Publish to PyPI (Trusted Publishing)
```

### 2. PyPI 元数据完善 ✅

**文件**: `pyproject.toml`

**新增内容**:

- ✅ MIT 许可证声明
- ✅ 关键词 (keywords) 用于 PyPI 搜索优化
- ✅ 分类器 (classifiers) 标注项目属性
- ✅ 项目链接 (Homepage, Repository, Documentation, Issues)
- ✅ 完整的项目描述

**PyPI 页面效果**:

- 用户可以通过搜索 "monoco", "agent-native", "kanban" 等关键词找到项目
- 清晰的许可证和 Python 版本兼容性信息
- 直达项目主页、文档和 Issue 追踪的链接

### 3. 配置文档 ✅

**文件**: `docs/pypi-trusted-publishing.md`

**内容**:

- ✅ Trusted Publishing 原理说明
- ✅ PyPI 配置步骤（图文并茂）
- ✅ 验证流程
- ✅ 正式发布流程
- ✅ 故障排查指南
- ✅ 与 Typedown 凭证复用说明

### 4. Issue 追踪 ✅

**创建**: `FEAT-0051: CLI 工具分发 - PyPI`

**状态**:

- ✅ 已关联到 `EPIC-0009: CICD 基建`
- ✅ 包含完整的 Objective、Acceptance Criteria 和 Technical Tasks
- ✅ 已标记部分任务为完成

## 待完成的工作

### 1. PyPI 配置 (需要项目管理员权限)

**操作人**: 拥有 PyPI `monoco-toolkit` 项目管理权限的用户

**步骤**:

1. 登录 [PyPI](https://pypi.org/)
2. 访问项目管理页面
3. 配置 Trusted Publisher:
   - Owner: `IndenScale`
   - Repository: `Monoco`
   - Workflow name: `publish-pypi.yml`
   - Environment name: (留空)

**参考**: `docs/pypi-trusted-publishing.md`

### 2. 首次发布验证

**建议流程**:

1. 创建测试 Tag: `v0.1.0-alpha.1`
2. 观察 GitHub Actions 执行
3. 检查 PyPI 是否成功发布
4. 验证 `pip install monoco-toolkit` 可用性

### 3. 文档更新

**待更新文件**:

- `README.md`: 添加 PyPI 安装说明
- `CONTRIBUTING.md`: 添加发布流程说明

**建议内容**:

````markdown
## Installation

```bash
pip install monoco-toolkit
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for release workflow.
````

## 与 Typedown 的对比

| 项目               | PyPI 包名        | Workflow 文件      | Trusted Publisher |
| ------------------ | ---------------- | ------------------ | ----------------- |
| **Typedown**       | `typedown`       | `publish-pypi.yml` | ✅ 已配置         |
| **Monoco Toolkit** | `monoco-toolkit` | `publish-pypi.yml` | ⏳ 待配置         |

**复用的凭证**:

- ✅ 使用相同的 PyPI 账号（IndenScale 团队账号）
- ✅ 使用相同的 Trusted Publishing 机制
- ✅ 使用相同的 GitHub Actions 权限配置

**差异**:

- Typedown 额外运行 `td test --path tests/integration_showcase`
- Toolkit 额外运行 `monoco issue lint --recursive`

## 发布流程示例

```bash
# 1. 更新版本号
# 编辑 pyproject.toml，修改 version = "0.1.0"

# 2. 提交变更
git add pyproject.toml
git commit -m "chore: bump version to 0.1.0"
git push

# 3. 创建并推送 Tag
git tag v0.1.0
git push origin v0.1.0

# 4. GitHub Actions 自动执行:
#    - 运行测试
#    - Lint Issues
#    - 构建包
#    - 发布到 PyPI

# 5. 验证发布
pip install monoco-toolkit==0.1.0
monoco --version
```

## 安全性说明

### Trusted Publishing 的优势

1. **无需长期 Token**: 不在 GitHub Secrets 中存储 PyPI API Token
2. **临时凭证**: 每次发布使用一次性 OIDC Token
3. **可追溯性**: 每次发布都与 Git Commit 和 Workflow Run 关联
4. **权限最小化**: 只有特定的 Workflow 可以发布

### 权限配置

```yaml
permissions:
  id-token: write # 必需: 用于 OIDC 认证
  contents: read # 必需: 读取仓库代码
```

## 后续优化建议

1. **版本自动化**: 考虑使用 `bump2version` 或 `semantic-release` 自动管理版本号
2. **Changelog 生成**: 集成 `git-cliff` 或 `conventional-changelog` 自动生成变更日志
3. **Pre-release 支持**: 支持 `v0.1.0-alpha.1` 等预发布版本
4. **多 Python 版本测试**: 在 CI 中测试 Python 3.10, 3.11, 3.12

## 参考资料

- [PyPI Trusted Publishers 官方文档](https://docs.pypi.org/trusted-publishers/)
- [Typedown 的 publish-pypi.yml](../../../Typedown/.github/workflows/publish-pypi.yml)
- [Hatchling 构建系统文档](https://hatch.pypa.io/latest/config/build/)
