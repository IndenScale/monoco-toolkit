# DevEx

## 定义
Developer Experience (Internal) - 致力于优化 **Monoco Toolkit 自身开发与维护** 的体验。即 "Engineering Productivity" 或 "Infrastructure"。
它服务于 Monoco 的**贡献者 (Contributors)**，而非 Monoco 的最终用户。

## 职责
- **CI/CD Pipeline**: GitHub Actions, Release Automations, Semantic Release.
- **Local Dev Environment**: `uv` 配置, 依赖管理, 本地构建脚本.
- **Code Quality Infrastructure**: Pre-commit hooks, Linter 配置 (Ruff/MyPy), Formatter 配置.
- **Testing Infrastructure**: Pytest 配置, Fixtures 管理, Coverage 报告生成, Mock 策略.
- **Repository Management**: `.gitignore`, `.editorconfig`, Repo 结构维护.

## 边界
- **负责**: Monoco 项目作为一个软件工程项目的"工地环境"健康度。
- **不负责**:
  - Monoco CLI/Plugin 交付给用户的交互体验 (-> CollaborationBus)
  - Issue Linter 的**业务逻辑** (-> IssueSystem/Governance)
  - Agent 的能力实现 (-> AgentEmpowerment)

## 原则
- **Automate Everything**: 能自动化的绝不手动 (Lint, Test, Release).
- **Zero Configuration for Contributors**: `git clone` -> `uv sync` 即可开始工作.
- **Hermetic Build**: 构建与测试过程应尽可能独立于环境.
