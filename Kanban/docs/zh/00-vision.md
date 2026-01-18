# 产品愿景 (Product Vision)

## 1. 背景与痛点

Monoco 已经在底层实现了强大的 **"Consensus as Code"** 基础设施（Typedown, Chassis, Toolkit）。然而，目前的用户交互主要依赖 CLI (`monoco issue`) 和纯文本编辑。这带来了以下问题:

- **门槛过高**: 对于非技术人员（PM, Designer），通过 CLI 管理任务是不现实的。
- **缺乏全景图**: 纯文本难以直观展示看板（Kanban）、甘特图（Gantt）或冲刺进度（Burn-down）。
- **反馈延迟**: 修改 Markdown -> 提交 Git -> 等待 CI 反馈的链路太长，缺乏现代应用的即时响应感。

## 2. 核心定位

Kanban 不仅仅是一个 UI，它是 **连接人类直觉与代码真理的桥梁**。

- **对于人类**: 它是一个类似于 [Linear](https://linear.app/) 或 [Jira](https://www.atlassian.com/software/jira) 的现代化项目管理工具。
- **对于机器**: 它是一个 **Git-based Headless CMS**。所有的拖拽、点击操作，最终都转化为标准的文件系统变更和 Git Commit。

## 3. 关键特性

### 3.1 极速 (Speed)

- **Optimistic UI**: 所有的操作（如拖动卡片）在 UI 上立即生效，后台异步处理文件读写和 Git 同步。
- **本地优先**: 数据读取自本地文件系统，无网络延迟。

### 3.2 共识可视化 (Consensus Visualization)

- **结构化解析**: 自动解析 Typedown (`.td`, `.md`) 中的元数据，展示为结构化字段而非纯文本。
- **双向链接**: 利用 Typedown 的引用机制，可视化任务之间的依赖关系图谱。

### 3.3 混合智能 (Hybrid Intelligence)

- **Agent 协作**: 在评论区与 AI Agent 对话。AI 的回复不仅仅是文字，而是直接提交代码或修改任务状态（体现为 Git Commit）。

## 4. 目标用户

1. **极客开发者**: 享受 CLI 的掌控感，但也需要看板视图来通过总览项目。
2. **技术产品经理 (TPM)**: 需要深度参与代码库管理，但希望通过图形化界面降低认知负担。
3. **敏捷团队**: 使用 Scrum/Kanban 方法论，需要一个基于 Git 单一事实来源的协作平台。
