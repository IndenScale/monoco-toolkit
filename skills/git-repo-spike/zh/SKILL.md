---
name: git-repo-spike
description: 引入外部 Git 仓库作为参考资料 (Reference)，用于 Spike、调研或代码借鉴。
---

# Git Repo Spike (Reference Management)

此技能用于规范化地引入外部代码仓库。Monoco 鼓励 "站在巨人的肩膀上"，但在引入外部代码时必须严格隔离，避免污染核心代码库。

## 核心原则 (Core Principles)

1. **只读引用 (Read-Only Reference)**: `.reference/` 目录下的代码仅供阅读和参考。**严禁**直接修改其中的代码，也**严禁**将其作为模块直接 import 到项目中。
2. **物理隔离 (Physical Isolation)**: 所有引入的仓库必须存放在项目根目录的 `.reference/` 目录下。
3. **版本控制 (VCS Hygiene)**: `.reference/` 目录必须被添加到 `.gitignore` 中。我们不提交别人的代码，我们只保留 "引用指针" (即通过脚本或文档记录我们 clone 了什么)。

## 工作流 (Workflow)

### 1. 引入 (Add) (Planned)

当你需要研究某个开源项目 (例如 `requests` 或 `fastapi`) 时：

1. **检查**: 确认 `.reference/` 是否在 `.gitignore` 中。
2. **克隆**: 使用 `git clone` 将仓库下载到 `.reference/<repo_name>`。
   - _未来支持_: 使用 `monoco spike add <url>` 自动完成此步骤。
3. **记录**: (可选) 在相关的 Issue 或设计文档中记录参考了该仓库。

### 2. 更新 (Update) (Planned)

为了保持引用的时效性：

1. **拉取**: 进入对应目录执行 `git pull`。
   - _未来支持_: 使用 `monoco spike update` 一键更新所有参考仓库。

### 3. 查看 (View)

- `monoco spike list`: 列出当前活跃的技术调研 (Spike) 和参考资料。
  - 支持 `--json` 输出。

### 4. 使用 (Usage)

Agent 在回答问题或编写代码时，可以读取 `.reference/` 下的文件作为 Context，但生成的代码必须是 "原创" 或 "经过消化后的重写"，遵守 License 协议。

## 常见场景

- **API 调研**: "这个库是怎么实现 OAuth 的？" -> Clone -> Read -> Mimic for Monoco.
- **协议分析**: "LSP 协议的具体消息格式是什么？" -> Clone `vscode-languageserver-node` -> Search definitions.
