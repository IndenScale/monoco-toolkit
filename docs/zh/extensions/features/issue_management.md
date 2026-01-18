# 任务管理 (Issue Management)

该模块负责项目任务的可视化管理与编辑支持。

## 2.1 看板视图 (`monoco-kanban`)

- **视图交互**
  - **展示形式**: 基于 Webview 的看板界面。
  - **分组逻辑**: 按 Issue 状态（Open, In Progress, Done 等）分组展示。
  - **状态更新**: 支持拖拽卡片或使用右键菜单更新 Issue 状态。
  - **上下文切换**: 读取 `.monoco` 元数据，支持在不同项目（Project）间切换。

- **数据同步**
  - **读取**: 通过 LSP 请求 `monoco/getAllIssues` 获取最新任务列表。
  - **写入**: 通过 LSP 请求 `monoco/updateIssue` 将变更回写到文件系统。
  - **实时性**: 监听文件变更事件，自动刷新看板数据。

- **创建任务**
  - **入口**: 看板界面的 "New Issue" 按钮。
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
