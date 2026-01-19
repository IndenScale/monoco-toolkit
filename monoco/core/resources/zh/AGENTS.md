### Monoco 核心

项目管理的核心工具包命令。

- **初始化**: `monoco init` (初始化新的 Monoco 项目)
- **配置**: `monoco config get|set <key> [value]` (管理配置)
- **同步**: `monoco sync` (与 agent 环境同步)
- **卸载**: `monoco uninstall` (清理 agent 集成)

---

## ⚠️ Agent 必读: Git 工作流

在修改任何代码前,**必须**遵循以下步骤:

### 标准流程

1. **创建 Issue**: `monoco issue create feature -t "功能标题"`
2. **🔒 启动隔离环境**: `monoco issue start FEAT-XXX --branch`
   - ⚠️ **强制要求** `--branch` 参数
   - ❌ 禁止在 `main`/`master` 分支直接修改代码
3. **实现功能**: 正常编码和测试
4. **同步文件**: `monoco issue sync-files` (提交前必须运行)
5. **提交审查**: `monoco issue submit FEAT-XXX`
6. **关闭 Issue**: `monoco issue close FEAT-XXX --solution implemented`

### 质量门禁

- Git Hooks 会自动运行 `monoco issue lint` 和测试
- 不要使用 `git commit --no-verify` 绕过检查
- Linter 会阻止在受保护分支上的直接修改

> 📖 详见 `monoco-issue` skill 获取完整工作流文档。
