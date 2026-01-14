# Monoco VS Code Extension

Monoco VS Code Cockpit Integration - 在 VS Code 中直接管理和查看 Monoco 项目的 Issue Board。

## 功能特性

- 📋 **Issue Board 视图**: 在侧边栏中查看项目的所有 Epic、Feature、Chore 和 Bug
- 🔄 **实时同步**: 与 Monoco Daemon 实时同步 Issue 状态
- 🎯 **快速导航**: 点击 Issue 直接打开对应的文件
- 🏷️ **状态管理**: 可视化展示 Issue 的状态（Todo、Doing、Review、Done）
- 🌐 **Web 集成**: 一键在浏览器中打开完整的 Kanban 界面

## 使用方法

1. 安装扩展后，在活动栏中点击 Monoco 图标
2. 在设置中配置 Monoco Daemon 的 API 地址（默认：`http://localhost:8642/api/v1`）
3. 选择项目后即可查看和管理 Issues

## 配置项

- `monoco.apiBaseUrl`: Monoco Daemon API 基础地址
- `monoco.webUrl`: Monoco Web UI 地址

## 要求

- VS Code 1.90.0 或更高版本
- Monoco Daemon 运行中

## 许可证

MIT License

## 更多信息

- [Monoco 项目主页](https://github.com/IndenScale/Monoco)
- [问题反馈](https://github.com/IndenScale/Monoco/issues)
