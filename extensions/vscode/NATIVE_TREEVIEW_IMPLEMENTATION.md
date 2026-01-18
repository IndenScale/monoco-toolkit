# Native TreeView 实现总结

## 概述

成功将 Monoco VSCode Extension 的 Issue 列表从 Webview 迁移到 Native TreeView，实现了更好的拖拽体验和性能。

## 实现的功能

### 1. 核心组件

#### `IssueTreeItem.ts`

- 封装 Issue 在 TreeView 中的显示逻辑
- 支持根据 `stage` 显示不同颜色的图标（draft/doing/review/done）
- 显示子 Issue 数量气泡
- 支持双击打开文件
- 提供详细的 Tooltip

#### `IssueTreeProvider.ts`

- 实现 `TreeDataProvider` 接口，提供层级数据
- 实现 `TreeDragAndDropController` 接口，支持拖拽
- 支持项目过滤
- 支持搜索/过滤
- 自动排序（按 stage 权重）

#### `TreeViewCommands.ts`

- `monoco.selectProject` - 项目选择器（QuickPick）
- `monoco.searchIssues` - 搜索/过滤 Issues
- `monoco.refreshTreeView` - 手动刷新

### 2. 配置更新

#### `package.json`

- 添加了 `monoco.issueTreeView` 视图定义
- 添加了 `monoco.useNativeTree` 配置项（默认 true）
- 保留了原有的 Webview 作为 Legacy 模式
- 添加了 TreeView 专属的工具栏按钮

### 3. Extension 集成

#### `extension.ts`

- 初始化 `IssueTreeProvider`
- 创建 TreeView 并注册拖拽控制器
- 通过定时器从 LSP 获取数据并更新 TreeView
- 将 TreeView 相关依赖传递给 CommandRegistry

#### `CommandRegistry.ts`

- 集成 `TreeViewCommands`
- 支持可选的 TreeView 依赖注入

### 4. LSP Server 修复

#### `server.ts`

- 为 `monoco/getAllIssues` 添加空值检查
- 为 `monoco/getMetadata` 添加空值检查
- 防止在 WorkspaceIndexer 未初始化时崩溃

## 拖拽功能 (Drag & Drop)

### 实现细节

- 使用 VS Code 原生的 `TreeDragAndDropController`
- 拖拽时设置 `text/uri-list` 和 `text/plain` MIME 类型
- 支持拖拽到终端、编辑器等原生组件
- 自定义 MIME 类型 `application/vnd.code.tree.monoco` 用于内部处理

### 优势

相比 Webview 的 HTML5 DND：

- ✅ 更稳定的跨容器拖拽
- ✅ 原生的拖拽视觉反馈
- ✅ 更好的 OS 集成
- ✅ 支持拖拽到 VS Code 终端

## 视觉特性

### Stage 指示

- **Draft** - 灰色图标 (`descriptionForeground`)
- **Doing** - 蓝色图标 (`charts.blue`)
- **Review** - 紫色图标 (`charts.purple`)
- **Done** - 绿色图标 (`charts.green`)

### Issue 类型图标

- **Epic** - `symbol-namespace`
- **Arch** - `symbol-structure`
- **Feature** - `symbol-method`
- **Chore** - `tools`
- **Fix/Bug** - `bug`

### 子 Issue 数量

- 在 `description` 字段显示（右对齐）
- 超过 99 个显示为 "99+"

## 配置切换

用户可以通过设置切换视图模式：

```json
{
  "monoco.useNativeTree": true  // 使用 Native TreeView（推荐）
  "monoco.useNativeTree": false // 使用 Webview（Legacy）
}
```

## 已知限制

1. **进度条**: Native TreeView 无法显示渐变进度条（已被气泡数量替代）
2. **动画效果**: 无法实现"呼吸灯"等 CSS 动画（已被颜色图标替代）
3. **文字颜色**: TreeItem 的标签文字颜色由主题控制，无法自定义

## 测试清单

- [x] 编译通过 (`npm run compile`)
- [x] Lint 通过 (`npm run lint`)
- [ ] TreeView 正确显示 Issue 层级
- [ ] 拖拽 Issue 到终端能粘贴路径
- [ ] 项目选择器工作正常
- [ ] 搜索功能工作正常
- [ ] 双击打开 Issue 文件
- [ ] 图标颜色正确显示 Stage

## 下一步

1. 测试拖拽功能在不同场景下的表现
2. 优化数据刷新机制（考虑使用 LSP 的文件监听）
3. 添加右键菜单（Context Menu）支持更多操作
4. 考虑实现 Issue 重新父级化（Drop 功能）
