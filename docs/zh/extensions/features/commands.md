# 命令系统 (Commands)

## 核心命令 (Core Commands)

扩展注册了以下核心命令，用于快速访问各项功能:

- **视图类 (Views)**
  - `monoco.openKanban`: 打开任务看板 Webview。
  - `monoco.openSettings`: 打开扩展的配置页面。
  - `monoco.openWebUI`: 在浏览器中打开 Monoco Web 界面。

- **操作类 (Actions)**
  - `monoco.createIssue`: 打开新建 Issue 的交互界面。
  - `monoco.runAction`: 启动 SOP 动作选择与执行流程 (通用入口)。
  - `monoco.refreshEntry`: 强制刷新看板数据和动作列表。

- **辅助类 (Utilities)**
  - `monoco.checkDependencies`: 检查 Monoco 环境依赖状态。

## 生命周期动作 (Lifecycle Actions)

VS Code 扩展通过 **CodeLens** 或 **Document Link** 在编辑器内直接提供基于上下文的动作。这套体系遵循 "Investigate - Develop - Verify" 的工程三部曲:

### 1. 通用动作 (Universal)

- **`$(telescope) Investigate` (调研)**: 任何阶段可用。调用 `agent:investigate` 扫描全局，完善依赖与背景。
- **`$(trash) Cancel` (取消)**: 终止任务，归档为 `Closed (Cancelled)`。

### 2. 阶段性动作 (Contextual)

| 当前阶段   | 动作                    | 语义         | 背后执行                                       |
| :--------- | :---------------------- | :----------- | :--------------------------------------------- |
| **DRAFT**  | `$(play) Start`         | **开始执行** | 转状态为 `DOING` (可选调用 Agent 进行细化)     |
| **DOING**  | `$(tools) Develop`      | **开发**     | 调用 `agent:develop` 编写代码与测试            |
| **DOING**  | `$(check) Submit`       | **提交验收** | 转状态为 `REVIEW` (可选调用 Agent 自测)        |
| **REVIEW** | `$(pass-filled) Accept` | **验收通过** | 转状态为 `DONE`，归档为 `Closed (Implemented)` |
| **REVIEW** | `$(error) Reject`       | **驳回**     | 状态退回 `DOING`                               |
