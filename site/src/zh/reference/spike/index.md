# Monoco Spike 系统

**Monoco Spike 系统** 是一个用于管理临时、研究导向型代码（Git Repo Spikes）的工具。它允许开发者（以及 AI Agent）轻松导入外部开源项目作为参考，同时保持主代码库的整洁。

## 📚 内容

- **[使用手册](./manual.md)**: 详细的命令参考和最佳实践。

## 💡 核心特性

- **物理隔离**: 参考代码存储在项目根目录的 `.reference/` 中，默认被 Git 忽略。
- **配置驱动**: 仓库列表记录在 `.monoco/project.yaml` 中，而不是提交到 Git 历史。
- **Agent 友好**: Agent 可以利用 Spike 系统在“重新发明轮子”之前先进行相关调研。
