# 任务管理 (Issue Management)

该模块负责项目任务的可视化管理与编辑支持。

## 2.1 Issue 资源管理器 (Issue Explorer)

- **视图交互**
  - **展示形式**: 基于 VS Code TreeView 的原生树状视图。
  - **分组逻辑**: 按 Issue 类型（Epic, Feature, etc.）或状态分组展示。
  - **快捷操作**: 支持在树节点上直接创建子 Issue 或进行状态流转。
  - **上下文切换**: 由 Workspace 自动识别项目边界。

- **数据同步**
  - **读取**: 通过 LSP 请求获取最新任务列表。
  - **写入**: 所有的增删改查直接通过 File System API 操作 Markdown 文件，由 File Watcher 保持同步。

- **创建任务**
  - **入口**: 视图标题栏的 "Create Issue" 按钮。
  - **生成逻辑**: 自动生成包含 Frontmatter 元数据的 Markdown 文件。
  - **文件命名**: 遵循 `ID-Title.md` 的规范格式。

## 2.2 编辑器增强 (Editor Support)

- **语法检查 (Diagnostics)**
  - **触发时机**: 文件打开或保存时。
  - **执行逻辑**: 调用 `monoco issue lint` 命令。
  - **验证内容**: Frontmatter 格式、必填字段、字段值合法性。
  - **反馈形式**: 在编辑器中显示波浪线错误提示。

- **智能补全 (Completion)**
  - **触发场景**: 在 Markdown 文件中输入文本时。
  - **补全内容**: 已存在的 Issue ID。
  - **提示信息**: 显示 Issue 的标题、类型和阶段。

- **定义跳转 (Definition)**
  - **操作**: 按住 Ctrl/Cmd 点击 Issue ID。
  - **行为**: 跳转到对应的 Issue 定义文件。

- **辅助功能**
  - **Hover**: 悬停在 Issue ID 上显示任务详情。
  - **CodeLens**: 在 Issue 标题上方提供 "Run Action" 等快捷操作入口。
