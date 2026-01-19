# 命令系统 (Commands)

## 核心命令 (Core Commands)

扩展注册了以下核心命令，用于快速访问各项功能:

- **视图类 (Views)**
  - `monoco.openSettings`: 打开扩展的配置页面。

- **操作类 (Actions)**
  - `monoco.createIssue`: 打开新建 Issue 的交互界面。
  - `monoco.refreshEntry`: 强制刷新看板数据。

- **辅助类 (Utilities)**
  - `monoco.checkDependencies`: 检查 Monoco 环境依赖状态。

## 生命周期动作 (Lifecycle Actions)

VS Code 扩展通过 **CodeLens** 或 **Document Link** 在编辑器内直接提供基于上下文的动作。

### 1. 通用动作 (Universal)

- **`$(trash) Cancel` (取消)**: 终止任务，归档为 `Closed (Cancelled)`。

### 2. 阶段性动作 (Contextual)

| 当前阶段   | 动作                    | 语义         | 背后执行                                       |
| :--------- | :---------------------- | :----------- | :--------------------------------------------- |
| **DRAFT**  | `$(play) Start`         | **开始执行** | 转状态为 `DOING`                               |
| **DOING**  | `$(check) Submit`       | **提交验收** | 转状态为 `REVIEW`                              |
| **REVIEW** | `$(pass-filled) Accept` | **验收通过** | 转状态为 `DONE`，归档为 `Closed (Implemented)` |
| **REVIEW** | `$(error) Reject`       | **驳回**     | 状态退回 `DOING`                               |
